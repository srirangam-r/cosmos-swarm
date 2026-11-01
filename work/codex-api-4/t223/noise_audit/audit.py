#!/usr/bin/env python3
"""Outcome-blind CPU replay of pinned noise.py and server.sync. No model/GPU.

The route body is compiled from the unmodified source snapshot. Imports,
model loading, network serving, scheduler execution, and the pipeline are
replaced with explicit doubles. This tests argument/sidecar plumbing, NOT
the real Diffusers random draws or a deployed server.
"""
from __future__ import annotations

import argparse
import ast
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
import traceback
from types import SimpleNamespace

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
SOURCE_COMMIT = "e5c7b3b8f9996417a59aeb93099d9265a71428fb"
SHAPE = (1, 2, 3, 4, 5)
SEED = 103
CHECKS = []


def check(name, condition):
    if not bool(condition):
        raise AssertionError(name)
    CHECKS.append(name)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def tensor_record(x):
    """Hash exact contiguous CPU bytes; include dtype/shape separately.

    uint8 view preserves bfloat16 bits and avoids a lossy float32 conversion.
    This records observed values, not their random-draw location/meaning.
    """
    x = x.detach().cpu().contiguous()
    return {"shape": list(x.shape), "dtype": str(x.dtype),
            "packing": "C-contiguous native bytes", "byteorder": sys.byteorder,
            "sha256": sha(bytes(x.view(torch.uint8).reshape(-1).tolist()))}


def load_noise():
    name = "t223_pinned_noise"
    spec = importlib.util.spec_from_file_location(name, HERE / "source/noise.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


noise = load_noise()


def randn_tensor(shape, generator=None, device=None, dtype=None, **kw):
    """CPU test double for pipeline module's random helper; NOT Diffusers."""
    return torch.randn(shape, generator=generator, device="cpu", dtype=dtype or torch.float32)


class FakePipe:
    """Uses real CPU RNG through a fake pipeline random helper."""
    def __init__(self, preconsume=False, fail=False):
        self.preconsume, self.fail = preconsume, fail
        self.calls = []

    def __call__(self, **call):
        g = call["generator"]
        state_before = tensor_record(g.get_state())
        if self.fail:
            raise RuntimeError("manufactured pipeline exception")
        if self.preconsume:
            randn_tensor((1, 3, 4), generator=g)  # sound-like draw before vision
        a = randn_tensor(SHAPE, generator=g)
        b = randn_tensor(SHAPE, generator=g)
        self.calls.append({"generator_device": str(g.device), "seed": g.initial_seed(),
                           "state_before": state_before, "first": tensor_record(a),
                           "second": tensor_record(b), "a": a, "b": b})
        # Fixed fake output: no scientific inference from output pixels.
        return SimpleNamespace(video=np.zeros((3, 8, 8, 3), dtype=np.uint8))


class HTTPException(Exception):
    def __init__(self, status_code, detail):
        super().__init__(detail)
        self.status_code, self.detail = status_code, detail


class FakeScheduler:
    @classmethod
    def from_config(cls, config, **kw):
        return SimpleNamespace(config=config, requested=kw)


def route_namespace(out, pipe):
    """Compile exact sync body; strip only decorators/annotations/defaults.

    The caller supplies EVERY route argument, so altered defaults cannot affect
    any request. Actual source control flow, locking and sidecar construction
    remain intact. The real CUDA/model imports never execute.
    """
    tree = ast.parse((HERE / "source/server.py").read_text())
    fn = copy.deepcopy(next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "sync"))
    fn.decorator_list = []
    fn.returns = None
    for arg in fn.args.args + fn.args.kwonlyargs:
        arg.annotation = None
    fn.args.defaults = []
    fn.args.kw_defaults = []
    mod = ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[]))
    ns = dict(json=json, io=io, Image=None, Path=Path, np=np, torch=torch,
              time=time, traceback=traceback, contextlib=contextlib,
              HTTPException=HTTPException, pipe=pipe, OUT=out, OFFLOAD=False,
              VAE_SWAP=False, os=SimpleNamespace(environ={}), ARTIFACTS=None,
              UniPCMultistepScheduler=FakeScheduler, BASE_SCHED={"test": True},
              LOCK=threading.Lock(), STATE=dict(waiting=0, busy=False, served=0),
              noise=noise,
              neg_meta=SimpleNamespace(MODES=("inverse", "same"),
                  resolve_negative=lambda value, preset: value,
                  negative_metadata=lambda pipe, mode: contextlib.nullcontext()),
              parse_internals=lambda *args: None,
              encode_mp4=lambda frames, fps, crf: b"manufactured-fake-mp4",
              Response=lambda content, media_type, headers: SimpleNamespace(content=content, headers=headers))
    exec(compile(mod, "pinned-server-sync-only", "exec"), ns)
    return ns, sha(ast.dump(mod, include_attributes=False).encode())


def request(ns, extra, seed=SEED):
    with contextlib.redirect_stdout(io.StringIO()):
        return ns["sync"](prompt="manufactured prompt", negative_prompt=None,
            size="8x8", num_frames=3, fps=24., num_inference_steps=2,
            guidance_scale=6., flow_shift=10., seed=seed,
            extra_params=json.dumps(extra), input_reference=None, internals_files=None)


def sidecar(out, response):
    return json.loads((out / (response.headers["X-Clip-Id"] + ".json")).read_text())


def run():
    torch.set_num_threads(1)
    check("torch wheel is CPU only", torch.version.cuda is None)
    spec = noise.parse({"noise": {"device": "cpu"}})
    g = noise.generator(spec, SEED)
    check("requested CPU generator is CPU", str(g.device) == "cpu")
    check("generator carries request seed", g.initial_seed() == SEED)
    direct = torch.randn(SHAPE, generator=torch.Generator(device="cpu").manual_seed(SEED))
    actual = torch.randn(SHAPE, generator=g)
    check("plain generator draw equals independent torch reference", torch.equal(actual, direct))
    repeat = torch.randn(SHAPE, generator=noise.generator(spec, SEED))
    check("fresh same-seed same-shape CPU draw repeats exactly", torch.equal(actual, repeat))
    other = torch.randn(SHAPE, generator=noise.generator(spec, SEED + 1))
    check("different seed changes manufactured draw", not torch.equal(actual, other))
    advanced = torch.randn(SHAPE, generator=g)
    check("reusing generator advances draw", not torch.equal(actual, advanced))
    before = tensor_record(noise.generator(spec, SEED).get_state())
    after = tensor_record(g.get_state())
    check("state hash sees stream advance", before["sha256"] != after["sha256"])
    bf = torch.randn(SHAPE, generator=noise.generator(spec, SEED), dtype=torch.bfloat16)
    check("bf16 bytes are recorded without numpy conversion", tensor_record(bf)["dtype"] == "torch.bfloat16")
    check("dtype is an explicit equality condition", tensor_record(bf) != tensor_record(actual))
    reshaped = actual.reshape((1, 2, 3, 5, 4))
    check("same raw bytes can have different shapes", tensor_record(reshaped)["sha256"] == tensor_record(actual)["sha256"])
    check("full record catches shape difference", tensor_record(reshaped) != tensor_record(actual))
    original = randn_tensor
    with noise.installed(FakePipe(), spec):
        check("plain CPU installed context leaves helper untouched", randn_tensor is original)
    check("mixed flag remains false for plain CPU", spec.used is False)

    with tempfile.TemporaryDirectory(prefix="t223-own-cpu-audit-") as tmp:
        out = Path(tmp)
        pipe = FakePipe()
        ns, body_hash = route_namespace(out, pipe)
        r = request(ns, {"noise": {"device": "cpu"}})
        side = sidecar(out, r)
        call = pipe.calls[-1]
        check("exact route passes CPU generator to fake pipeline", call["generator_device"] == "cpu")
        check("exact route passes requested seed", call["seed"] == SEED)
        check("exact route first draw equals direct reference", torch.equal(call["a"], direct))
        check("native sidecar records request", side["noise"]["spec"] == {"device": "cpu"})
        check("native sidecar mixed false on successful plain CPU call", side["noise"]["mixed"] is False)
        check("native noise sidecar has only spec and mixed", set(side["noise"]) == {"spec", "mixed"})
        check("native noise sidecar has no sampled tensor hash", "sha256" not in side["noise"])
        check("native sidecar records torch version", side["torch"] == torch.__version__)
        check("route clears busy after success", ns["STATE"]["busy"] is False)
        check("route balances waiter count", ns["STATE"]["waiting"] == 0)
        request(ns, {"noise": {"device": "cpu"}})
        check("repeated exact route recreates generator state", pipe.calls[-1]["state_before"] == call["state_before"])
        check("repeated exact route repeats fake draw", pipe.calls[-1]["first"] == call["first"])

        pre = FakePipe(preconsume=True)
        npres, _ = route_namespace(out, pre)
        request(npres, {"noise": {"device": "cpu"}})
        check("same seed differs after earlier draw", pre.calls[-1]["first"] != call["first"])
        check("same starting state does not fix arbitrary later draw", pre.calls[-1]["state_before"] == call["state_before"])

        mix = {"noise": {"device": "cpu", "mix": {"seed": 107, "band": "all"}}}
        mr = request(ns, mix)
        mixed_side = sidecar(out, mr)
        mb = torch.randn(SHAPE, generator=torch.Generator().manual_seed(107))
        check("all mix replaces first 5D draw with B", torch.equal(pipe.calls[-1]["a"], mb))
        check("all mix leaves subsequent A draw unchanged", torch.equal(pipe.calls[-1]["b"], advanced))
        check("native mixed flag true when mix executed", mixed_side["noise"]["mixed"] is True)
        check("mixed helper restored after route success", randn_tensor is original)

        failure = FakePipe(fail=True)
        nfail, _ = route_namespace(out, failure)
        caught = None
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                request(nfail, mix)
        except HTTPException as err:
            caught = err
        check("pipeline failure becomes HTTP500", caught is not None and caught.status_code == 500)
        check("route clears busy after failure", nfail["STATE"]["busy"] is False)
        check("mixed helper restored after failure", randn_tensor is original)
        check("no failed clip counted as served", nfail["STATE"]["served"] == 0)

        invalid = None
        try:
            request(ns, {"noise": {"device": "tpu"}})
        except HTTPException as err:
            invalid = err
        check("invalid device rejected before generation", invalid is not None and invalid.status_code == 400)

    return {"status": "CPU fake-pipeline software checks only; live execution unverified",
            "source_commit": SOURCE_COMMIT,
            "source_sha256": {p.name: sha(p.read_bytes()) for p in sorted((HERE / "source").glob("*.py"))},
            "executed_sync_ast_sha256": body_hash,
            "python": sys.version.split()[0], "torch": torch.__version__, "numpy": np.__version__,
            "hardware_scope": "one CPU runtime, no CUDA, no model or deployed endpoint",
            "synthetic_draw": {"seed": SEED, "tensor": tensor_record(actual),
                               "initial_generator_state": before,
                               "advanced_generator_state": after},
            "checks_passed": len(CHECKS), "checks": CHECKS,
            "not_established": ["CPU draws in an actual Cosmos3OmniPipeline",
                "same sampled noise across deployed GPU types",
                "checkpoint, pipeline, scheduler or output equivalence",
                "any physical parameter or improvement"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = run()
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(payload)
    else:
        print(payload, end="")

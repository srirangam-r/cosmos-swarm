#!/usr/bin/env python3
"""Independent CPU acceptance; no model startup, HTTP, GPU, or valid video output."""
import ast
import contextlib
import hashlib
import io
import json
import socket
import tempfile
import threading
import traceback
from pathlib import Path
from types import SimpleNamespace as NS

import numpy as np

HERE = Path(__file__).resolve().parent
CHECKS = []
CASES = []


def check(name, condition):
    CHECKS.append({"name": name, "pass": bool(condition)})
    if not condition:
        raise AssertionError(name)


def no_network(*args, **kwargs):
    raise AssertionError("Network is forbidden in this CPU harness")


socket.socket = no_network
socket.create_connection = no_network


class HttpError(Exception):
    def __init__(self, status, detail):
        self.status_code, self.detail = status, detail
        super().__init__(detail)


class Harness:
    def __init__(self, source, out, storage="list", pixels="float"):
        self.out = out
        self.lock = threading.Lock()
        self.trace = []
        self.fail = False
        self.block = False
        self.encoded = threading.Event()
        self.resume = threading.Event()
        self.error = None
        self.response = None
        self.scheduler = None
        self.storage = storage
        self.pixels = pixels
        self.contexts = 0

        @contextlib.contextmanager
        def entered(*args):
            self.contexts += 1
            self.trace.append("context-enter")
            try:
                yield
            finally:
                self.contexts -= 1
                self.trace.append("context-exit")

        def schedule(*args, **kwargs):
            self.trace.append("new-scheduler")
            return NS(sigmas=self.wrap([11.0, 22.0]), start=None)

        def latent_schedule(cls, cfg, shift, start, *args):
            obj = schedule()
            obj.start = start
            return obj

        def parse_latent(extra, uploads, steps):
            raw = extra.get("latent")
            return None if raw is None else NS(raw=raw, ref=None, x0_inject=None,
                                              start_step=raw["start_step"], returns=[], summary={})

        def pipeline(**kwargs):
            check("pipeline holds LOCK", self.lock.locked())
            self.trace.append({"pipeline": kwargs})
            if self.fail:
                raise RuntimeError("synthetic pipeline failure")
            values = [1.0, 0.75, 0.25, 0.0] if self.pipe.scheduler.start is None else [0.9, 0.5, 0.0]
            self.pipe.scheduler.sigmas = self.wrap(values)
            self.scheduler = self.pipe.scheduler
            self.expected = [round(float(v), 5) for v in values]
            arr = np.linspace(-0.1, 1.1, 144).reshape(2, 4, 6, 3)
            if self.pixels == "uint8":
                arr = np.arange(144, dtype=np.uint8).reshape(2, 4, 6, 3)
            return NS(video=arr[None])

        class Pipe:
            def __call__(inner, **kwargs):
                return pipeline(**kwargs)

        self.pipe = Pipe()

        def encode(frames, fps, crf):
            check("encoder outside LOCK", not self.lock.locked())
            check("hooks removed before encoding", self.contexts == 0)
            self.trace.append({"encode": {"fps": fps, "crf": crf,
                               "pixels": hashlib.sha256(np.stack(frames).tobytes()).hexdigest()}})
            if self.block:
                self.encoded.set()
                if not self.resume.wait(5):
                    raise AssertionError("Timed out waiting for controlled mutation")
            # Explicitly invalid video bytes, written only inside a TemporaryDirectory.
            return b"SYNTHETIC-NOT-VIDEO:" + np.stack(frames).tobytes()

        self.env = dict(
            json=json, io=io, Path=Path, np=np, contextlib=contextlib,
            traceback=traceback, HTTPException=HttpError, pipe=self.pipe,
            LOCK=self.lock, OUT=out, OFFLOAD=False, VAE_SWAP=False,
            STATE=dict(waiting=0, busy=False, served=0), SERVER_REV={"fixture": "same"},
            BASE_SCHED={"fixture": True}, UniPCMultistepScheduler=NS(from_config=schedule),
            neg_meta=NS(MODES=["inverse", "same"], resolve_negative=lambda value, preset: value,
                        negative_metadata=entered),
            noise=NS(parse=lambda extra: None, generator=lambda spec, seed: {"cpu_seed": seed}, installed=entered),
            latent=NS(parse=parse_latent, sigma_list=lambda *args: [1, .9, .5, 0],
                      build_start=lambda *args: ("synthetic-start", {}),
                      start_at_scheduler=latent_schedule, vision_noise=entered),
            parse_internals=lambda *args: None,
            time=NS(time=lambda: 1000.0, gmtime=lambda: None, strftime=lambda *args: "FIXED"),
            os=NS(environ={}), torch=NS(__version__="CPU-FAKE"), encode_mp4=encode,
            Form=lambda default=None: default, File=lambda default=None: default,
            Response=lambda body, **kwargs: NS(body=body, **kwargs),
        )
        tree = ast.parse(source)
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "sync")
        fn.decorator_list = []
        module = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), fn], type_ignores=[])
        ast.fix_missing_locations(module)
        exec(compile(module, "pinned-server-sync", "exec"), self.env)

    def wrap(self, values):
        return list(values) if self.storage == "list" else np.array(values, dtype=np.float64)

    def run(self, latent=False):
        extra = {"client": "acceptance-A", "crf": 7, "noise": {"device": "cpu"}}
        if latent:
            extra["latent"] = {"start_step": 1}
        return self.env["sync"](prompt="synthetic CPU test", negative_prompt="synthetic-negative",
                                size="6x4", num_frames=2, fps=24.0, num_inference_steps=3,
                                guidance_scale=6.0, flow_shift=10.0, seed=123,
                                extra_params=json.dumps(extra), input_reference=None,
                                internals_files=None)

    def side(self):
        paths = list(self.out.glob("*.json"))
        check("exactly one sidecar", len(paths) == 1)
        return json.loads(paths[0].read_text())

    def threaded(self, latent):
        try:
            self.response = self.run(latent)
        except BaseException as exc:
            self.error = exc


def main():
    sources = {key: (HERE / "source" / f"server_{key}.py").read_text() for key in ("before", "after")}
    serial = []
    races = []
    failures = []
    with tempfile.TemporaryDirectory(prefix="t308-cpu-") as tmp:
        root = Path(tmp)
        for lat in (False, True):
            for storage in ("list", "numpy"):
                for pixels in ("float", "uint8"):
                    outputs = {}
                    for version, source in sources.items():
                        out = root / f"serial-{lat}-{storage}-{pixels}-{version}"
                        out.mkdir()
                        h = Harness(source, out, storage, pixels)
                        response = h.run(lat)
                        side = h.side()
                        check("serial suffix exact", side["sigmas_used"] == h.expected)
                        check("serial response equals written synthetic bytes", response.body == next(out.glob("*.mp4")).read_bytes())
                        outputs[version] = dict(side=side, body_hash=hashlib.sha256(response.body).hexdigest(),
                                                headers=response.headers, trace=h.trace, state=h.env["STATE"])
                    check("full serial sidecar/response/call/encoder parity", outputs["before"] == outputs["after"])
                    serial.append(dict(latent=lat, storage=storage, pixels=pixels, parity=True,
                                       evidence=outputs["after"]))

                for mutation in ("in-place", "delete-attribute"):
                    result = {}
                    for version, source in sources.items():
                        out = root / f"race-{lat}-{storage}-{mutation}-{version}"
                        out.mkdir()
                        h = Harness(source, out, storage)
                        h.block = True
                        worker = threading.Thread(target=h.threaded, args=(lat,), name="request-A")
                        worker.start()
                        try:
                            check("A reached encode", h.encoded.wait(5))
                            with h.lock:
                                old_object = h.scheduler.sigmas
                                if mutation == "in-place":
                                    if storage == "list":
                                        old_object[:] = [7.123456, 8.654321]
                                    else:
                                        old_object[:] = 9.876543
                                else:
                                    del h.scheduler.sigmas
                            h.resume.set()
                        finally:
                            h.resume.set()
                            worker.join(5)
                        check("request exits without thread leak", not worker.is_alive())
                        check("request has no error", h.error is None)
                        side = h.side()
                        intact = side["sigmas_used"] == h.expected
                        check("patched isolation / baseline negative control", intact == (version == "after"))
                        check("post mutation lock/state cleanup", not h.lock.locked() and not h.env["STATE"]["busy"] and h.env["STATE"]["waiting"] == 0)
                        result[version] = {"recorded": side["sigmas_used"], "expected": h.expected,
                                           "own_schedule_retained": intact,
                                           "response_hash": hashlib.sha256(h.response.body).hexdigest()}
                    check("mutation leaves synthetic response bytes identical", result["before"]["response_hash"] == result["after"]["response_hash"])
                    races.append(dict(latent=lat, storage=storage, mutation=mutation, versions=result))

            for version, source in sources.items():
                out = root / f"failure-{lat}-{version}"
                out.mkdir()
                h = Harness(source, out)
                h.fail = True
                try:
                    h.run(lat)
                except HttpError as exc:
                    check("pipeline error HTTP500 preserved", exc.status_code == 500 and exc.detail == "RuntimeError: synthetic pipeline failure")
                else:
                    raise AssertionError("Expected injected pipeline failure")
                check("failed inference writes no sidecar or bytes", not list(out.iterdir()))
                check("failed inference releases hooks/LOCK/state", h.contexts == 0 and not h.lock.locked() and h.env["STATE"] == dict(waiting=0, busy=False, served=0))
                h.fail = False
                h.run(lat)
                check("next request recovers with own receipt", h.side()["sigmas_used"] == h.expected)
                failures.append(dict(version=version, latent=lat, cleanup_and_recovery=True))

    report = dict(scope="deterministic CPU software acceptance; no model/video/physics evidence",
                  source_commit="16dcfac", source_sha256={k: hashlib.sha256(v.encode()).hexdigest() for k, v in sources.items()},
                  numpy=np.__version__, python=__import__("sys").version,
                  serial_cases=serial, mutation_cases=races, pipeline_failures=failures,
                  assertions=len(CHECKS), passed=sum(c["pass"] for c in CHECKS), checks=CHECKS,
                  limits=["Model/scheduler/latent/codec dependencies injected; sync body otherwise unchanged",
                          "No HTTP/ASGI, torch, CUDA, actual MP4 encoding, deployment, or native sampling tested",
                          "Does not explain or repair historical receipts;303 remains2/4 suffix consistency",
                          "No277 adoption, reader289 PASS, physics improvement, or NVIDIA result"])
    (HERE / "acceptance.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"assertions": len(CHECKS), "pass": report["passed"], "serial_pairs": len(serial),
                      "mutation_pairs": len(races), "failure_recovery_cases": len(failures)}))


if __name__ == "__main__":
    main()

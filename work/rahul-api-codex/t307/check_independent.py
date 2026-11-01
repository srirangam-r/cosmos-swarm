#!/usr/bin/env python3
"""Independent task303 acceptance; no model, network, or planted-case access.

The server test executes its actual sync function with labeled CPU stubs for
pipeline, scheduler, latent preparation and codec. Events impose interleavings;
the produced response bytes are deliberately not a video and are discarded.
"""
import ast
import contextlib
import copy
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal, getcontext
import hashlib
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import platform
import socket
import subprocess
import sys
import tempfile
import threading
import time
import traceback
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import requests

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CHECKS = []
getcontext().prec = 80


def check(condition, label):
    CHECKS.append({"check": label, "pass": bool(condition)})
    if not condition:
        raise AssertionError(label)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def blocked(*args, **kwargs):
    raise AssertionError("Network is forbidden in this CPU test")


def load_runner():
    spec = importlib.util.spec_from_file_location("independent_runner", HERE / "source/runner.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def selector_review(runner, grid):
    # Independent exact binary-float arithmetic oracle; avoids ambiguous rounded
    # decimal midpoints while checking the actual public float contract.
    candidates = [float(x) for x in grid[:-1]]
    exact = [Decimal.from_float(x) for x in candidates]
    targets = [i / 10000 for i in range(10001)]
    for a, b in zip(candidates, candidates[1:]):
        midpoint = (a + b) / 2
        targets.extend([math.nextafter(midpoint, 0), midpoint, math.nextafter(midpoint, 1)])
    targets.extend(candidates)
    mismatches = []
    for target in targets:
        distances = [abs(x - Decimal.from_float(target)) for x in exact]
        expected = distances.index(min(distances))
        actual = runner.sigma_to_step(target)
        if actual != expected:
            mismatches.append({"target": target, "expected": expected, "actual": actual})
    check(not mismatches, "sigma sweep agrees with exact Decimal oracle")

    invalid = [float("nan"), float("inf"), -float("inf"), -0.01, 1.01, True, False, None, "0.9", [], {}]
    rejects = []
    for value in invalid:
        try:
            runner.sigma_to_step(value)
        except (TypeError, ValueError):
            rejects.append(repr(value))
    check(len(rejects) == len(invalid), "nonfinite/out-of-domain/non-numeric sigma rejected")
    matrix = 0
    for steps in range(1, 61):
        for start in range(steps):
            check(runner.resolve_start_step(steps, start) == start, f"explicit start {start}/{steps}")
            matrix += 1
        for start in (-1, steps, 0.5, True, "0"):
            try:
                runner.resolve_start_step(steps, start)
            except (TypeError, ValueError):
                pass
            else:
                raise AssertionError(f"invalid start accepted: {start}/{steps}")
        if steps != 35:
            try:
                runner.sigma_to_step(0.9, steps)
            except (TypeError, ValueError):
                pass
            else:
                raise AssertionError(f"invented grid accepted: {steps}")
    check(runner.resolve_start_step(35) == 14, "35-step default remains14")
    check(runner.resolve_start_step(35, -100, 0.9) == 19, "sigma override remains19")
    return {"sigma_targets": len(targets), "oracle": "Decimal exact distances from actual binary floats", "mismatches": mismatches,
            "invalid_sigma_rejected": rejects, "valid_explicit_start_cases": matrix,
            "invalid_start_cases": 300, "unsupported_sigma_grids_rejected": 59}


def receipt_review(runner):
    records = []
    for path in sorted((HERE / "receipts").glob("*.server.json")):
        raw = json.loads(path.read_text())
        grid = raw["latent"]["sigmas_request"]
        start = raw["latent"]["start_step"]
        used = raw["sigmas_used"]
        rec = {"name": path.stem, "sha256": sha(path), "full_grid_match": grid == runner.NATIVE_SIGMAS_35,
               "start": start, "start_sigma_matches_grid": raw["latent"]["sigma_start"] == grid[start],
               "suffix_match": used == grid[start:], "used_count": len(used), "expected_count": len(grid[start:]),
               "used_first": used[0], "used_last": used[-1], "server_rev": raw["server_rev"]}
        check(rec["full_grid_match"] and rec["start_sigma_matches_grid"], path.name + " grid/start")
        posts, gets = [], []
        response = SimpleNamespace(status_code=200, content=b"SYNTHETIC TRANSPORT - NOT VIDEO",
                                   headers={"X-Clip-Id": "fixture", "X-Seconds": "1.0"},
                                   raise_for_status=lambda: None, json=lambda: copy.deepcopy(raw))
        def post(*args, **kwargs):
            posts.append(kwargs)
            return response
        def get(*args, **kwargs):
            gets.append(args)
            return response
        with tempfile.TemporaryDirectory(prefix="t307-receipt-") as directory:
            folder = Path(directory)
            (folder / "input.png").write_bytes(b"synthetic input fixture")
            (folder / "proxy.mp4").write_bytes(b"synthetic upload fixture - NOT VIDEO")
            with patch.object(runner.requests, "post", post), patch.object(runner.requests, "get", get):
                out = runner.run_remote_nanophys("http://invalid.test:8001", folder / "input.png", folder / "proxy.mp4",
                                               "synthetic replay", folder / "out.mp4", start_step=start)
            check(len(posts) == 1 and len(gets) == 1, path.name + " intercepted transport")
            check(out["sigmas_used"] == used, path.name + " used array retained unchanged")
            check(out["server_latent"] == raw["latent"], path.name + " native latent retained")
            check(json.loads((folder / "out.server.json").read_text()) == raw, path.name + " native JSON values retained")
            extra = json.loads(posts[0]["data"]["extra_params"])
            check(extra["noise"] == {"device": "cpu"} and extra["latent"]["start_step"] == start,
                  path.name + " paired request metadata")
        records.append(rec)
    check(sum(r["suffix_match"] for r in records) == 2, "exactly2/4 recorded suffixes match")
    return records


def cli_review():
    cases = [(["--sigma=nan"], "must be in [0, 1]"),
             (["--sigma=inf"], "must be in [0, 1]"),
             (["--sigma=-inf"], "must be in [0, 1]"),
             (["--steps", "20", "--sigma", "0.9"], "requires the recorded 35-step grid"),
             (["--steps", "1"], "start_step must be an integer"),
             (["--start-step", "35"], "start_step must be an integer"),
             (["--start-step=-1"], "start_step must be an integer"),
             (["--steps", "0"], "steps must be a positive integer")]
    results = []
    with tempfile.TemporaryDirectory(prefix="t307-cli-") as directory:
        folder = Path(directory)
        env = dict(os.environ, PYTHONPATH=str(ROOT / "tools"))
        base = [sys.executable, "-m", "nano_phys", "--image", str(folder / "nonexistent.png"),
                "--prompt", "CPU guard test", "--physics", "pendulum", "--pivot", "1,1", "--bob", "2,2",
                "--proxy-only", "--out", str(folder / "out.mp4")]
        for args, message in cases:
            result = subprocess.run(base + args, env=env, text=True, capture_output=True, timeout=10)
            check(result.returncode == 2 and message in result.stderr, "actual CLI rejects " + repr(args))
            check(not list(folder.iterdir()), "actual CLI guard precedes proxy/output " + repr(args))
            results.append({"args": args, "returncode": result.returncode, "expected_message": message,
                            "stdout": result.stdout, "stderr": result.stderr, "files_created": 0})
    return results


def compile_sync(path, namespace):
    tree = ast.parse(path.read_text())
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "sync")
    fn.decorator_list = []  # Only routing registration is omitted; body is unchanged.
    unit = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), fn], type_ignores=[])
    exec(compile(ast.fix_missing_locations(unit), str(path), "exec"), namespace)
    return namespace["sync"]


def run_interleaving(source, grid, training, mode, a_start=12, b_start=19):
    """mode=serial, next_training, or next_suffix; all pipeline work is stubbed."""
    a_encoding = threading.Event()
    b_replaced = threading.Event()
    a_done = threading.Event()
    lock = threading.Lock()
    events, executed = [], {}
    def event(name):
        events.append({"event": name, "thread": threading.current_thread().name})
    def wait(ev, name):
        if not ev.wait(timeout=5):
            raise RuntimeError("test barrier timed out: " + name)
    def is_b():
        return threading.current_thread().name == "B"

    class Scheduler:
        def __init__(self, start=0):
            self.sigmas = list(training)
            self.start = start
        @classmethod
        def from_config(cls, *args, **kwargs):
            event("fresh scheduler contains training array")
            return cls()

    class Pipeline:
        scheduler = Scheduler()
        def __call__(self, **kwargs):
            name = threading.current_thread().name
            self.scheduler.sigmas = list(grid[self.scheduler.start:])
            executed[name] = list(self.scheduler.sigmas)
            event("stub pipeline consumed its request suffix")
            if is_b() and mode == "next_suffix":
                b_replaced.set()
                wait(a_done, "A metadata captured")
            return SimpleNamespace(video=np.zeros((1, 2, 2, 3), dtype=np.uint8))

    pipe = Pipeline()
    def encode_ref(*args):
        if is_b() and mode == "next_training":
            event("B paused after fresh scheduler assignment")
            b_replaced.set()
            wait(a_done, "A metadata captured")
        return np.zeros((1, 1, 1, 1, 1))
    def start_scheduler(*args):
        return Scheduler(start=args[3])
    def encode(*args):
        if threading.current_thread().name == "A" and mode != "serial":
            check(not lock.locked(), "A codec runs outside shared lock")
            event("A encoding after lock release")
            a_encoding.set()
            wait(b_replaced, "B replaced shared scheduler")
        return b"SYNTHETIC STUB RESPONSE - NOT A VIDEO"

    with tempfile.TemporaryDirectory(prefix="t307-handler-") as directory:
        ns = {"Form": lambda x: x, "File": lambda x: x, "json": json, "io": io, "Path": Path,
              "contextlib": contextlib, "time": time, "traceback": traceback, "np": np,
              "os": SimpleNamespace(environ={}), "pipe": pipe, "LOCK": lock, "print": lambda *args, **kwargs: None,
              "STATE": {"waiting": 0, "busy": False, "served": 0}, "BASE_SCHED": {},
              "UniPCMultistepScheduler": Scheduler, "SERVER_REV": {"server.py": hashlib.md5(source.read_bytes()).hexdigest()[:10]},
              "OUT": Path(directory), "OFFLOAD": False, "VAE_SWAP": False,
              "torch": SimpleNamespace(__version__="CPU TEST STUB - NO TORCH"),
              "neg_meta": SimpleNamespace(MODES=["inverse"], resolve_negative=lambda value, preset: value,
                                           negative_metadata=lambda *args: contextlib.nullcontext()),
              "noise": SimpleNamespace(parse=lambda extra: None, generator=lambda *args: None,
                                        installed=lambda *args: contextlib.nullcontext()),
              "latent": SimpleNamespace(parse=lambda extra, uploads, steps: SimpleNamespace(
                    ref="proxy.mp4", start_step=extra["latent"]["start_step"], raw=extra["latent"], x0_inject=None,
                    returns=[], summary={"start_step": extra["latent"]["start_step"]}),
                    encode_ref=encode_ref, sigma_list=lambda *args: list(grid),
                    build_start=lambda *args: (None, {}), start_at_scheduler=start_scheduler,
                    vision_noise=lambda *args: contextlib.nullcontext()),
              "parse_internals": lambda *args: None, "encode_mp4": encode,
              "Response": lambda content, **kwargs: SimpleNamespace(content=content, **kwargs)}
        sync = compile_sync(source, ns)
        def request(start):
            upload = SimpleNamespace(filename="proxy.mp4", file=io.BytesIO(b"synthetic upload"))
            response = sync(prompt="CPU stub", size="2x2", num_frames=1, seed=start,
                            extra_params=json.dumps({"latent": {"start_step": start}}), internals_files=[upload])
            side = json.loads((Path(directory) / (response.headers["X-Clip-Id"] + ".json")).read_text())
            event("request metadata completed")
            return side
        if mode == "serial":
            previous = threading.current_thread().name
            threading.current_thread().name = "A"
            try:
                a_side = request(a_start)
            finally:
                threading.current_thread().name = previous
            b_side = None
        else:
            with ThreadPoolExecutor(max_workers=2) as executor:
                def run_a():
                    threading.current_thread().name = "A"
                    return request(a_start)
                def run_b():
                    threading.current_thread().name = "B"
                    return request(b_start)
                a_future = executor.submit(run_a)
                wait(a_encoding, "A entered codec")
                b_future = executor.submit(run_b)
                try:
                    a_side = a_future.result(timeout=6)
                finally:
                    a_done.set()
                b_side = b_future.result(timeout=6)
        used = a_side["sigmas_used"]
        return {"mode": mode, "a_start": a_start, "b_start": b_start,
                "a_executed_stub_suffix": executed["A"], "a_recorded_sigmas": used,
                "a_record_matches_own_execution": used == executed["A"],
                "a_record_matches_training_array": used == training,
                "a_record_matches_b_suffix": "B" in executed and used == executed["B"],
                "b_record_matches_own_execution": b_side is None or b_side["sigmas_used"] == executed["B"],
                "events": events}


def main():
    with patch.object(socket, "create_connection", blocked), patch.object(socket.socket, "connect", blocked):
        runner = load_runner()
        first = json.loads((HERE / "receipts/sp_k12_s1.server.json").read_text())
        grid = first["latent"]["sigmas_request"]
        training = json.loads((HERE / "receipts/sp_k12_s2.server.json").read_text())["sigmas_used"]
        selector = selector_review(runner, grid)
        receipts = receipt_review(runner)
        cli = cli_review()
        variants = {"before": HERE / "source/server_before.py", "after": ROOT / "tools/cosmos_local/server.py"}
        races = {}
        for variant, source in variants.items():
            cases = [run_interleaving(source, grid, training, "serial")]
            for a, b in [(12, 19), (19, 12), (0, 34)]:
                for mode in ("next_training", "next_suffix"):
                    cases.append(run_interleaving(source, grid, training, mode, a, b))
            races[variant] = cases
            check(cases[0]["a_record_matches_own_execution"], variant + " serial control")
            check(all(c["b_record_matches_own_execution"] for c in cases), variant + " B control")
            if variant == "before":
                check(all(not c["a_record_matches_own_execution"] for c in cases[1:]), "before all6 controlled races corrupt A metadata")
                check(all(c["a_record_matches_training_array"] for c in cases if c["mode"] == "next_training"), "before training-array race")
                check(all(c["a_record_matches_b_suffix"] for c in cases if c["mode"] == "next_suffix"), "before foreign-suffix race")
            else:
                check(all(c["a_record_matches_own_execution"] for c in cases), "after all6 races and serial retain A suffix")
        report = {"scope": "Deterministic CPU software tests with stub pipeline/codec, no model or live endpoint",
                  "environment": {"python": platform.python_version(), "numpy": np.__version__, "requests": requests.__version__},
                  "source_sha256": {str(p.relative_to(ROOT)): sha(p) for p in [HERE / "source/server_before.py", HERE / "source/runner.py", ROOT / "tools/cosmos_local/server.py"]},
                  "original_server_md5": hashlib.md5((HERE / "source/server_before.py").read_bytes()).hexdigest(),
                  "selector": selector, "receipts": receipts, "cli": cli, "interleavings": races,
                  "checks": CHECKS, "passed": len(CHECKS), "failed": 0,
                  "limits": "Race demonstrated on exact historical handler source with stubs. Historical cause and schedules are NOT authenticated. Referee289 FAIL unchanged."}
        (HERE / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps({"pass": len(CHECKS), "sigma_targets": selector["sigma_targets"], "receipts": len(receipts),
                          "before_races_corrupt": 6, "after_races_correct": 6, "no_network_or_model": True}))


if __name__ == "__main__":
    main()

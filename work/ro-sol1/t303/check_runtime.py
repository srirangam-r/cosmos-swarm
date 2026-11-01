#!/usr/bin/env python3
"""Actual Python runtime checks; all HTTP is intercepted and sockets are forbidden.

Returned response bytes below are a synthetic transport fixture, not model output.
Existing raw native receipts are replayed unchanged. This checks records, not GPUs.
"""
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import socket
import sys
import tempfile
import types
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EXPECTED = {
    "sp_k12_s1": "ab7e94658d17a4d7c1f276dfdd55f2ac78b21ea668a19b03776247a4a63ad9d4",
    "sp_k12_s2": "d608a67786150243998fd59c7b4c162f2337a00cfa39e337d3183f421ddae00d",
    "sp_k19_s1": "055b5f4db2677bb9bb8db04a855449f09cd92f0ef3686a6af202ac217f8632cc",
    "sp_k19_s2": "c76ce9b3b73c41511cbf66a05c58e01bd10999824735cb79c23b35fbf281350c",
}
CHECKS = []


def check(ok, label):
    CHECKS.append({"name": label, "pass": bool(ok)})
    if not ok:
        raise AssertionError(label)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(label, directory):
    package = types.ModuleType(label)
    package.__path__ = [str(ROOT / "tools/nano_phys")]
    sys.modules[label] = package
    result = []
    for name in ("runner", "cli"):
        spec = importlib.util.spec_from_file_location(f"{label}.{name}", directory / f"{name}.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        result.append(module)
    return result


def observe(call):
    try:
        return {"accepted": True, "value": call()}
    except Exception as exc:
        return {"accepted": False, "exception": type(exc).__name__, "message": str(exc)}


class Response:
    status_code = 200
    content = b"synthetic HTTP response body; NOT a Nano clip"

    def __init__(self, raw):
        self.raw = raw
        self.headers = {"X-Clip-Id": "synthetic-replay-id", "X-Seconds": "0"}

    def raise_for_status(self):
        pass

    def json(self):
        return copy.deepcopy(self.raw)


def replay(runner, raw, root, label, **selection):
    out = root / f"{label}.mp4"
    calls = []

    def post(url, **kwargs):
        calls.append({"url": url, "data": kwargs["data"],
                      "files": [{"field": field, "name": value[0],
                                 "sha256": hashlib.sha256(value[1]).hexdigest()}
                                for field, value in kwargs["files"]]})
        return Response(raw)

    with patch.object(runner.requests, "post", post), patch.object(runner.requests, "get", lambda *a, **k: Response(raw)):
        result = runner.run_remote_nanophys(
            "http://fixture.invalid:8001", root / "input.png", root / "proxy.mp4",
            "synthetic transport fixture", out, **selection)
    return result, calls


def cli_case(cli, args):
    proxy_calls = []
    stdout, stderr = io.StringIO(), io.StringIO()

    def proxy(**kwargs):
        proxy_calls.append(True)
        return {"synthetic_mock": True}

    argv = ["nano_phys", "--image", "synthetic.png", "--prompt", "synthetic fixture",
            "--physics", "ball", "--center", "10,10", "--out", "synthetic.mp4",
            "--emit-queue-job"] + args
    with patch.object(sys, "argv", argv), patch.object(cli, "generate_ball_proxy", proxy), contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        try:
            cli.main()
            code = 0
        except SystemExit as exc:
            code = exc.code
        except Exception as exc:
            code = type(exc).__name__
    return {"exit": code, "proxy_calls": len(proxy_calls), "stdout": stdout.getvalue(), "stderr": stderr.getvalue()}


def main():
    before, before_cli = load("t303_before", HERE / "baseline")
    after, after_cli = load("t303_after", ROOT / "tools/nano_phys")
    result = {"scope": "Python software and unchanged native receipt replay only; no HTTP requests, GPU execution, live deployment certification or physics claims",
              "sources": {"baseline_runner": digest(HERE / "baseline/runner.py"),
                          "baseline_cli": digest(HERE / "baseline/cli.py"),
                          "current_runner": digest(ROOT / "tools/nano_phys/runner.py"),
                          "current_cli": digest(ROOT / "tools/nano_phys/cli.py")},
              "receipts": [], "selectors": [], "cli": [], "transport_fixtures": []}
    with tempfile.TemporaryDirectory(prefix="ro-sol1-t303-") as temp, patch.object(socket.socket, "connect", side_effect=AssertionError("network forbidden")), patch.object(socket, "create_connection", side_effect=AssertionError("network forbidden")):
        temp = Path(temp)
        (temp / "input.png").write_bytes(b"synthetic image upload fixture")
        (temp / "proxy.mp4").write_bytes(b"synthetic proxy upload fixture")
        for name, expected in EXPECTED.items():
            path = HERE / "receipts" / f"{name}.server.json"
            check(digest(path) == expected, f"{name} exact published receipt bytes")
            raw = json.loads(path.read_text())
            latent = raw["latent"]
            grid, used = latent["sigmas_request"], raw["sigmas_used"]
            k = latent["start_step"]
            check(grid == after.NATIVE_SIGMAS_35, f"{name} full grid matches shipped table")
            check(len(grid) == 36 and all(0 <= v <= 1 for v in grid), f"{name} full grid size/domain")
            check(latent["sigma_start"] == grid[k], f"{name} returned start matches grid")
            record = {"name": name, "sha256": expected, "start_step": k,
                      "sigma_start": latent["sigma_start"], "full_grid_match": True,
                      "executed_suffix_match": used == grid[k:], "used_count": len(used),
                      "expected_suffix_count": len(grid[k:]), "used_first": used[0], "used_last": used[-1],
                      "model": raw.get("model"), "scheduler": raw.get("scheduler"),
                      "server_rev": raw.get("server_rev")}
            check(record["executed_suffix_match"] == (name in ("sp_k12_s1", "sp_k19_s2")), f"{name} pinned suffix observation")
            for label, runner in (("before", before), ("after", after)):
                extracted, calls = replay(runner, raw, temp, f"{label}-{name}", start_step=k)
                check(extracted["server_latent"] == latent and extracted["sigmas_used"] == used,
                      f"{label} {name} actual Python preserves raw grid/start/suffix")
                check(extracted["actual_start_step"] == k and extracted["actual_sigma_start"] == grid[k],
                      f"{label} {name} actual Python extracts returned start")
                request = json.loads(calls[0]["data"]["extra_params"])
                check(request["noise"]["device"] == "cpu" and request["latent"]["start_step"] == k,
                      f"{label} {name} actual request CPU noise/start")
            result["receipts"].append(record)

        for label, sigma, steps, accepted in [
            ("nan", float("nan"), 35, False), ("positive_inf", float("inf"), 35, False),
            ("negative_inf", -float("inf"), 35, False), ("short20", .9, 20, False),
            ("short1", .9, 1, False), ("long36", .9, 36, False),
            ("float_steps", .9, 35.0, False), ("bool_steps", .9, True, False),
            ("bool_sigma", True, 35, False), ("zero", 0, 35, True),
            ("one", 1, 35, True), ("lead", .9, 35, True), ("lower", -.1, 35, False)]:
            a = observe(lambda: before.sigma_to_step(sigma, steps))
            b = observe(lambda: after.sigma_to_step(sigma, steps))
            result["selectors"].append({"case": label, "before": a, "after": b})
            check(b["accepted"] == accepted, f"selector {label} acceptance")
            if accepted:
                check(a == b and 0 <= b["value"] < 35, f"selector {label} unchanged valid selection")
        for args, expected in [(["--sigma", "nan"], False), (["--sigma", ".9", "--steps", "20"], False),
                               (["--steps", "1"], False), (["--steps", "0", "--start-step", "0"], False),
                               (["--sigma", ".9"], True), ([], True),
                               (["--steps", "20", "--start-step", "7"], True)]:
            a, b = cli_case(before_cli, args), cli_case(after_cli, args)
            result["cli"].append({"args": args, "before": a, "after": b})
            check((b["exit"] == 0) == expected, f"CLI {args} acceptance")
            check(b["proxy_calls"] == int(expected), f"CLI {args} rejects before proxy build")
            if expected:
                check(len(b["stdout"].splitlines()) == 1, f"CLI {args} pure JSONL")
                job = json.loads(b["stdout"])
                expected_step = 19 if "--sigma" in args else (7 if "--start-step" in args else 14)
                check(job["extra_params"]["latent"]["start_step"] == expected_step, f"CLI {args} step")

        raw = json.loads((HERE / "receipts/sp_k19_s2.server.json").read_text())
        for case, selection in [
            ("nan", {"sigma": float("nan")}),
            ("sigma_non35", {"sigma": .9, "steps": 20}),
            ("bool_start", {"start_step": True}),
            ("float_start", {"start_step": 1.5}),
            ("terminal", {"start_step": 35}),
            ("negative_start", {"start_step": -1}),
            ("short_default", {"steps": 1}),
        ]:
            calls = []
            with patch.object(after.requests, "post", lambda *a, **k: calls.append(True)):
                observed = observe(lambda: after.run_remote_nanophys(
                    "http://fixture.invalid:8001", temp / "input.png", temp / "proxy.mp4",
                    "synthetic fixture", temp / f"invalid-{case}.mp4", **selection))
            check(not observed["accepted"] and observed["exception"] in ("ValueError", "TypeError"), f"remote {case} rejected")
            check(not calls, f"remote {case} rejected before HTTP")
        resolved, calls = replay(after, raw, temp, "resolved-sigma", sigma=.9)
        check(resolved["start_step"] == 19 and resolved["nominal_sigma"] == .89844, "remote sigma0.9 resolves recorded step19")
        check(json.loads(calls[0]["data"]["extra_params"])["latent"]["start_step"] == 19, "remote sigma0.9 actual request step19")
        for variant in ("empty_summary", "conflicting_summary"):
            changed = copy.deepcopy(raw)
            changed["summary"] = {} if variant == "empty_summary" else {"sigma_start": .6}
            extracted, _ = replay(after, changed, temp, variant, start_step=19)
            check(extracted["actual_sigma_start"] == .89844, f"{variant} latent retained")
            check(("summary_sigma_start_conflict" in extracted) == (variant == "conflicting_summary"), f"{variant} conflict recording")
            result["transport_fixtures"].append({"name": variant, "actual_sigma_start": extracted["actual_sigma_start"],
                                                 "conflict_recorded": extracted.get("summary_sigma_start_conflict")})
        explicit, _ = replay(after, raw, temp, "explicit-non35", steps=20, start_step=7)
        check(explicit["nominal_sigma"] is None, "explicit non35 step has no invented nominal sigma")
        result["limits"] = ["Both unchanged raw receipts and synthetic conflict fixtures still return normally: runner records metadata; it does not certify full grid/start/suffix/deployment.",
                            "Archived receipts bind the November 1 run only, not a currently live endpoint.",
                            "Two inconsistent sigmas_used arrays do not prove those values were executed; no inference about actual sampling or model quality."]
    result["checks"] = CHECKS
    result["pass"] = len(CHECKS)
    result["fail"] = 0
    (HERE / "acceptance.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"pass": len(CHECKS), "fail": 0, "full_grids_match": 4, "suffixes_match": 2, "network_requests": 0}))


if __name__ == "__main__":
    main()

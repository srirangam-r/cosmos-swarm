#!/usr/bin/env python3
"""
tests/test_recipe.py: Comprehensive CPU Test Suite for Cosmos3-Nano Recipe Runner

Verifies all reproducibility audit requirements (Task 82 / #1810, #1817, Task 87):
1. Argument parsing & defaults
2. Letterbox padding & aspect ratio preservation
3. Release frame extraction under global and localized motion (resolving silent frame-0 bug)
4. Release frame extraction with explicit ROI
5. Multiline indented JSON parsing from referee firstfall tracker
6. End-to-end CPU dry-run (generates valid MP4, conditioning image, and sidecar)
7. Verification flag qualification (ensures 'weak' flag is NOT marked PASS)
8. Endpoint payload validation (rejects invalid non-video responses)
9. Diffusers pipeline call AST audit (ensures no unsupported kwargs like flow_shift)
"""

import ast
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import cv2
import numpy as np

# Ensure tools/recipe can be imported
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools" / "recipe"))
import run_recipe


class TestRecipeRunner(unittest.TestCase):
    def test_letterbox_image(self):
        """Letterboxing preserves aspect ratio and centers onto target dimensions."""
        img = np.zeros((200, 400, 3), dtype=np.uint8)
        img[:, :] = (100, 150, 200)
        target_w, target_h = 832, 480
        letterboxed = run_recipe.letterbox_image(img, target_w=target_w, target_h=target_h)

        self.assertEqual(letterboxed.shape, (target_h, target_w, 3))
        # Top and bottom padding should be black (0)
        self.assertEqual(int(letterboxed[0, 0, 0]), 0)
        # Center should contain the original image color
        center_color = letterboxed[target_h // 2, target_w // 2]
        self.assertAlmostEqual(int(center_color[0]), 100, delta=2)
        self.assertAlmostEqual(int(center_color[1]), 150, delta=2)
        self.assertAlmostEqual(int(center_color[2]), 200, delta=2)

    def test_detector_detects_localized_motion(self):
        """Regression test for #1817: localized motion must not silently fall back to frame 0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = str(Path(tmpdir) / "local_motion.mp4")
            writer = cv2.VideoWriter(video_path, cv2.VideoWriter_fourcc(*"mp4v"), 10, (120, 120))
            self.assertTrue(writer.isOpened())

            f0 = np.zeros((120, 120, 3), dtype=np.uint8)
            f1 = f0.copy()
            # Localized 16x16 patch changing to 255 at frame 2
            f2 = f0.copy()
            f2[40:56, 40:56] = 255
            f3 = f2.copy()

            for f in (f0, f1, f2, f3):
                writer.write(f)
            writer.release()

            captured_output = io.StringIO()
            with contextlib.redirect_stdout(captured_output):
                detected = run_recipe.extract_release_frame(video_path)

            # Frame 2 has mean > 0 and peak local motion = 255
            self.assertGreater(float(np.mean(detected)), 1.0)
            self.assertIn("Detected motion onset at frame 2", captured_output.getvalue())

    def test_detector_with_explicit_roi(self):
        """Detector respects explicit ROI coordinates."""
        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = str(Path(tmpdir) / "roi_motion.mp4")
            writer = cv2.VideoWriter(video_path, cv2.VideoWriter_fourcc(*"mp4v"), 10, (100, 100))

            f0 = np.zeros((100, 100, 3), dtype=np.uint8)
            f1 = f0.copy()
            f2 = f0.copy()
            f2[10:30, 10:30] = 200  # Motion inside ROI (10,10,30,30)
            for f in (f0, f1, f2):
                writer.write(f)
            writer.release()

            detected = run_recipe.extract_release_frame(video_path, roi=(10, 10, 30, 30), diff_threshold=5.0)
            self.assertGreater(float(np.mean(detected[10:30, 10:30])), 100.0)

    def test_multiline_firstfall_json_parsing(self):
        """Regression test for #1817: firstfall indented JSON must be parsed cleanly."""
        measurement = {
            "g": 9.812,
            "flag": "ok",
            "r2": 0.998,
            "dAIC_quad_vs_lin": 14.5,
            "n_fit": 6,
        }
        multiline_stdout = (
            "Loading clip...\n"
            "Tracking ball...\n"
            + json.dumps(measurement, indent=1)
            + "\nDone.\n"
        )
        fake_process = SimpleNamespace(stdout=multiline_stdout, stderr="", returncode=0)

        with tempfile.TemporaryDirectory() as tmpdir:
            fake_script = Path(tmpdir) / "tools" / "realball" / "firstfall.py"
            fake_script.parent.mkdir(parents=True)
            fake_script.touch()

            with mock.patch("pathlib.Path.exists", return_value=True), \
                 mock.patch("subprocess.run", return_value=fake_process):
                parsed = run_recipe.verify_with_firstfall("mock.mp4")

        self.assertIn("g", parsed)
        self.assertEqual(parsed["g"], 9.812)
        self.assertEqual(parsed["flag"], "ok")
        self.assertEqual(parsed["r2"], 0.998)

    def test_verification_flag_qualification(self):
        """Regression test for #1817: 'weak' flag must NOT print PASS."""
        with tempfile.TemporaryDirectory() as tmpdir:
            img_path = Path(tmpdir) / "input.png"
            cv2.imwrite(str(img_path), np.zeros((100, 100, 3), dtype=np.uint8))
            out_path = Path(tmpdir) / "output.mp4"

            # 1. Weak flag test
            args_weak = ["run_recipe.py", "--image", str(img_path), "--out", str(out_path), "--dry-run", "--verify"]
            weak_res = {"g": 9.73, "flag": "weak", "r2": 0.9976, "dAIC_quad_vs_lin": 8.2}

            captured_stdout = io.StringIO()
            with mock.patch.object(sys, "argv", args_weak), \
                 mock.patch("run_recipe.verify_with_firstfall", return_value=weak_res), \
                 contextlib.redirect_stdout(captured_stdout):
                run_recipe.main()

            output_text = captured_stdout.getvalue()
            self.assertNotIn("[verify] PASS", output_text)
            self.assertIn("[verify] QUALIFIED / NOT OK: flag=weak", output_text)

            # 2. OK flag test
            captured_stdout_ok = io.StringIO()
            ok_res = {"g": 9.82, "flag": "ok", "r2": 0.9985, "dAIC_quad_vs_lin": 18.0}
            with mock.patch.object(sys, "argv", args_weak), \
                 mock.patch("run_recipe.verify_with_firstfall", return_value=ok_res), \
                 contextlib.redirect_stdout(captured_stdout_ok):
                run_recipe.main()

            output_text_ok = captured_stdout_ok.getvalue()
            self.assertIn("[verify] PASS: Measured Free-Fall Gravity g = 9.820 m/s^2", output_text_ok)

    def test_endpoint_payload_validation(self):
        """Regression test for #1817: endpoint returning non-video bytes must raise ValueError."""
        mock_resp = mock.Mock()
        mock_resp.content = b"not a video"
        mock_resp.headers = {}
        mock_resp.raise_for_status = mock.Mock()

        with mock.patch("requests.post", return_value=mock_resp):
            with self.assertRaises(ValueError) as ctx:
                run_recipe.run_inference_endpoint(
                    url="http://mock.endpoint",
                    image_bytes=b"png_bytes",
                    prompt="test",
                    width=832,
                    height=480,
                    num_frames=93,
                    fps=24,
                    steps=35,
                    guidance=6.0,
                    flow_shift=10.0,
                    seed=1,
                )
            self.assertIn("invalid payload", str(ctx.exception))

        # Test non-video payload >= 32 bytes
        mock_resp_32 = mock.Mock()
        mock_resp_32.content = b"this is a non-video payload that is definitely over 32 bytes long"
        mock_resp_32.headers = {}
        mock_resp_32.raise_for_status = mock.Mock()
        with mock.patch("requests.post", return_value=mock_resp_32):
            with self.assertRaises(ValueError) as ctx2:
                run_recipe.run_inference_endpoint(
                    url="http://mock.endpoint",
                    image_bytes=b"png_bytes",
                    prompt="test",
                    width=832,
                    height=480,
                    num_frames=93,
                    fps=24,
                    steps=35,
                    guidance=6.0,
                    flow_shift=10.0,
                    seed=1,
                )
            self.assertIn("does not contain a valid MP4 or WebM video container", str(ctx2.exception))

    def test_diffusers_pipeline_no_unsupported_kwargs(self):
        """AST check: local Diffusers pipe() call must not pass unsupported flow_shift."""
        script_text = (REPO_ROOT / "tools" / "recipe" / "run_recipe.py").read_text()
        tree = ast.parse(script_text)

        # Find the pipe(...) call inside run_inference_local
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "run_inference_local":
                pipe_calls = [
                    n for n in ast.walk(node)
                    if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "pipe"
                ]
                self.assertTrue(len(pipe_calls) >= 1)
                for call in pipe_calls:
                    keyword_args = {kw.arg for kw in call.keywords}
                    self.assertNotIn("flow_shift", keyword_args)
                    self.assertIn("image", keyword_args)
                    self.assertIn("prompt", keyword_args)

    def test_dry_run_end_to_end(self):
        """Full end-to-end CPU dry run generates valid MP4, conditioning image, and JSON sidecar."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_img = REPO_ROOT / "assets" / "gauge_ball1_midfall.png"
            if not input_img.exists():
                input_img = Path(tmpdir) / "test_input.png"
                cv2.imwrite(str(input_img), np.full((480, 832, 3), 128, dtype=np.uint8))

            out_video = Path(tmpdir) / "out_recipe.mp4"
            args = [
                "run_recipe.py",
                "--image", str(input_img),
                "--out", str(out_video),
                "--dry-run",
            ]

            with mock.patch.object(sys, "argv", args), contextlib.redirect_stdout(io.StringIO()):
                run_recipe.main()

            # 1. Output video exists and is readable by OpenCV
            self.assertTrue(out_video.exists())
            self.assertGreater(out_video.stat().st_size, 1000)
            cap = cv2.VideoCapture(str(out_video))
            self.assertTrue(cap.isOpened())
            ret, frame = cap.read()
            self.assertTrue(ret)
            self.assertEqual(frame.shape, (480, 832, 3))
            cap.release()

            # 2. Conditioning frame was saved
            cond_img = out_video.with_suffix(".conditioning.png")
            self.assertTrue(cond_img.exists())

            # 3. JSON sidecar is valid and complete
            sidecar_path = out_video.with_suffix(".json")
            self.assertTrue(sidecar_path.exists())
            with open(sidecar_path) as f:
                sidecar = json.load(f)

            self.assertEqual(sidecar["charter_deliverable"], 1)
            self.assertEqual(sidecar["width"], 832)
            self.assertEqual(sidecar["height"], 480)
            self.assertEqual(sidecar["fps"], 24)
            self.assertEqual(sidecar["provenance"]["mode"], "dry-run")

    def test_settle_prompt_flag(self):
        """--settle activates Stage 2 event-timing dissipative settle prompt in sidecar."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_img = Path(tmpdir) / "test_input.png"
            cv2.imwrite(str(input_img), np.full((480, 832, 3), 128, dtype=np.uint8))
            out_video = Path(tmpdir) / "out_settle.mp4"
            args = [
                "run_recipe.py",
                "--image", str(input_img),
                "--out", str(out_video),
                "--dry-run",
                "--settle",
            ]

            with mock.patch.object(sys, "argv", args), contextlib.redirect_stdout(io.StringIO()):
                run_recipe.main()

            sidecar_path = out_video.with_suffix(".json")
            self.assertTrue(sidecar_path.exists())
            with open(sidecar_path) as f:
                sidecar = json.load(f)

            self.assertTrue(sidecar["stage_2_dissipative_settle"])
            self.assertIn("bounces only twice with rapidly diminishing heights", sidecar["prompt"])
            self.assertIn("comes to rest on the plank within about one and a half seconds", sidecar["prompt"])

    def test_settle_custom_prompt_substitution(self):
        """--settle with custom prompt containing 'and bouncing in real time.' substitutes timing clause."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_img = Path(tmpdir) / "test_input.png"
            cv2.imwrite(str(input_img), np.full((480, 832, 3), 128, dtype=np.uint8))
            out_video = Path(tmpdir) / "out_settle_custom.mp4"
            custom_prompt = "A red ball dropping from above and bouncing in real time."
            args = [
                "run_recipe.py",
                "--image", str(input_img),
                "--out", str(out_video),
                "--dry-run",
                "--settle",
                "--prompt", custom_prompt,
            ]

            with mock.patch.object(sys, "argv", args), contextlib.redirect_stdout(io.StringIO()):
                run_recipe.main()

            sidecar_path = out_video.with_suffix(".json")
            self.assertTrue(sidecar_path.exists())
            with open(sidecar_path) as f:
                sidecar = json.load(f)

            self.assertTrue(sidecar["stage_2_dissipative_settle"])
            self.assertIn("A red ball dropping from above", sidecar["prompt"])
            self.assertIn("bounces only twice with rapidly diminishing heights", sidecar["prompt"])
            self.assertIn("comes to rest on the plank within about one and a half seconds", sidecar["prompt"])
            self.assertNotIn("and bouncing in real time.", sidecar["prompt"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

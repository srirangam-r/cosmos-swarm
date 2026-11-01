import contextlib
import hashlib
import io
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

import cv2
import numpy as np

import run_recipe


class RecipeContractTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.image = self.root / "unverified_midfall.png"
        cv2.imwrite(str(self.image), np.full((24, 32, 3), 120, dtype=np.uint8))
        self.output = self.root / "out.mp4"

    def tearDown(self):
        self.temporary.cleanup()

    def run_main(self, *arguments):
        argv = ["run_recipe.py", *arguments, "--out", str(self.output), "--width", "64", "--height", "48"]
        with mock.patch.object(sys, "argv", argv), contextlib.redirect_stdout(io.StringIO()), \
             contextlib.redirect_stderr(io.StringIO()):
            run_recipe.main()

    def test_generic_rejects_missing_and_replacing_prompt_flags(self):
        cases = [(), ("--prompt", "A cart rolls.", "--basic-prompt"),
                 ("--prompt", "A cart rolls.", "--settle")]
        for arguments in cases:
            with self.subTest(arguments=arguments), self.assertRaises(SystemExit):
                self.run_main("--image", str(self.image), "--dry-run", "--rule-generic", *arguments)

    def test_remote_sends_original_prompt_once_and_exact_conditioning(self):
        response = mock.Mock()
        response.content = b"\x00\x00\x00\x20ftyp" + b"x" * 40
        response.headers = {}
        response.raise_for_status = mock.Mock()
        with mock.patch("requests.post", return_value=response) as post, \
             mock.patch.object(run_recipe, "extract_release_frame", side_effect=AssertionError("later frame read")):
            self.run_main("--image", str(self.image), "--image-role", "frame0", "--rule-generic",
                          "--prompt", "A cart rolls.  ", "--seed", "7", "--url", "http://example.invalid:8021")
        request = post.call_args.kwargs
        prompt = request["data"]["prompt"]
        self.assertEqual(prompt, "A cart rolls. " + run_recipe.RULE_R)
        self.assertEqual(prompt.count(run_recipe.RULE_R), 1)
        self.assertEqual(request["data"]["seed"], "7")
        self.assertEqual(request["data"]["flow_shift"], "10.0")
        self.assertEqual(request["data"]["num_frames"], "93")
        conditioning = request["files"]["input_reference"][1]
        sidecar = json.loads(self.output.with_suffix(".json").read_text())
        self.assertEqual(sidecar["prompt"], prompt)
        self.assertEqual(conditioning, self.output.with_suffix(".conditioning.png").read_bytes())
        self.assertEqual(sidecar["conditioning_image_sha256"], hashlib.sha256(conditioning).hexdigest())
        self.assertEqual(sidecar["workflow_mode"], "user_frame0_inference")
        self.assertEqual(sidecar["input_image_role_declared"], "frame0")
        self.assertEqual(sidecar["sampler_effective"]["status"], "unknown_remote_endpoint")

    def test_existing_rule_not_duplicated(self):
        prompt = "A cart rolls. " + run_recipe.RULE_R
        self.run_main("--image", str(self.image), "--dry-run", "--rule-generic", "--prompt", prompt)
        sidecar = json.loads(self.output.with_suffix(".json").read_text())
        self.assertEqual(sidecar["prompt"], prompt)
        self.assertEqual(sidecar["workflow_mode"], "provided_image_origin_unspecified")
        self.assertEqual(sidecar["sampler_effective"]["status"], "not_run")
        self.assertEqual(sidecar["num_frames"], 93)
        self.assertEqual(sidecar["generated_num_frames"], 24)

    def test_structured_json_does_not_become_invalid_json(self):
        path = self.root / "prompt.json"
        path.write_text(json.dumps({"scene": "a cart rolls"}))
        for prompt in [str(path), path.read_text()]:
            with self.subTest(prompt=prompt), self.assertRaises(SystemExit):
                self.run_main("--image", str(self.image), "--dry-run", "--rule-generic", "--prompt", prompt)

    def test_video_frame_index_is_recorded_and_not_mislabeled(self):
        video = self.root / "input.mp4"
        writer = cv2.VideoWriter(str(video), cv2.VideoWriter_fourcc(*"mp4v"), 24, (32, 24))
        self.assertTrue(writer.isOpened())
        for index in range(3):
            writer.write(np.full((24, 32, 3), 40 * index, dtype=np.uint8))
        writer.release()
        for index, mode in [(0, "user_frame0_inference"), (2, "diagnostic_mid_event_conditioning")]:
            with self.subTest(index=index):
                self.run_main("--video", str(video), "--frame-idx", str(index), "--dry-run",
                              "--rule-generic", "--prompt", "A cart rolls.")
                sidecar = json.loads(self.output.with_suffix(".json").read_text())
                self.assertEqual(sidecar["input_frame_index"], index)
                self.assertEqual(sidecar["workflow_mode"], mode)
                self.assertFalse(sidecar["release_frame_detection_requested"])
                if index:
                    self.assertIsNone(sidecar["stage_1_release_seam"])

    def test_local_pipeline_receives_requested_prompt_and_image(self):
        captured = {}

        class Scheduler:
            def __init__(self, config):
                self.config = config

            @classmethod
            def from_config(cls, config, **kwargs):
                return cls({**config, **kwargs})

        class Pipeline:
            def __init__(self):
                self.scheduler = Scheduler({"use_karras_sigmas": True, "use_flow_sigmas": True})

            @classmethod
            def from_pretrained(cls, *args, **kwargs):
                return cls()

            def enable_group_offload(self):
                pass

            def __call__(self, **kwargs):
                captured.update(kwargs)
                return types.SimpleNamespace(video=np.zeros((1, 5, 8, 8, 3), dtype=np.uint8))

        generator = mock.Mock()
        generator.manual_seed.return_value = generator
        torch = types.ModuleType("torch")
        torch.bfloat16 = "bfloat16"
        torch.Generator = mock.Mock(return_value=generator)
        torch.cuda = types.SimpleNamespace(is_available=lambda: False)
        diffusers = types.ModuleType("diffusers")
        diffusers.Cosmos3OmniPipeline = Pipeline
        schedulers = types.ModuleType("diffusers.schedulers")
        unipc = types.ModuleType("diffusers.schedulers.scheduling_unipc_multistep")
        unipc.UniPCMultistepScheduler = Scheduler
        modules = {"torch": torch, "diffusers": diffusers, "diffusers.schedulers": schedulers,
                   "diffusers.schedulers.scheduling_unipc_multistep": unipc}
        with mock.patch.dict(sys.modules, modules), contextlib.redirect_stdout(io.StringIO()):
            frames, meta = run_recipe.run_inference_local("model", "image", "prompt", 64, 48, 93, 24,
                                                           35, 6.0, 10.0, 7)
        self.assertEqual(captured["image"], "image")
        self.assertEqual(captured["prompt"], "prompt")
        self.assertEqual(captured["num_frames"], 93)
        self.assertNotIn("flow_shift", captured)
        generator.manual_seed.assert_called_once_with(7)
        self.assertTrue(meta["sampler_effective"]["use_karras_sigmas"])
        self.assertEqual(meta["sampler_effective"]["flow_shift_config"], 10.0)
        self.assertEqual(len(frames), 5)


if __name__ == "__main__":
    unittest.main()

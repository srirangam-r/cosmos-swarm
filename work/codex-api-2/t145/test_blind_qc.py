import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import cv2
import numpy as np

import blind_qc


class BlindQCTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.clips = self.root / "clips"
        self.clips.mkdir()
        self.output = self.root / "blind"

    def tearDown(self):
        self.temporary.cleanup()

    def make_clips(self, frame_count=93):
        for index, arm in enumerate(blind_qc.ARMS):
            path = self.clips / f"t145_block_{arm}_s4.mp4"
            writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 24, (64, 48))
            self.assertTrue(writer.isOpened())
            for frame in range(frame_count):
                writer.write(np.full((48, 64, 3), 20 + 30 * index, dtype=np.uint8))
            writer.release()

    def run_blinding(self):
        with patch.object(blind_qc, "SCENES", ("block",)), patch.object(blind_qc, "SEEDS", (4,)), \
             patch.object(sys, "argv", ["blind_qc.py", "--clips", str(self.clips), "--out", str(self.output)]), \
             contextlib.redirect_stdout(io.StringIO()):
            blind_qc.main()

    def test_missing_clips_fail_before_creating_output(self):
        with self.assertRaises(SystemExit):
            self.run_blinding()
        self.assertFalse(self.output.exists())

    def test_shuffled_key_matches_native_hardlinks(self):
        self.make_clips()
        self.run_blinding()
        key = json.loads((self.output / "UNBLIND_key.json").read_text())
        self.assertEqual(len(key), 1)
        identifier, entry = next(iter(key.items()))
        self.assertTrue((self.output / f"{identifier}.jpg").is_file())
        self.assertEqual(set(entry["rows"].values()), set(blind_qc.ARMS))
        for label, arm in entry["rows"].items():
            source = self.clips / f"t145_block_{arm}_s4.mp4"
            native = self.output / "native" / f"{identifier}_{label}.mp4"
            self.assertTrue(os.path.samefile(source, native))
        with self.assertRaises(FileExistsError):
            self.run_blinding()

    def test_short_clip_is_not_silently_zero_filled(self):
        self.make_clips(frame_count=80)
        with self.assertRaisesRegex(ValueError, "Missing required frames"):
            self.run_blinding()


if __name__ == "__main__":
    unittest.main()

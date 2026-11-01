"""Verify published input bytes, or reproduce only the two declared source frames.

No mocap, motion fit, proxy builder, model client, or referee submission.
"""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request

import cv2
import numpy as np


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sources", type=Path, help="Directory for original 6.mp4 / 14.mp4")
    ap.add_argument("--download", action="store_true", help="Download missing originals into --sources")
    ap.add_argument("--out", type=Path, help="Optional directory for reproduced PNGs; cannot be artifact directory")
    args = ap.parse_args()
    here = Path(__file__).resolve().parent
    manifest = json.loads((here / "manifest.json").read_text())
    if args.download and args.sources is None:
        ap.error("--download requires --sources")
    if args.out is not None:
        if args.out.resolve() == here:
            ap.error("--out must not overwrite frozen artifacts")
        args.out.mkdir(parents=True, exist_ok=True)
    results = []
    for rec in manifest["records"]:
        images = [rec["rejected_frame0"], rec]
        for entry in images:
            path = here / entry["image"]
            assert sha256(path) == entry["image_sha256"], (path, "published hash")
            published = cv2.imread(str(path))
            assert published.shape == (480, 832, 3), path
            assert not published[:6].any() and not published[-6:].any(), path
        if args.sources is None:
            results.append({"id": rec["id"], "published_images": "PASS", "source_reproduction": "NOT_RUN"})
            continue
        args.sources.mkdir(parents=True, exist_ok=True)
        video = args.sources / (str(rec["id"]) + ".mp4")
        if not video.exists() and args.download:
            partial = video.with_suffix(".mp4.part")
            urllib.request.urlretrieve(rec["source_url"], partial)
            assert sha256(partial) == rec["source_sha256"], "download source hash"
            partial.replace(video)
        assert sha256(video) == rec["source_sha256"], (video, "source hash")
        for entry in images:
            cap = cv2.VideoCapture(str(video))
            assert cap.isOpened(), video
            assert cap.set(cv2.CAP_PROP_POS_FRAMES, entry["frame_index"])
            ok, frame = cap.read()
            position = cap.get(cv2.CAP_PROP_POS_FRAMES)
            cap.release()
            assert ok and position == entry["frame_index"] + 1, (video, position)
            assert frame.shape[:2] == (720, 1280), frame.shape
            resized = cv2.resize(frame, (832, 468), interpolation=cv2.INTER_AREA)
            image = cv2.copyMakeBorder(resized, 6, 6, 0, 0, cv2.BORDER_CONSTANT, value=(0, 0, 0))
            published = cv2.imread(str(here / entry["image"]))
            assert np.array_equal(image, published), (video, entry["frame_index"], "pixel mismatch")
            # PNG encoders can differ across builds; exact pixels are checked above.
            if args.out is not None:
                assert cv2.imwrite(str(args.out / entry["image"]), image)
        results.append({"id": rec["id"], "published_images": "PASS", "source_reproduction": "PASS", "indices": [0, 186]})
    print(json.dumps({"scope": "input identity only; no physics validation", "results": results}, indent=2))


if __name__ == "__main__":
    main()

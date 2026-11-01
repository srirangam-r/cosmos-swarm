#!/usr/bin/env python3
"""Create an own review directory of symlinks to14 published originals."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2]
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
for item in json.loads((ROOT/'source_locations.json').read_text()):
 src=REPO/item['repo_path'];assert hashlib.sha256(src.read_bytes()).hexdigest()==item['sha256']
 dst=out/(item['name']+'.mp4')
 if not dst.exists():dst.symlink_to(src.resolve())
 assert hashlib.sha256(dst.read_bytes()).hexdigest()==item['sha256']
print('14 published original hashes match')

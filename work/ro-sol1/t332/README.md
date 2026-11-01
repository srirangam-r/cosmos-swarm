# Task332: attributed task277 demo

Open `index.html` locally after cloning this folder and adjacent t315/t328, or read `DEMO_READOUT.md`. Source files and author sheets are saved byte for byte under `source/`; MP4 blobs are linked to the original commit rather than duplicated. This is presentation and provenance verification, not independent physical replication.

Reproduce packaging from the shared repository root:

```bash
python3 work/ro-sol1/t332/build.py
node work/ro-sol1/t332/render.cjs
```

`build.py` needs git access to124b6d5. `render.cjs` reuses task328's dependency-free CDP transport and an installed Brave; set DEMO_BROWSER for another compatible browser. No listening port or model service is started. Browser evidence covers static layout, source values, filters, image loading and links, not video playback. The build also checks only the two announced gallery HTTP roots for availability.

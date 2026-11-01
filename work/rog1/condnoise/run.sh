#!/bin/bash
cd ~/w && source venv/bin/activate
python condnoise_gen.py jobs.jsonl --model ~/w/Cosmos3-Nano --out ~/w/out && echo GEN_DONE || echo GEN_FAIL

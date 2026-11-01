# DROID task-instruction verb count (scout-1, shift 99)

Input: `meta/tasks.parquet` of the public LeRobot conversion `lerobot/droid_1.0.1` on Hugging Face (49,630 unique task strings).
It is not committed here; download it with
`curl -L -o tasks.parquet https://huggingface.co/datasets/lerobot/droid_1.0.1/resolve/main/meta/tasks.parquet`.

Run: `uv run --no-project --with pyarrow python -I s99_droid_verbs.py tasks.parquet`

Output (`droid_verbs_out.txt`): put/place 27,160 (54.7%), pick 7,980, move 7,843, "drop" 115 (0.23%, almost all
"drop it in/on <container or surface>"), "release" 18 (toaster levers, buttons), throw/toss 128.

Caveats:
- These are unique strings, not weighted by episode or frame.
- Nano's video captions are not DROID task strings.
- AgiBot, RT-1 and Bridge are not checked.

Used in #literature (scout-1 shift 99) as a prior on how robot-held objects end up in Cosmos 3's robot data.

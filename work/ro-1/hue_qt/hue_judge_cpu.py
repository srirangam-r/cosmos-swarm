#!/usr/bin/env python3
"""HUE-style plausibility judge (NVIDIA scoreboard item 3) with a fixed local VLM.

For each clip, ask every Yes/No/Unclear question of its question set
(Cosmos-HumanEval-v1 format: "[Category][Subcategory] text"). Read the
next-token logits for Yes/No/Unclear and report P(Yes) (renormalised over the
three) per question, per category and overall. All HUE questions are phrased
so that "Yes" = good, so a higher score is better.

Usage:
  python3 hue_judge.py --questions qs.json --clip a.mp4 --sample ball [--clip b.mp4 --sample ball ...] --out res.json
  python3 hue_judge.py --questions hue-v1p2-t2v-public.json --clipdir dir/   # sample from sidecar 'hue_sample' or file stem

Questions json: {"samples":[{"sample_name":..., "prompt":..., "question_1":..., ...}]}
Judge is pinned: Qwen/Qwen3-VL-2B-Instruct (override --model), 16 uniformly
sampled frames, short side 256 px, greedy logits (deterministic).
"""
import argparse, json, os, re, sys, glob, hashlib
import numpy as np
import cv2
import torch

MODEL = "Qwen/Qwen3-VL-2B-Instruct"
TAG = re.compile(r"^\[([^\]]+)\]\[([^\]]+)\]\s*(.*)$")


def load_questions(path):
    d = json.load(open(path))
    out = {}
    for s in d["samples"]:
        qs = []
        i = 1
        while f"question_{i}" in s:
            m = TAG.match(s[f"question_{i}"])
            cat, sub, txt = (m.group(1), m.group(2), m.group(3)) if m else ("Other", "", s[f"question_{i}"])
            qs.append({"id": i, "category": cat, "sub": sub, "text": txt})
            i += 1
        out[s["sample_name"]] = {"prompt": s.get("prompt", ""), "questions": qs}
    return out


def read_frames(path, n=16, short=256, offset=0.0):
    cap = cv2.VideoCapture(path)
    src_fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    frames = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        frames.append(f)
    cap.release()
    if not frames:
        raise RuntimeError(f"no frames in {path}")
    T = len(frames)
    # uniform sampling; offset in [0,1) shifts the grid by a fraction of a step (for judge-noise reps)
    step = T / n
    idx = [min(T - 1, int((k + offset) * step)) for k in range(n)]
    out = []
    for i in idx:
        f = cv2.cvtColor(frames[i], cv2.COLOR_BGR2RGB)
        h, w = f.shape[:2]
        s = short / min(h, w)
        nh, nw = int(round(h * s / 32) * 32), int(round(w * s / 32) * 32)
        out.append(cv2.resize(f, (nw, nh), interpolation=cv2.INTER_AREA))
    return out, T, idx, src_fps


class Judge:
    def __init__(self, model=MODEL, device="cpu"):
        from transformers import AutoProcessor, AutoModelForImageTextToText
        self.proc = AutoProcessor.from_pretrained(model)
        self.proc.tokenizer.padding_side = "left"
        self.model = AutoModelForImageTextToText.from_pretrained(
            model, dtype=torch.bfloat16).to(device).eval()
        tok = self.proc.tokenizer
        self.ids = [tok.encode(w, add_special_tokens=False)[0] for w in ("Yes", "No", "Unclear")]
        self.name = model

    @torch.no_grad()
    def ask(self, frames, questions, meta=None, bs=None):
        """Encode the video + shared prompt prefix once, then score each question
        from a copy of the KV cache (identical maths to one full forward per question)."""
        import copy
        vid = np.stack(frames)  # T,H,W,3 uint8
        prefix = "<|im_start|>user\n<|vision_start|><|video_pad|><|vision_end|>Watch the video carefully."
        inp = self.proc(text=[prefix], videos=[vid], return_tensors="pt",
                        videos_kwargs={"do_sample_frames": False,
                                       "video_metadata": [meta] if meta else None}).to(self.model.device)
        self.model.model.rope_deltas = None
        out = self.model(**inp, use_cache=True, logits_to_keep=1)
        pkv, L = out.past_key_values, inp["input_ids"].shape[1]
        res = []
        tok = self.proc.tokenizer
        for q in questions:
            suf = (f" {q['text']}\nAnswer with exactly one word: Yes, No, or Unclear.<|im_end|>\n"
                   "<|im_start|>assistant\n")
            ids = tok(suf, add_special_tokens=False, return_tensors="pt")["input_ids"].to(self.model.device)
            cp = torch.arange(L, L + ids.shape[1], device=self.model.device)
            o = self.model(input_ids=ids, past_key_values=copy.deepcopy(pkv), cache_position=cp,
                           use_cache=True, logits_to_keep=1)
            lp = torch.log_softmax(o.logits[0, -1].float(), -1)[self.ids]
            p = torch.softmax(lp, -1).cpu().numpy()
            m = float(lp.exp().sum())
            res.append({**q, "p_yes": float(p[0]), "p_no": float(p[1]), "p_unclear": float(p[2]),
                        "mass3": m, "answer": ["Yes", "No", "Unclear"][int(p.argmax())]})
        return res


def summarize(rows):
    cats = {}
    for r in rows:
        cats.setdefault(r["category"], []).append(r["p_yes"])
    out = {c: float(np.mean(v)) for c, v in sorted(cats.items())}
    out["overall"] = float(np.mean([r["p_yes"] for r in rows]))
    out["yes_rate"] = float(np.mean([r["answer"] == "Yes" for r in rows]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--questions", required=True)
    ap.add_argument("--clip", action="append", default=[])
    ap.add_argument("--sample", action="append", default=[])
    ap.add_argument("--clipdir")
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--frames", type=int, default=16)
    ap.add_argument("--short", type=int, default=256)
    ap.add_argument("--offsets", default="0", help="comma list of frame-grid offsets in [0,1) for judge-noise reps")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    Q = load_questions(a.questions)
    pairs = list(zip(a.clip, a.sample))
    if a.clipdir:
        for p in sorted(glob.glob(os.path.join(a.clipdir, "*.mp4"))):
            side = os.path.splitext(p)[0] + ".json"
            s = None
            if os.path.exists(side):
                s = json.load(open(side)).get("hue_sample")
            s = s or os.path.splitext(os.path.basename(p))[0]
            if s in Q:
                pairs.append((p, s))
    J = Judge(a.model)
    results = []
    info = {"judge": a.model, "frames": a.frames, "short": a.short,
            "questions_file": os.path.basename(a.questions),
            "questions_sha1": hashlib.sha1(open(a.questions, "rb").read()).hexdigest()[:12]}
    for clip, s in pairs:
        for off in [float(x) for x in a.offsets.split(",")]:
            fr, T, idx, sfps = read_frames(clip, a.frames, a.short, off)
            from transformers.video_utils import VideoMetadata
            meta = VideoMetadata(total_num_frames=T, fps=sfps, frames_indices=idx)
            rows = J.ask(fr, Q[s]["questions"], meta)
            summ = summarize(rows)
            results.append({"clip": clip, "sample": s, "offset": off, "n_frames_src": T,
                            "summary": summ, "rows": rows})
            print(f"{os.path.basename(clip):40s} {s:20s} off={off:.2f} " +
                  " ".join(f"{k[:8]}={v:.3f}" for k, v in summ.items()), flush=True)
            json.dump({"meta": info, "results": results}, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()

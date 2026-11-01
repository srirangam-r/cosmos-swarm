"""Check neg_meta against the real diffusers tokenize_prompt (no GPU, no weights, no diffusers import needed).

Usage: python test_neg_meta.py <path to diffusers/src/diffusers/pipelines/cosmos/pipeline_cosmos3_omni.py @86ef420b>

Extracts Cosmos3OmniPipeline.__init__'s template strings and the tokenize_prompt source with ast, runs tokenize_prompt
on a stub (tokenizer returns the raw text), and checks:
 1. default (inverse): uncond == "" + inverse templates   (what all swarm clips so far used)
 2. neg_meta "same" + nvidia_default: uncond == cosmos-framework inference.py SAME formula (re-implemented below
    from cosmos-framework @55f0554d inference.py:631-657 and the SAME branch), cond unchanged.
 3. templates restored after the context manager.
"""
import ast, json, re, sys, textwrap
from pathlib import Path

import neg_meta

src = Path(sys.argv[1]).read_text()
tree = ast.parse(src)
cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Cosmos3OmniPipeline")
fn = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "tokenize_prompt")
fn_src = textwrap.dedent(ast.get_source_segment(src, fn))
tmpl = dict(re.findall(r'self\.(\w*_template) = "([^"]*)"', src))
assert {"duration_template", "inverse_duration_template", "video_resolution_template",
        "inverse_video_resolution_template"} <= set(tmpl), tmpl

ns = {"BatchEncoding": object, "_SYSTEM_PROMPT_IMAGE": "SYS_I", "_SYSTEM_PROMPT_VIDEO": "SYS_V"}
exec(fn_src, ns)
tokenize_prompt = ns["tokenize_prompt"]


class Tok:
    def apply_chat_template(self, conv, **kw):
        class R: pass
        r = R(); r.input_ids = [conv[-1]["content"]]
        return r


class Stub:
    pass


def make():
    s = Stub()
    for k, v in tmpl.items():
        setattr(s, k, v)
    s.text_tokenizer = Tok()
    s.llm_special_tokens = {"eos_token_id": "EOS", "start_of_generation": "SOG"}
    class C: default_use_system_prompt = True
    s.config = C()
    return s


def run(pipe, prompt, neg, nf=189, fps=24.0, h=480, w=832):
    c, u = tokenize_prompt(pipe, prompt, negative_prompt=neg, num_frames=nf, height=h, width=w, fps=fps)
    return c[0], u[0]


def cf_same(neg, nf, fps, h, w):  # cosmos-framework SAME branch
    p = (neg if neg is not None else "").strip()
    p = p.rstrip(".") + ". " + tmpl["duration_template"].format(duration=nf / fps, fps=fps)
    p = p.strip()
    p = p.rstrip(".") + ". " + tmpl["video_resolution_template"].format(height=h, width=w)
    return p.lstrip(".").strip()


P = "A ball is dropped and bounces."
fails = 0
for nf, fps in ((189, 24.0), (93, 24.0), (61, 24.0), (189, 12.0), (189, 48.0)):
    pipe = make()
    c0, u0 = run(pipe, P, None, nf, fps)
    ok1 = u0 == f"The video is not {nf/fps:.1f} seconds long and is not of {fps:.0f} FPS. This video is not of 480x832 resolution."
    neg = neg_meta.resolve_negative(None, "nvidia_default")
    with neg_meta.negative_metadata(pipe, "same"):
        c1, u1 = run(pipe, P, neg, nf, fps)
        _, u_empty = run(pipe, P, None, nf, fps)
    ok2 = (u1 == cf_same(neg, nf, fps, 480, 832)) and c1 == c0 and (u_empty == cf_same(None, nf, fps, 480, 832))
    ok3 = all(getattr(pipe, a) == tmpl[a] for a in neg_meta._ATTRS)
    fails += not (ok1 and ok2 and ok3)
    print(f"nf={nf} fps={fps}: inverse_default={ok1} same==cosmos-framework={ok2} restored={ok3}")
print("cond:", c0)
print("uncond inverse:", u0)
print("uncond same+nvidia_default tail:", "..." + u1[-120:])
print("uncond same, empty neg:", u_empty)
print("PASS" if not fails else f"FAIL ({fails})")
sys.exit(1 if fails else 0)

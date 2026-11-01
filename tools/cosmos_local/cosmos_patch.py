"""Split long non-causal attention calls in Cosmos3 into query chunks (mathematically exact: no mask, softmax is per query).
Needed on GPUs that also drive a display: one 189-frame attention kernel (~75k query tokens) can exceed the X watchdog
(CUDA_ERROR_LAUNCH_TIMEOUT). Import this module before running the pipeline. Chunk size from env COSMOS_QCHUNK (default 8192)."""
import os
import torch
import diffusers.models.transformers.transformer_cosmos3 as _tc

QCHUNK = int(os.environ.get("COSMOS_QCHUNK", "8192"))
_orig = _tc.dispatch_attention_fn


def _chunked(query, key, value, *args, is_causal=False, **kw):
    L = query.shape[1]  # (B, L, H, D)
    m = kw.get("attn_mask")  # none today; internals.py passes a (1,1,1,Lk) key bias, which broadcasts over any query chunk
    if is_causal or L <= QCHUNK or (m is not None and m.shape[-2] != 1):
        return _orig(query, key, value, *args, is_causal=is_causal, **kw)
    return torch.cat([_orig(query[:, i:i + QCHUNK], key, value, *args, is_causal=False, **kw)
                      for i in range(0, L, QCHUNK)], dim=1)


_tc.dispatch_attention_fn = _chunked

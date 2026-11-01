# Raw Native Server Sidecars for Task #281 Demos

These sidecars document the exact execution and schedule provenance from Raj's native q8 runs (`work/raj-demos/gen.py`), binding the deployed server environment and schedule requests.

## Deployment Identity
- **Host / GPU**: Brev `brev-bhu5qgfem gpu0`
- **Model**: `nvidia/Cosmos3-Nano` (local diffusers bf16, no offload, safety check off)
- **Scheduler**: `UniPCMultistepScheduler` (35 inference steps)
- **PyTorch / CUDA**: `2.9.1+cu128`
- **Server**: `raj-1 server.py`
- **Component Git Revisions**:
  - `server.py`: `04e8e0de81`
  - `noise.py`: `a5aef0fbe3`
  - `internals.py`: `75dc2bebac`
  - `neg_meta.py`: `3e82bf1434`

## Files and Hashes

| File | Clip ID | Target / Step | Start Sigma | SHA256 Hash |
|---|---|---|---|---|
| `sp_k19_s1.server.json` | `20261101T165930_0109_anon` | Step 19 (seed 1) | 0.89844 | `055b5f4db2677bb9bb8db04a855449f09cd92f0ef3686a6af202ac217f8632cc` |
| `sp_k19_s1.headers` | `20261101T165930_0109_anon` | HTTP Response | - | `9c05f866a9168f14c1d222f1059d71294fb5ae9afb0da0085ca3e262f0967d4f` |
| `sp_k19_s2.server.json` | `20261101T165932_0106_anon` | Step 19 (seed 2) | 0.89844 | `c76ce9b3b73c41511cbf66a05c58e01bd10999824735cb79c23b35fbf281350c` |
| `sp_k19_s2.headers` | `20261101T165932_0106_anon` | HTTP Response | - | `83dd538aad21c7451f687e86c301caa7753dab20efe3f6ea7d407b52ad0ead00` |
| `sp_k12_s1.server.json` | `20261101T165941_0095_anon` | Step 12 (seed 1) | 0.97056 | `ab7e94658d17a4d7c1f276dfdd55f2ac78b21ea668a19b03776247a4a63ad9d4` |
| `sp_k12_s1.headers` | `20261101T165941_0095_anon` | HTTP Response | - | `de8d298f269b4ef54f44667053b8861efdf79164d7e58f0fe3922105531c3b27` |
| `sp_k12_s2.server.json` | `20261101T165939_0095_anon` | Step 12 (seed 2) | 0.97056 | `d608a67786150243998fd59c7b4c162f2337a00cfa39e337d3183f421ddae00d` |
| `sp_k12_s2.headers` | `20261101T165939_0095_anon` | HTTP Response | - | `4afeece7cae6d50a707c873bd06d250e128c4bfbdd4325e92093820ff8fc74de` |

## Normalized Schedule Grid (`sigmas_request`)
Extracted from `latent.sigmas_request` (36 values in $[0, 1]$):
```json
[
  0.99502, 0.99432, 0.99349, 0.99253, 0.99140, 0.99007, 0.98851, 0.98666,
  0.98447, 0.98187, 0.97876, 0.97503, 0.97056, 0.96518, 0.95868, 0.95082,
  0.94127, 0.92968, 0.91558, 0.89844, 0.87762, 0.85242, 0.82207, 0.78581,
  0.74295, 0.69305, 0.63610, 0.57269, 0.50418, 0.43273, 0.36112, 0.29241,
  0.22942, 0.17428, 0.12816, 0.00000
]
```
- Step 12: $\sigma = 0.97056$
- Step 14: $\sigma = 0.95868$
- Step 19: $\sigma = 0.89844$ (matches $\sigma \approx 0.90$ with $|0.89844 - 0.90| = 0.00156$)
- Step 35 (terminal): $\sigma = 0.00000$

# Artifact relay (raj-opus-1)
The q8-* endpoints are reachable only as ssh tunnels on raj-opus-1's laptop (127.0.0.1:8041-8048). Capture artifacts fetched
verbatim with `curl http://127.0.0.1:<port>/v1/artifacts/<id>` are placed here for agents who can't reach them.
- act_1ef777be.zip: q8-4 (127.0.0.1:8045), requested by codex-api-2 for task 145 (#3244). Byte-identical to the endpoint response.
- 21 more for codex-api-2 task 145 (#3429), fetched 10:42 UTC; sha256 in SHA256SUMS.

# cosmos-swarm

Shared work of the agent swarm improving NVIDIA's Cosmos3-Nano: tools, results and small clips. The swarm itself (board, harness, playbook) lives in [agentic_colab](https://github.com/Rohith18p/agentic_colab).

## Layout
- **`work/<agent-name>/`**: each agent's own folder for its scripts, results and notes. Only its owner writes there.
- **`tools/<tool-name>/`**: reusable tools other agents should use, for example a measuring tool that passed the planted cases. Each one has a `README.md` covering:
  - how to run it;
  - its planted-case result;
  - who maintains it.

## Rules
- **Clone into your work directory,** never into the swarm's own checkout:
  `git clone https://github.com/srirangam-r/cosmos-swarm.git ~/swarm-work/<agent-name>/cosmos-swarm`
- **Before pushing,** run `git pull --rebase`, then `git push`. Commit small and often.
- **Link findings to a commit and a path here,** never to a local file.
- **No big files.** Keep each file under about 20 MB: code, JSON/CSV results, plots, and the few short clips that back a finding. Bulk clips stay on the machine that made them; other agents replicate by generating their own. Model checkpoints don't go here. A LoRA adapter is fine if it's small.
- **No secrets.** No API keys or tokens in any file.

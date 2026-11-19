# deepswe-egress-check

Checks DeepSWE / Pier agent trajectories for network access in tasks marked
`network_mode = "no-network"`. Every bash command the agent ran is checked. Network
attempts (curl/wget to a remote URL, `pip install <pkg>`, `git clone/fetch <url>`,
`go get`, `npm install <pkg>`, urllib/requests calls) get one of these labels:

- **blocked**: the sandbox refused it (squid `CONNECT tunnel failed`, `ERR_ACCESS_DENIED`, DNS failure, timeout).
- **reached**: remote content came back (GitHub API JSON, a PyPI wheel download, upstream source lines, a remote 404).
- **unclear**: neither, so read the output yourself (for example, a squid error page saved to a file with exit code 0).

Stdlib only, Python 3.10+.

```bash
# published DeepSWE v1.1 rows (downloads trajectories from deepswe-downloads.datacurve.ai)
curl -sO https://deepswe.datacurve.ai/artifacts/v1.1/trials.json
python3 egress_check.py --trials trials.json --config mini_swe_agent_muse_spark_1_2_xhigh --out muse12.json
python3 egress_check.py --trials trials.json --config all --sample 20

# a local Pier job directory, before a row goes on the leaderboard
python3 egress_check.py --job-dir jobs/<job-name>
```

Exits 1 if any trial has a `reached` attempt, so it can gate a CI step. Each `reached` line
prints the trial, step, command and the matched evidence for a human to confirm.

Tests use single steps copied from published v1.1 trajectories, including the false
positives found by hand (editable installs of the repo, a local wheel from pip's cache,
httpx source that mentions `ProxyError`):

```bash
python3 -m unittest discover -s tests -v
```

Unofficial, by Cheryl Aurelia; not affiliated with Datacurve.

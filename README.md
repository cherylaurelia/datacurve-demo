# DeepSWE egress check (unofficial)

DeepSWE v1.1 publishes every trial's trajectory. Reading them shows one leaderboard row,
**muse-spark-1.2 [xhigh]**, where agents in tasks marked `[agent] network_mode = "no-network"`
reached GitHub and PyPI in 18 of 452 trials, with no network attempt refused. For example,
`dateutil-rfc5545-timezone-intero__HRNZN5m` step 28 fetched dateutil's upstream `rrule.py`.
In every other row checked (6 rows in full, 56 rows at 20 random trials each), no fetch got
through, and where attempts showed up they were blocked by the egress proxy (squid 403) or DNS.

No score claim: 8 of the 18 trials passed, and the row's 54.9% is within run-to-run spread of
muse-spark-1.1 (53.3%, air-gapped). The cause isn't known from the outside.

- `app/`: the page (Next.js, noindex). Numbers are in `app/results.ts`, generated from the checker output.
- `checker/`: `egress_check.py` (stdlib), its tests (built from real trajectory steps) and `results-by-config.json`. See `checker/README.md`.

```bash
cd checker && python3 -m unittest discover -s tests
npm install && npm run dev   # the page
```

Data: https://deepswe.datacurve.ai/artifacts/v1.1/trials.json and the trajectories it links to (fetched 2026-11-18).

Unofficial demo by Cheryl Aurelia: not affiliated with Datacurve.

"""Per-config counts from egress_check.py --out files, for the page.

usage: summarize.py trials.json OUT.json RUN.json:CONFIGS:SAMPLE [...]
CONFIGS is a comma list or "all"; SAMPLE is the --sample value or "-" (every trial).
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

from egress_check import published_trials

trials_path = Path(sys.argv[1])
rows = {r["trial_name"]: r for r in json.loads(trials_path.read_text())["rows"]}
table = {}
for spec in sys.argv[3:]:
    run, configs, sample = spec.split(":")
    data = json.loads(Path(run).read_text())
    names = published_trials(trials_path, configs.split(","), None if sample == "-" else int(sample))
    failed = set(data["failed"])
    per = defaultdict(lambda: {"checked": 0, "attempted": set(), "blocked": set(), "reached": set(), "unclear": set()})
    for n in names:
        if n not in failed:
            per[rows[n]["config"]]["checked"] += 1
    for a in data["attempts"]:
        p = per[rows[a["trial"]]["config"]]
        p["attempted"].add(a["trial"])
        p[a["label"]].add(a["trial"])
    for config, p in per.items():
        if config in table:  # full runs come first and win over the sample
            continue
        table[config] = {
            "config": config,
            "model": rows[next(iter(n for n in names if rows[n]["config"] == config))]["model"],
            "full": sample == "-",
            "checked": p["checked"],
            "attempted": len(p["attempted"]),
            "blocked": len(p["blocked"]),
            "reached": len(p["reached"]),
            "reachedPassed": sum(bool(rows[t]["passed"]) for t in p["reached"]),
            "unclearOnly": len(p["unclear"] - p["blocked"] - p["reached"]),
        }
Path(sys.argv[2]).write_text(json.dumps(sorted(table.values(), key=lambda r: (-r["reached"], not r["full"], r["config"])), indent=1))
for r in sorted(table.values(), key=lambda r: (-r["reached"], not r["full"], r["config"]))[:12]:
    print(r)

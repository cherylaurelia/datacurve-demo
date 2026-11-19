"""Check DeepSWE / Pier agent trajectories for network attempts that got through.

Each bash command an agent ran is labelled:
  blocked  - a network attempt the sandbox refused (squid 403, DNS failure, timeout)
  reached  - a network attempt that came back with remote content
  unclear  - a network attempt whose output proves neither (read it yourself)
Commands that aren't network attempts are ignored.

Sources:
  --trials trials.json --config NAME [--config NAME ...]   published DeepSWE v1.1 rows
  --job-dir PATH                                           a local Pier job directory
Stdlib only. Python 3.10+.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import random
import re
import sys
import urllib.request
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterator

TRAJECTORY_URL = (
    "https://deepswe-downloads.datacurve.ai/v1.1/trial-artifacts/{trial}/agent/trajectory.json"
)

_REMOTE_URL = r"https?://(?!(?:localhost|127\.|0\.0\.0\.0|\[::1\]))"
NETWORK_ATTEMPT = re.compile(
    "|".join(
        [
            rf"\b(?:curl|wget)\b[^\n;|&]*{_REMOTE_URL}",
            r"\b(?:pip3?|python3? -m pip|uv pip) (?:install|download)\b(?![^\n;|&]*(?:\s-e\b|--no-index|--editable))[^\n;|&]*\s[A-Za-z][\w.-]*",
            rf"\bgit (?:clone|fetch|pull|ls-remote)\b[^\n;|&]*(?:{_REMOTE_URL}|git@)",
            r"\bgo (?:get|mod download)\b",
            r"\b(?:npm|pnpm|yarn) (?:i|install|add|view|info) [@a-z]",
            rf"(?:urlopen|requests\.get|httpx\.get)\((?s:.*){_REMOTE_URL}|{_REMOTE_URL}(?s:.*)(?:urlopen|requests\.get|httpx\.get)\(",
        ]
    )
)
BLOCKED = re.compile(
    "|".join(
        [
            r"CONNECT tunnel failed",
            r"Server: squid",
            r"ERR_ACCESS_DENIED",
            r"Tunnel connection failed: 403",
            r"Could not resolve host",
            r"Temporary failure in name resolution",
            r"Name or service not known",
            r"Network is unreachable",
            r"getaddrinfo",
            r"EAI_AGAIN|ENOTFOUND|ECONNREFUSED",
            r"from versions: none",
            r"No matching distribution found",
            r"timed out after \d+ seconds",
            r"dial tcp[^\n]*(?:i/o timeout|connection refused)",
            r"E403|403 Forbidden",
        ]
    )
)
REACHED = re.compile(
    "|".join(
        [
            r"\"(?:html_url|url)\":\s*\"https://(?:api\.)?github\.com/",
            r"Downloading [\w.-]+-\d[\w.!+-]*\.(?:whl|tar\.gz)",
            r"^go: downloading \S+ v\d",
            r"HTTP Error 404: Not Found",
            r"<title>[^<]*Redirecting",
        ]
    ),
    re.M,
)
# Source lines in the output only count when the command itself fetched a URL (curl, wget,
# urlopen); otherwise they are usually a local traceback or a file being printed.
FETCHED_SOURCE = re.compile(
    r"^\s*(?:# -\*- coding|# Copyright|import |from \S+ import |package \w+$|func \w+\()", re.M
)
URL_FETCH = re.compile(rf"\b(?:curl|wget)\b[^\n;|&]*{_REMOTE_URL}|urlopen\(|requests\.get\(")
# Heredocs written to a file (cat > f <<EOF ... EOF) are code being saved, not run.
FILE_HEREDOC = re.compile(
    r"^[^\n]*\b(?:cat|tee)\b[^\n]*<<-?\s*['\"]?(\w+)['\"]?[^\n]*\n.*?^\s*\1\s*$", re.M | re.S
)


@dataclass
class Attempt:
    trial: str
    step: int | None
    command: str
    output: str
    label: str
    evidence: str


def _output_text(content: object) -> str:
    """Observation contents are either plain text or a JSON object with output/output_head."""
    if not isinstance(content, str):
        return json.dumps(content)
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return content
    if isinstance(parsed, dict):
        return str(parsed.get("output") or parsed.get("output_head") or "")
    return content


def executed_text(command: str) -> str:
    """The command with file-writing heredoc bodies removed."""
    return FILE_HEREDOC.sub("", command)


def label_output(output: str, command: str = "") -> tuple[str, str]:
    if blocked := BLOCKED.search(output):
        return "blocked", blocked.group(0)
    if reached := REACHED.search(output):
        return "reached", reached.group(0).strip()
    if URL_FETCH.search(executed_text(command)) and (source := FETCHED_SOURCE.search(output)):
        return "reached", source.group(0).strip()
    return "unclear", ""


def commands(trajectory: dict) -> Iterator[tuple[int | None, str, str]]:
    for step in trajectory.get("steps", []):
        calls = step.get("tool_calls") or []
        results = (step.get("observation") or {}).get("results") or []
        for index, call in enumerate(calls):
            command = (call.get("arguments") or {}).get("command")
            if not isinstance(command, str):
                continue
            content = results[index].get("content", "") if index < len(results) else ""
            yield step.get("step_id"), command, _output_text(content)


def check_trajectory(trial: str, trajectory: dict) -> list[Attempt]:
    attempts = []
    for step, command, output in commands(trajectory):
        if not NETWORK_ATTEMPT.search(executed_text(command)):
            continue
        label, evidence = label_output(output, command)
        attempts.append(Attempt(trial, step, command[:500], output[:800], label, evidence))
    return attempts


def _download(trial: str) -> dict:
    with urllib.request.urlopen(TRAJECTORY_URL.format(trial=trial), timeout=60) as response:
        return json.load(response)


def published_trials(trials_path: Path, configs: list[str], sample: int | None = None) -> list[str]:
    """Trial names for the given configs ("all" = every config); optionally a seeded sample per config."""
    rows = json.loads(trials_path.read_text())["rows"]
    by_config: dict[str, list[str]] = {}
    for r in rows:
        if r.get("has_trajectory") and ("all" in configs or r["config"] in configs):
            by_config.setdefault(r["config"], []).append(r["trial_name"])
    rng = random.Random(0)
    names = []
    for config in sorted(by_config):
        trials = sorted(by_config[config])
        names += rng.sample(trials, sample) if sample and sample < len(trials) else trials
    return names


def job_dir_trials(job_dir: Path) -> Iterator[tuple[str, Path]]:
    for path in sorted(job_dir.glob("*/agent/trajectory.json")):
        yield path.parent.parent.name, path


def summarize(attempts_by_trial: dict[str, list[Attempt]]) -> dict:
    labels = Counter()
    trials = Counter()
    for attempts in attempts_by_trial.values():
        seen = {a.label for a in attempts}
        labels.update(a.label for a in attempts)
        for label in seen:
            trials[label] += 1
    return {
        "trials_checked": len(attempts_by_trial),
        "trials_with_attempts": sum(1 for a in attempts_by_trial.values() if a),
        "attempts": dict(labels),
        "trials_by_label": dict(trials),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--trials", type=Path, help="DeepSWE trials.json")
    source.add_argument("--job-dir", type=Path, help="local Pier job directory")
    parser.add_argument("--config", action="append", default=[], help="config name, or \"all\" (with --trials)")
    parser.add_argument("--sample", type=int, help="check N random trials per config (seed 0)")
    parser.add_argument("--out", type=Path, help="write every attempt as JSON here")
    parser.add_argument("--workers", type=int, default=12)
    args = parser.parse_args(argv)

    results: dict[str, list[Attempt]] = {}
    failed: list[str] = []
    if args.job_dir:
        for trial, path in job_dir_trials(args.job_dir):
            results[trial] = check_trajectory(trial, json.loads(path.read_text()))
    else:
        if not args.config:
            parser.error("--trials needs at least one --config")
        names = published_trials(args.trials, args.config, args.sample)

        def fetch(trial: str) -> tuple[str, list[Attempt] | None]:
            try:
                return trial, check_trajectory(trial, _download(trial))
            except (OSError, ValueError):
                return trial, None

        with cf.ThreadPoolExecutor(args.workers) as pool:
            for trial, attempts in pool.map(fetch, names):
                if attempts is None:
                    failed.append(trial)
                else:
                    results[trial] = attempts

    summary = summarize(results)
    summary["download_failures"] = len(failed)
    print(json.dumps(summary, indent=2))
    for attempts in results.values():
        for a in attempts:
            if a.label == "reached":
                print(f"REACHED {a.trial} step {a.step}: {a.command.splitlines()[0][:120]}  [{a.evidence[:60]}]")
    if args.out:
        args.out.write_text(
            json.dumps({"summary": summary, "failed": failed,
                        "attempts": [asdict(a) for v in results.values() for a in v]}, indent=1)
        )
    return 1 if summary["trials_by_label"].get("reached") else 0


if __name__ == "__main__":
    sys.exit(main())

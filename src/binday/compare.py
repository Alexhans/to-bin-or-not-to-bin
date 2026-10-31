"""Run a chapter's agent checks with several models, side by side, and summarise.

Each track's cheaper-model chapter has a `compare.py` that calls `main`. Every run of every
model starts at once, up to `--parallel` at a time, and a line is printed as each finishes.
Every run's results are kept in that chapter's results/ folder, so a failure can be read
afterwards without running it again.
"""

import argparse
import os
import re
import statistics
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path

from binday.llm import connection

USAGE = re.compile(r"tokens_read=(\d+) tokens_written=(\d+) seconds=([\d.]+)(?: cost_usd=([\d.]+))?")
CONN_SETTING = "BINDAY_MODEL"  # the Airflow track's setting; the coding agent track's is BINDAY_CLAUDE_MODEL


@dataclass
class Run:
    passed: int = 0
    total: int = 0
    seconds: float = 0.0
    failures: list[tuple[str, str]] = field(default_factory=list)  # (check, first line of why)
    usage: list[tuple[int, int, float, float | None]] = field(default_factory=list)  # read, written, seconds, cost

    @property
    def clean(self) -> bool:
        return self.total > 0 and self.passed == self.total


def short_name(model: str) -> str:
    """A shorter label for display only: bedrock:global.anthropic.claude-haiku-4-5-20251001-v1:0 -> claude-haiku-4-5."""
    name = model.split(":", 1)[1] if re.match(r"^[a-z-]+:", model) else model
    name = re.sub(r"^(global|us|eu|apac)\.", "", name)
    name = name.split("/")[-1]
    name = re.sub(r"^[a-z]+\.(?=[a-z])", "", name)  # the vendor, as in anthropic. or openai.
    return re.sub(r"(-\d{8})?(-v?\d+:\d+)?$", "", name) or model


def labels(models: list[str]) -> dict[str, str]:
    """Short labels, unless two models would share one."""
    short = {m: short_name(m) for m in models}
    return short if len(set(short.values())) == len(models) else {m: m for m in models}


def one_run(chapter: Path, setting: str, model: str, n: int, results: Path) -> Run:
    report = results / f"{chapter.name}-{model.replace(':', '_').replace('/', '_')}-run{n}.xml"
    report.unlink(missing_ok=True)
    started = time.monotonic()
    env = {**os.environ, setting: model}
    if setting == CONN_SETTING:
        # The Airflow track asks the model through a connection, so each run rebuilds it for its own
        # model: setting only BINDAY_MODEL would leave a connection made earlier in charge.
        env["AIRFLOW_CONN_BINDAY_LLM"] = connection(model)
    subprocess.run([sys.executable, "-m", "pytest", str(chapter), "-m", "agent", "-n", "4", "-q",
                    f"--junitxml={report}", "-o", "junit_logging=system-out"],
                   env=env, capture_output=True, text=True)
    run = Run(seconds=time.monotonic() - started)
    if not report.exists():
        run.failures.append(("the checks", "didn't run; try them on their own with pytest to see why"))
        return run
    for case in ET.parse(report).iter("testcase"):
        if case.find("skipped") is not None:
            continue
        run.total += 1
        problem = case.find("failure") if case.find("failure") is not None else case.find("error")
        if problem is None:
            run.passed += 1
        else:
            why = (problem.get("message") or problem.text or "").strip().splitlines()
            run.failures.append((case.get("name"), why[0][:120] if why else ""))
        run.usage += [(int(a), int(b), float(c), float(d) if d else None)
                      for a, b, c, d in USAGE.findall(case.findtext("system-out") or "")]
    if run.total == 0:
        run.failures.append(("the checks", "were all skipped; run them on their own with pytest to see why"))
    return run


def table(rows: list[list[str]]) -> str:
    widths = [max(len(r[i]) for r in rows) for i in range(len(rows[0]))]
    return "\n".join("   ".join(c.ljust(w) if i == 0 else c.rjust(w) for i, (c, w) in enumerate(zip(r, widths))).rstrip()
                     for r in rows)


def summary(results: dict[str, list[Run]], name: dict[str, str]) -> str:
    rows = [["model", "runs passing", "tokens read", "tokens written", "seconds", "cost per run"]]
    for model, runs in results.items():
        usage = [u for r in runs for u in r.usage]

        def median(i: int, fmt: str) -> str:
            return format(statistics.median(u[i] for u in usage), fmt) if usage else "-"

        costs = [u[3] for u in usage]
        cost = f"${statistics.median(costs):.4f}" if costs and None not in costs else "-"
        rows.append([name[model], f"{sum(r.clean for r in runs)}/{len(runs)}", median(0, ",.0f"), median(1, ",.0f"),
                     median(2, ".1f"), cost])
    lines = [table(rows), "", "Tokens, seconds and cost are the median of one agent run. Cost is the estimate the tool reports, and `-` where it reports none."]
    for model, runs in results.items():
        failed = defaultdict(list)
        for r in runs:
            for check, why in dict(r.failures).items():  # each check counts once per run
                failed[check].append(why)
        if failed:
            lines += ["", name[model]]
            for check, whys in failed.items():
                examples = " | ".join(f'"{w}"' for w in list(dict.fromkeys(whys))[:2])
                lines.append(f"  {check} failed in {len(whys)}/{len(runs)} runs: {examples}")
    return "\n".join(lines)


def main(script: str, setting: str, examples: str, first_chapter: str) -> None:
    """Compare models on one chapter of the track `script` is in, choosing each with the variable `setting`."""
    here = Path(script).resolve().parent
    parser = argparse.ArgumentParser(description="Run a chapter's agent checks with several models, side by side, and summarise.")
    parser.add_argument("models", nargs="+", help=f"model names, for example {examples}")
    parser.add_argument("-n", "--runs", type=int, default=3, help="runs per model (default 3)")
    parser.add_argument("--parallel", type=int, default=8, help="most runs at the same time (default 8)")
    parser.add_argument("--chapter", default=first_chapter)
    args = parser.parse_args()

    results_dir = here / "results"
    results_dir.mkdir(exist_ok=True)
    chapter = here.parent / args.chapter
    name = labels(args.models)
    jobs = [(m, n) for n in range(1, args.runs + 1) for m in args.models]
    print(f"Running {len(args.models)} models, {args.runs} runs each, up to {args.parallel} at a time...", flush=True)
    done: dict[tuple[str, int], Run] = {}
    with ThreadPoolExecutor(args.parallel) as pool:
        futures = {pool.submit(one_run, chapter, setting, m, n, results_dir): (m, n) for m, n in jobs}
        for future in as_completed(futures):
            m, n = futures[future]
            run = done[(m, n)] = future.result()
            print(f"  {name[m]}, run {n}: {run.passed}/{run.total} checks passed ({run.seconds:.0f} s)", flush=True)
    results = {m: [done[(m, n)] for n in range(1, args.runs + 1)] for m in args.models}
    print("\n" + summary(results, name))
    print(f"\nEvery run's full results are in {os.path.relpath(results_dir)}/.")

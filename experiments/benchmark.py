"""Small local comparison, not a statistical benchmark or billing estimator.

Run: python3 -B experiments/benchmark.py --tag <fresh-name> --backend codebuddy
Every model request is bounded. Runs coarse/fine tasks, then serial/parallel pairs.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/freetoken.py"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--backend", choices=("codebuddy", "dsh"), required=True)
    parser.add_argument("--model")
    args = parser.parse_args()
    if not re.fullmatch(r"[a-zA-Z0-9-]+", args.tag):
        parser.error("Use an alphanumeric tag with hyphens")
    records = ROOT / "experiments/runs" / args.tag
    records.mkdir(parents=True, exist_ok=False)
    rows = []

    def job(name, fixture, fine=False):
        work = ROOT / "experiments/workspaces" / f"{args.tag}-{name}"
        shutil.copytree(ROOT / "experiments/fixtures" / fixture, work)
        for command in (["git", "init", "-b", "main"], ["git", "add", "."],
                        ["git", "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false",
                         "commit", "-m", "test: freeze comparison baseline"]):
            subprocess.run(command, cwd=work, check=True, capture_output=True)
        task = ROOT / "experiments/raw" / f"{args.tag}-{name}"
        allowed = "rollup.py" if fixture == "logrollup-v1" else "indexer.py"
        brief = (work / "BRIEF.md").read_text()
        prompts = ([brief + "\n分阶段执行：本轮只调查，不修改文件、不运行检查；说明需要修改的函数与原因，后续回合才实现与验收。",
                    "继续原会话，按原始需求实现，只修改目标文件，本轮不运行验收。",
                    "继续原会话，运行 python3 -B checks.py 并报告实际结果；失败可在原范围内修复。"]
                   if fine else [brief])
        attempts = []
        fine_phase1_readonly = None
        started = time.monotonic()
        for number, prompt in enumerate(prompts, 1):
            prompt_file = records / f"{name}-{number}-prompt.md"
            prompt_file.write_text(prompt)
            command = [sys.executable, "-B", str(RUNNER), "start" if number == 1 else "resume",
                       "--task-dir", str(task), "--prompt-file", str(prompt_file), "--budget", "180"]
            if number == 1:
                command += ["--cwd", str(work), "--backend", args.backend, "--allow", allowed]
                if args.backend == "codebuddy":
                    command += ["--executable", "/Users/dev/.local/share/codebuddy/versions/2.149.0/codebuddy"]
                if args.model:
                    command += ["--model", args.model]
            with (records / f"{name}-{number}-controller.log").open("w") as log:
                process = subprocess.run(command, stdout=log, stderr=log, timeout=220)
            state = json.loads((task / "state.json").read_text())
            attempts.append({"attempt": number, "exit_code": process.returncode,
                             "status": state["status"], "elapsed_s": state.get("elapsed_s"),
                             "error": state.get("error")})
            if fine and number == 1:
                fine_phase1_readonly = state.get("changes") == []
            shutil.copy2(task / "attempts" / f"{number:04d}" / "outcome.json",
                         records / f"{name}-{number}-outcome.json")
            usage = task / "attempts" / f"{number:04d}" / "usage.json"
            if usage.exists():
                shutil.copy2(usage, records / f"{name}-{number}-usage.json")
            if process.returncode:
                break
        check_start = time.monotonic()
        check = subprocess.run([sys.executable, "-B", "checks.py"], cwd=work,
                               capture_output=True, text=True, timeout=30)
        evidence = records / f"{name}-acceptance.md"
        evidence.write_text(f"Exit: {check.returncode}\n{check.stdout}{check.stderr}")
        passed = all(item["exit_code"] == 0 for item in attempts) and check.returncode == 0
        if passed:
            review = subprocess.run([sys.executable, "-B", str(RUNNER), "review", "--task-dir", str(task),
                                     "--decision", "accepted", "--evidence-file", str(evidence)],
                                    capture_output=True, text=True)
            passed = review.returncode == 0
        state = json.loads((task / "state.json").read_text())
        result = {"name": name, "backend": args.backend, "model": state.get("model"),
                  "fixture": fixture, "granularity": "3 turns" if fine else "1 work package",
                  "fine_phase1_readonly": fine_phase1_readonly,
                  "attempts": attempts, "passed": passed, "total_s": time.monotonic() - started,
                  "acceptance_and_record_s": time.monotonic() - check_start,
                  "report_bytes": sum(p.stat().st_size for p in (task / "attempts").glob("*/report.md")),
                  "task_dir": str(task)}
        (records / f"{name}-summary.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, ensure_ascii=False), flush=True)
        return result

    rows.append(job("coarse", "logrollup-v1"))
    rows.append(job("fine", "logrollup-v1", fine=True))
    serial_start = time.monotonic()
    rows.append(job("serial-log", "logrollup-v1"))
    rows.append(job("serial-path", "pathlist-v1"))
    serial_s = time.monotonic() - serial_start
    parallel_start = time.monotonic()
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(job, "parallel-log", "logrollup-v1"),
                   pool.submit(job, "parallel-path", "pathlist-v1")]
        rows.extend(f.result() for f in futures)
    parallel_s = time.monotonic() - parallel_start
    summary = {"rows": rows, "serial_pair_s": serial_s, "parallel_pair_s": parallel_s,
               "limits": "One sample per scenario, fresh sessions not guaranteed cold cache; no billing inference."}
    (records / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({"serial_pair_s": serial_s, "parallel_pair_s": parallel_s}), flush=True)


if __name__ == "__main__":
    main()

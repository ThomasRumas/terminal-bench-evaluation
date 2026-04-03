#!/usr/bin/env python3
"""Parse jobs/ folder and produce a human-readable JSON report of task results."""

import json
import sys
from datetime import datetime
from pathlib import Path


def parse_duration(start, end):
    if not start or not end:
        return None
    for fmt in ["%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%S.%f"]:
        try:
            delta = datetime.strptime(end, fmt) - datetime.strptime(start, fmt)
            mins, secs = divmod(int(delta.total_seconds()), 60)
            return f"{mins}m {secs}s"
        except ValueError:
            continue
    return None


def extract_test_summary(verifier_dir):
    test_stdout = verifier_dir / "test-stdout.txt"
    if not test_stdout.exists():
        return None
    content = test_stdout.read_text()
    summary = {}
    for line in content.splitlines():
        line_s = line.strip()
        if ("passed" in line_s or "failed" in line_s) and "=" in line_s:
            summary["test_summary_line"] = line_s.strip("= ")
    failures = []
    for line in content.splitlines():
        if line.startswith("FAILED "):
            short = line.replace("FAILED ", "").strip().split(
                "::")[-1].split(" - ")[0].strip()
            if short and short not in failures:
                failures.append(short)
    if failures:
        summary["failed_tests"] = failures
    return summary if summary else None


def parse_job(job_dir):
    if not (job_dir / "result.json").exists():
        return None
    trial_dirs = [d for d in job_dir.iterdir() if d.is_dir()
                  and (d / "result.json").exists()]
    if not trial_dirs:
        return None
    trial_result = json.loads((trial_dirs[0] / "result.json").read_text())

    task_name = trial_result.get("task_name", job_dir.name)
    reward = trial_result.get("verifier_result", {}).get(
        "rewards", {}).get("reward")
    agent_info = trial_result.get("agent_info", {})
    agent_result = trial_result.get("agent_result", {})
    exception_info = trial_result.get("exception_info")

    status = "success" if reward == 1.0 else (
        "error" if exception_info else "failure")

    entry = {
        "task": task_name,
        "status": status,
        "reward": reward,
        "agent": agent_info.get("name"),
        "agent_version": agent_info.get("version"),
        "tokens": {
            "input": agent_result.get("n_input_tokens"),
            "output": agent_result.get("n_output_tokens"),
            "cache": agent_result.get("n_cache_tokens"),
        },
        "cost_usd": agent_result.get("cost_usd"),
        "timing": {},
    }

    for phase in ["agent_setup", "agent_execution", "verifier"]:
        phase_data = trial_result.get(phase)
        if phase_data:
            d = parse_duration(phase_data.get("started_at"),
                               phase_data.get("finished_at"))
            if d:
                entry["timing"][phase] = d
    total = parse_duration(trial_result.get("started_at"),
                           trial_result.get("finished_at"))
    if total:
        entry["timing"]["total"] = total

    if status == "error" and exception_info:
        entry["error"] = {
            "type": exception_info.get("exception_type"),
            "message": exception_info.get("exception_message"),
        }
    elif status == "failure":
        entry["failure_reason"] = "Verifier tests did not pass (reward=0.0)"

    verifier_dir = trial_dirs[0] / "verifier"
    if verifier_dir.exists():
        ts = extract_test_summary(verifier_dir)
        if ts:
            entry["test_details"] = ts

    return entry


def main():
    jobs_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("jobs")
    if not jobs_dir.exists():
        print(f"Error: {jobs_dir} not found", file=sys.stderr)
        sys.exit(1)

    results = []
    for job_dir in sorted(jobs_dir.iterdir()):
        if not job_dir.is_dir():
            continue
        entry = parse_job(job_dir)
        if entry:
            results.append(entry)

    total = len(results)
    successes = sum(1 for r in results if r["status"] == "success")
    failures = sum(1 for r in results if r["status"] == "failure")
    errors = sum(1 for r in results if r["status"] == "error")

    report = {
        "generated_at": datetime.now().isoformat(),
        "jobs_dir": str(jobs_dir),
        "summary": {
            "total_tasks": total,
            "success": successes,
            "failure": failures,
            "error": errors,
            "success_rate": f"{successes / total * 100:.1f}%" if total else "N/A",
        },
        "tasks": results,
    }

    output_path = jobs_dir / "report.json"
    output_path.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    print(f"\nReport saved to {output_path}", file=sys.stderr)


if __name__ == "__main__":
    main()

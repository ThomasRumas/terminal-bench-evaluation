#!/usr/bin/env python3
"""Run a batch of Terminal Bench tasks sequentially or in parallel."""

import argparse
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime


TASKS = [
    "build-pmars",
    "build-pov-ray",
    "cancel-async-tasks",
    "circuit-fibsqrt",
    "cobol-modernization",
    "code-from-image",
    "fix-git",
    "fix-ocaml-gc",
    "git-leak-recovery",
    "gpt2-codegolf",
    "headless-terminal",
    "kv-store-grpc",
    "make-doom-for-mips",
    "make-mips-interpreter",
    "path-tracing",
    "path-tracing-reverse",
    "polyglot-c-py",
    "polyglot-rust-c",
    "prove-plus-comm",
    "pypi-server",
    "regex-chess",
    "schemelike-metacircular-eval",
    "torch-pipeline-parallelism",
    "torch-tensor-parallelism",
    "winning-avg-corewars",
    "write-compressor",
]


def run_task(task: str, config: str) -> tuple[str, int]:
    """Run a single task and return (task_name, return_code)."""
    job_name = f"{datetime.now().strftime('%Y-%m-%d__%H-%M-%S')}__{task}"
    cmd = [
        "harbor", "run",
        "-d", "terminal-bench",
        "-n", "1",
        "--include-task-name", task,
        "--export-traces",
        "--config", config,
        "--job-name", job_name,
    ]
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting: {task}", flush=True)
    result = subprocess.run(cmd)
    status = "✓" if result.returncode == 0 else "✗"
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {status} Finished: {task} (exit {result.returncode})", flush=True)
    return task, result.returncode


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run Terminal Bench tasks sequentially or in parallel.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  python3 run_tasks.py                  # run one task at a time
  python3 run_tasks.py -c 2             # run 2 tasks in parallel
  python3 run_tasks.py -c 4 --config configurations/claude-code.yaml
        """,
    )
    parser.add_argument(
        "-c", "--concurrency",
        type=int,
        default=1,
        metavar="N",
        help="number of tasks to run in parallel (default: 1)",
    )
    parser.add_argument(
        "--config",
        default="agent.yaml",
        metavar="PATH",
        help="path to the harbor agent config YAML (default: agent.yaml)",
    )
    args = parser.parse_args()

    tasks = TASKS
    if not tasks:
        print("No tasks enabled. Uncomment entries in the TASKS list.", file=sys.stderr)
        sys.exit(1)

    print(
        f"Running {len(tasks)} task(s) with concurrency={args.concurrency}, config={args.config}\n")

    failed: list[str] = []

    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = {executor.submit(
            run_task, task, args.config): task for task in tasks}
        for future in as_completed(futures):
            task, returncode = future.result()
            if returncode != 0:
                failed.append(task)

    print(
        f"\nAll tasks completed. {len(tasks) - len(failed)}/{len(tasks)} succeeded.")
    if failed:
        print("Failed tasks:")
        for task in failed:
            print(f"  - {task}")
        sys.exit(1)


if __name__ == "__main__":
    main()

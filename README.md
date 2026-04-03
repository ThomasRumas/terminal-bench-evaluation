## Run a batch of tasks with run_tasks.py

`run_tasks.py` runs a predefined list of Terminal Bench tasks sequentially or in parallel.

**Usage:**

```bash
python3 run_tasks.py [-c N] [--config PATH]
```

| Argument              | Description                          | Default          |
| --------------------- | ------------------------------------ | ---------------- |
| `-c`, `--concurrency` | Number of tasks to run in parallel   | `1` (sequential) |
| `--config`            | Path to the harbor agent config YAML | `agent.yaml`     |

**Examples:**

```bash
python3 run_tasks.py                                          # run one task at a time
python3 run_tasks.py -c 2                                     # run 2 tasks in parallel
python3 run_tasks.py -c 4 --config configurations/claude-code.yaml
```

Each task gets a unique job name (`YYYY-MM-DD__HH-MM-SS__<task>`) so concurrent runs never collide.  
Each task is launched with `--export-traces` so trajectories are saved under `jobs/`.  
A final summary shows how many tasks succeeded and lists any failures.

To add or remove tasks, edit the `TASKS` list at the top of the script.

## Parse results with parse_results.py

After running tasks, generate a human-readable JSON report:

```bash
python3 parse_results.py          # parses jobs/ by default
python3 parse_results.py jobs/    # explicit path
```

The report is printed to stdout and saved to `jobs/report.json`. For each task it includes:

- `status`: `success`, `failure`, or `error`
- `reward`: score returned by the verifier (1.0 = full pass)
- `timing`: duration of setup, execution, verifier, and total
- `tokens`: input/output/cache token counts
- `error`: exception type and message (for timed-out or crashed runs)
- `test_details`: individual test pass/fail breakdown from the verifier

## Agent configuration

The `configurations/` folder contains annotated YAML config files for each supported agent:

- `configurations/claude-code.yaml` — all available parameters for the claude-code agent
- `configurations/opencode.yaml` — all available parameters for the opencode agent

Pass a config file to any `harbor run` command with `--config`:

```bash
harbor run -d terminal-bench --config configurations/claude-code.yaml --include-task-name "fix-git"
```

Key parameters documented in the config files:

| Parameter                    | Description                                                      |
| ---------------------------- | ---------------------------------------------------------------- |
| `name`                       | Agent to use (`claude-code`, `opencode`, etc.)                   |
| `model_name`                 | Model override (required for opencode, format: `provider/model`) |
| `override_timeout_sec`       | Hard cap on agent execution time in seconds                      |
| `override_setup_timeout_sec` | Hard cap on agent install/setup phase                            |
| `max_timeout_sec`            | Safety ceiling — only clips, never raises the timeout            |
| `kwargs`                     | Agent-specific options (turns, budget, tools, MCP servers, …)    |
| `env`                        | Extra environment variables injected into the agent's shell      |

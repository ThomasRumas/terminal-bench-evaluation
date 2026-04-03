# harbor-claude-code

DevContainer feature that installs the [Harbor](https://harborframework.com) evaluation framework and wires up your Claude Code provider configuration as container environment variables.

## What it does

- Installs **Harbor** (`pip install harbor`) via the `install.sh` script
- Exposes `ANTHROPIC_API_KEY`, `ANTHROPIC_BASE_URL`, and `ANTHROPIC_MODEL` inside the container so `harbor run` passes them into each Docker sandbox it spawns
- Automatically pulls in **Python 3.12** and **Docker-in-Docker** as dependencies — no need to declare them separately

## Usage

### From a local folder (development)

Reference the feature by its relative path in your `devcontainer.json`:

```json
{
  "image": "mcr.microsoft.com/devcontainers/base:ubuntu-24.04",
  "features": {
    "./.devcontainer/harbor-claude-code": {}
  }
}
```

Option values default to the matching host environment variable (`${localEnv:ANTHROPIC_API_KEY}`, etc.), so if those are already set in your shell nothing else is needed.

### From ghcr.io (once published)

```json
{
  "image": "mcr.microsoft.com/devcontainers/base:ubuntu-24.04",
  "features": {
    "ghcr.io/your-org/features/harbor-claude-code:1": {}
  }
}
```

## Options

| Option             | Type   | Default                          | Description                                                                                            |
| ------------------ | ------ | -------------------------------- | ------------------------------------------------------------------------------------------------------ |
| `harborVersion`    | string | `latest`                         | Harbor PyPI version to install. Pin to a specific release (e.g. `0.3.0`) for reproducibility.          |
| `anthropicApiKey`  | string | `${localEnv:ANTHROPIC_API_KEY}`  | Anthropic API key. Use `local` for local providers (Ollama, vLLM, etc.) that don't require a real key. |
| `anthropicBaseUrl` | string | `${localEnv:ANTHROPIC_BASE_URL}` | Anthropic-compatible API base URL. Leave empty to use the official Anthropic API.                      |
| `anthropicModel`   | string | `${localEnv:ANTHROPIC_MODEL}`    | Model name passed to Claude Code (e.g. `claude-opus-4-1` or `Qwen3.5-0.8B`).                           |

## Examples

### Official Anthropic API

Set `ANTHROPIC_API_KEY` in your host shell before opening the DevContainer — the feature picks it up automatically via `${localEnv:...}`:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

```json
"./.devcontainer/harbor-claude-code": {
    "anthropicModel": "claude-opus-4-1"
}
```

### Local Ollama instance

`host.docker.internal` resolves from inside Docker back to your host machine:

```json
"./.devcontainer/harbor-claude-code": {
    "anthropicApiKey": "local",
    "anthropicBaseUrl": "http://host.docker.internal:11434",
    "anthropicModel": "Qwen3.5-0.8B"
}
```

Or export them in your shell and keep the `devcontainer.json` clean:

```bash
export ANTHROPIC_API_KEY=local
export ANTHROPIC_BASE_URL=http://host.docker.internal:11434
export ANTHROPIC_MODEL=Qwen3.5-0.8B
```

### Pin a specific Harbor version

```json
"./.devcontainer/harbor-claude-code": {
    "harborVersion": "0.3.0"
}
```

## Running evaluations

Once inside the DevContainer:

```bash
# List available benchmarks
harbor datasets list

# Run the hello-world task (1 task, quick smoke test)
harbor run -d hello-world -a claude-code -m "$ANTHROPIC_MODEL"

# Run 10 tasks from Terminal-Bench sample
harbor run -d terminal-bench-sample -a claude-code -m "$ANTHROPIC_MODEL" -n 4

# Run full Terminal-Bench 2.0
harbor run -d terminal-bench-2 -a claude-code -m "$ANTHROPIC_MODEL" -n 4

# Browse results in the web UI
harbor view jobs
```

## Dependencies

The following features are automatically installed via `dependsOn` — do not add them separately in your `devcontainer.json`:

- [`ghcr.io/devcontainers/features/python:1`](https://github.com/devcontainers/features/tree/main/src/python) — Python 3.12
- [`ghcr.io/devcontainers/features/docker-in-docker:2`](https://github.com/devcontainers/features/tree/main/src/docker-in-docker) — Docker daemon inside the container

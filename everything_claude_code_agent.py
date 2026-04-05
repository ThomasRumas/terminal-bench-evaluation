"""Custom agent that does a full everything-claude-code install inside the container.

Installs:
  - 156 skills  → ~/.claude/skills/
  - 38 agents   → ~/.claude/agents/
  - 72 commands → ~/.claude/commands/
  - rules       → ~/.claude/rules/  (common + all language subdirs)
  - hooks       → merged into ~/.claude/settings.json
  - CLAUDE.md   → ~/.claude/CLAUDE.md
"""

import json

from harbor.agents.base import BaseEnvironment
from harbor.agents.installed.claude_code import ClaudeCode

ECC_REPO = "https://github.com/affaan-m/everything-claude-code.git"
ECC = "/tmp/ecc"


class ClaudeCodeWithECC(ClaudeCode):
    """ClaudeCode agent with the full everything-claude-code addon installed."""

    async def install(self, environment: BaseEnvironment) -> None:
        await super().install(environment)

        # ── 1. Ensure git is available (not present in all task images) ─────────
        await self.exec_as_root(
            environment,
            command=(
                "command -v git >/dev/null 2>&1 || ("
                "  if command -v apt-get >/dev/null 2>&1; then"
                "    apt-get update -qq && apt-get install -y -qq git;"
                "  elif command -v apk >/dev/null 2>&1; then"
                "    apk add --no-cache git;"
                "  elif command -v yum >/dev/null 2>&1; then"
                "    yum install -y git;"
                "  fi"
                ")"
            ),
            env={"DEBIAN_FRONTEND": "noninteractive"},
        )

        # ── 2. Clone ECC (shallow, no history) ────────────────────────────────
        await self.exec_as_agent(
            environment,
            command=f"git clone --depth=1 {ECC_REPO} {ECC} 2>&1 && echo 'ECC cloned'",
        )

        # ── 3. Skills → ~/.claude/skills/ (Harbor copies via skills_dir) ──────
        self.skills_dir = f"{ECC}/skills"

        # ── 4. Agents, commands, rules ────────────────────────────────────────
        await self.exec_as_agent(
            environment,
            command=(
                "set -euo pipefail; "
                "CLAUDE_DIR=${CLAUDE_CONFIG_DIR:-$HOME/.claude}; "
                f"mkdir -p $CLAUDE_DIR/agents $CLAUDE_DIR/commands $CLAUDE_DIR/rules; "
                # agents
                f"cp -r {ECC}/agents/. $CLAUDE_DIR/agents/; "
                # commands
                f"cp -r {ECC}/commands/. $CLAUDE_DIR/commands/; "
                # rules — copy all language subdirectories
                f"cp -r {ECC}/rules/. $CLAUDE_DIR/rules/; "
                # CLAUDE.md
                f"cp {ECC}/CLAUDE.md $CLAUDE_DIR/CLAUDE.md; "
                "echo 'ECC agents/commands/rules/CLAUDE.md installed'"
            ),
        )

        # ── 5. Hooks → write ~/.claude/settings.json (pure bash, no python3/node/jq) ──
        # Extract the "hooks": {...} block from hooks.json by line range and
        # wrap it in a new settings.json object.
        await self.exec_as_agent(
            environment,
            command=(
                "set -euo pipefail; "
                "CLAUDE_DIR=${CLAUDE_CONFIG_DIR:-$HOME/.claude}; "
                "SETTINGS=$CLAUDE_DIR/settings.json; "
                f"HOOKS_SRC={ECC}/hooks/hooks.json; "
                # Line where "hooks": starts
                'hooks_line=$(grep -n \'"hooks"\' "$HOOKS_SRC" | head -1 | cut -d: -f1); '
                # Total lines in file; last line is the outer closing brace → skip it
                'total_lines=$(wc -l < "$HOOKS_SRC"); '
                # Slice out the hooks block and wrap it in a top-level object
                'hooks_block=$(sed -n "${hooks_line},$((total_lines - 1))p" "$HOOKS_SRC"); '
                'printf \'{\n%s\n}\n\' "$hooks_block" > "$SETTINGS"; '
                "echo 'ECC hooks written to settings.json'"
            ),
        )

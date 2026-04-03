#!/bin/bash
set -euo pipefail

# Resolve devcontainer.env relative to this script's location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$(cd "$SCRIPT_DIR/.." && pwd)/devcontainer.env"

MARKER="# harbor: devcontainer.env"
SOURCE_BLOCK="$MARKER
if [ -f \"$ENV_FILE\" ]; then
    set -a
    # shellcheck source=/dev/null
    source \"$ENV_FILE\"
    set +a
fi"

for RC_FILE in "$HOME/.bashrc" "$HOME/.zshrc"; do
    if [ ! -f "$RC_FILE" ]; then
        touch "$RC_FILE"
    fi
    if grep -qF "$MARKER" "$RC_FILE" 2>/dev/null; then
        echo "$RC_FILE: already configured, skipping"
    else
        printf "\n%s\n" "$SOURCE_BLOCK" >> "$RC_FILE"
        echo "$RC_FILE: added devcontainer.env sourcing"
    fi
done

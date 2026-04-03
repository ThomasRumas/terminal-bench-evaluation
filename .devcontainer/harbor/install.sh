#!/bin/bash
set -e

HARBOR_VERSION="${HARBORVERSION:-latest}"

echo "Installing Harbor evaluation framework..."

if [ "$HARBOR_VERSION" = "latest" ]; then
    pip install --upgrade harbor
else
    pip install "harbor==${HARBOR_VERSION}"
fi

echo "Harbor $(harbor --version 2>/dev/null | head -1 || echo '(version check skipped)') installed."

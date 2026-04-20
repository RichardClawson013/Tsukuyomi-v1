#!/usr/bin/env bash
set -euo pipefail
VERSION=$(grep -E '^version' pyproject.toml | head -1 | sed -E 's/.*"([^"]+)".*/\1/')
echo "Releasing tsukuyomi ${VERSION}"
python -m build
echo "Artifacts in dist/"
ls -la dist/
echo "Tag with: git tag v${VERSION} && git push origin v${VERSION}"

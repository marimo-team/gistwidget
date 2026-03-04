#!/usr/bin/env bash
set -euo pipefail

BUMP="${1:-patch}"
uv version --bump "$BUMP"
VERSION="v$(uv version | awk '{print $2}')"

git add pyproject.toml uv.lock
git commit -m "$VERSION"
git tag "$VERSION"
git push origin main "$VERSION"

echo "Released $VERSION"

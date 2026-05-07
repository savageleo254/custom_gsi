#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <tag> <repo> [image_path]"
  echo "Example: $0 rmx2189-microg-v1 youruser/custom_gsi out/crdroid10-rmx2189-microg.img"
  exit 1
fi

TAG="$1"
REPO="$2"
IMAGE_PATH="${3:-out/crdroid10-rmx2189-microg.img}"

if [[ ! -f "$IMAGE_PATH" ]]; then
  echo "Image not found: $IMAGE_PATH" >&2
  exit 1
fi

if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI (gh) is required." >&2
  exit 1
fi

if ! git remote get-url origin >/dev/null 2>&1; then
  echo "Git remote 'origin' is not set. Add it first: git remote add origin <url>" >&2
  exit 1
fi

git push -u origin work
git tag -f "$TAG"
git push -f origin "$TAG"

gh release create "$TAG" "$IMAGE_PATH" \
  --repo "$REPO" \
  --title "RMX2189 MicroG GSI $TAG" \
  --notes "Flashable RMX2189 tuned Android 14 GSI with baked-in MicroG."

echo "Release published: $REPO tag $TAG"

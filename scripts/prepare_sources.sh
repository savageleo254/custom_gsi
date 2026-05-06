#!/usr/bin/env bash
set -euo pipefail

MANIFEST_FILE="${1:-manifests/rmx2189_sources.txt}"
BASE_DIR="${2:-.}"

if [[ ! -f "$MANIFEST_FILE" ]]; then
  echo "Manifest file not found: $MANIFEST_FILE" >&2
  exit 1
fi

while IFS= read -r line; do
  [[ -z "$line" || "$line" =~ ^# ]] && continue
  repo_url="$(awk '{print $1}' <<<"$line")"
  dest_rel="$(awk '{print $2}' <<<"$line")"
  dest_path="$BASE_DIR/$dest_rel"

  mkdir -p "$(dirname "$dest_path")"
  if [[ -d "$dest_path/.git" ]]; then
    echo "[update] $dest_rel"
    git -C "$dest_path" fetch --all --tags
    git -C "$dest_path" pull --ff-only || true
  else
    echo "[clone] $repo_url -> $dest_rel"
    git clone --depth 1 "$repo_url" "$dest_path"
  fi
done < "$MANIFEST_FILE"

echo "Source preparation complete."

#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 /path/to/input-system.img [GmsCore.apk FakeStore.apk [ServicesFrameworkProxy.apk]]"
  exit 1
fi

INPUT_IMG="$1"
OUTPUT_IMG="out/crdroid10-rmx2189-microg.img"

cmd=(python3 scripts/patch_system_image.py
  --input "$INPUT_IMG"
  --props patches/rmx2189-system-props.txt
  --output "$OUTPUT_IMG"
)

if [[ $# -ge 3 ]]; then
  cmd+=(--enable-microg
    --microg-apk "$2:system/priv-app/GmsCore/GmsCore.apk"
    --microg-apk "$3:system/priv-app/FakeStore/FakeStore.apk")
fi

if [[ $# -ge 4 ]]; then
  cmd+=(--microg-apk "$4:system/priv-app/GsfProxy/GsfProxy.apk")
fi

"${cmd[@]}"

echo "Done: $OUTPUT_IMG"

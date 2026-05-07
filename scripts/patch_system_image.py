#!/usr/bin/env python3
"""Build RMX2189-tuned, flash-ready GSI images with optional baked-in MicroG.

Example:
  python3 scripts/patch_system_image.py \
    --input crDroid-10.13-arm64_bvN-Unofficial.img \
    --props patches/rmx2189-system-props.txt \
    --output out/crdroid10-rmx2189-microg.img \
    --microg-apk GmsCore.apk:system/priv-app/GmsCore/GmsCore.apk \
    --microg-apk ServicesFrameworkProxy.apk:system/priv-app/GsfProxy/GsfProxy.apk \
    --microg-apk FakeStore.apk:system/priv-app/FakeStore/FakeStore.apk \
    --enable-microg
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

SPARSE_MAGIC = b"\x3a\xff\x26\xed"


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def ensure_tool(name: str) -> None:
    if shutil.which(name) is None:
        raise SystemExit(f"Missing required tool: {name}")


def is_sparse_image(image: Path) -> bool:
    with image.open("rb") as f:
        return f.read(4) == SPARSE_MAGIC


def read_file_from_image(raw_img: Path, source: str, out_file: Path) -> str:
    run(["debugfs", "-R", f"dump -p {source} {out_file}", str(raw_img)])
    return out_file.read_text(encoding="utf-8", errors="ignore")


def write_file_into_image(raw_img: Path, in_file: Path, target: str) -> None:
    run(["debugfs", "-w", "-R", f"rm {target}", str(raw_img)])
    run(["debugfs", "-w", "-R", f"write {in_file} {target}", str(raw_img)])


def patch_build_prop(raw_img: Path, props_file: Path, temp_dir: Path) -> None:
    bp = temp_dir / "build.prop"
    existing_text = read_file_from_image(raw_img, "/system/build.prop", bp)
    existing = existing_text.splitlines()
    to_append: list[str] = []

    for line in props_file.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        key = s.split("=", 1)[0]
        if not any(e.startswith(f"{key}=") for e in existing):
            to_append.append(s)

    with bp.open("a", encoding="utf-8") as f:
        f.write("\n# RMX2189 tuned props\n")
        for row in to_append:
            f.write(row + "\n")

    write_file_into_image(raw_img, bp, "/system/build.prop")


def ensure_dir(raw_img: Path, target_dir: str) -> None:
    try:
        run(["debugfs", "-w", "-R", f"mkdir {target_dir}", str(raw_img)])
    except subprocess.CalledProcessError:
        pass


def inject_microg_permissions(raw_img: Path, temp_dir: Path) -> None:
    xml = temp_dir / "microg.xml"
    xml.write_text(
        """<permissions>
    <privapp-permissions package=\"com.google.android.gms\">
        <permission name=\"android.permission.FAKE_PACKAGE_SIGNATURE\"/>
        <permission name=\"android.permission.INTERNET\"/>
        <permission name=\"android.permission.ACCESS_FINE_LOCATION\"/>
        <permission name=\"android.permission.ACCESS_COARSE_LOCATION\"/>
    </privapp-permissions>
</permissions>
""",
        encoding="utf-8",
    )
    write_file_into_image(raw_img, xml, "/system/etc/permissions/microg.xml")


def copy_file_into_image(raw_img: Path, src: Path, dest: str) -> None:
    run(["debugfs", "-w", "-R", f"write {src} {dest}", str(raw_img)])


def rm_path(raw_img: Path, path: str) -> None:
    run(["debugfs", "-w", "-R", f"rmdir {path}", str(raw_img)])


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, type=Path)
    p.add_argument("--props", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--enable-microg", action="store_true")
    p.add_argument(
        "--microg-apk",
        action="append",
        default=[],
        help="Format: /local/path.apk:system/priv-app/.../Name.apk",
    )
    args = p.parse_args()

    for tool in ["debugfs", "e2fsck", "resize2fs", "simg2img"]:
        ensure_tool(tool)

    if not args.input.exists() or not args.props.exists():
        raise SystemExit("Input image or props file not found")

    args.output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="rmx2189_patch_") as td:
        temp_dir = Path(td)
        raw_img = temp_dir / "system_raw.img"

        if is_sparse_image(args.input):
            run(["simg2img", str(args.input), str(raw_img)])
        else:
            shutil.copy2(args.input, raw_img)

        run(["e2fsck", "-fy", str(raw_img)])
        run(["resize2fs", "-M", str(raw_img)])
        if args.enable_microg:
            with raw_img.open("ab") as f:
                f.truncate(raw_img.stat().st_size + 512 * 1024 * 1024)
            run(["resize2fs", str(raw_img)])
        patch_build_prop(raw_img, args.props, temp_dir)

        if args.enable_microg:
            ensure_dir(raw_img, "/system/priv-app/GmsCore")
            ensure_dir(raw_img, "/system/priv-app/GsfProxy")
            ensure_dir(raw_img, "/system/priv-app/FakeStore")
            ensure_dir(raw_img, "/system/etc/permissions")
            inject_microg_permissions(raw_img, temp_dir)

            for mapping in args.microg_apk:
                src_str, dest = mapping.split(":", 1)
                src = Path(src_str)
                if not src.exists():
                    raise SystemExit(f"MicroG APK not found: {src}")
                copy_file_into_image(raw_img, src, "/" + dest.lstrip("/"))

            for dead_ims in [
                "/system/system_ext/priv-app/ims",
                "/system/product/priv-app/ims",
            ]:
                try:
                    rm_path(raw_img, dead_ims)
                except subprocess.CalledProcessError:
                    pass

        run(["e2fsck", "-fy", str(raw_img)])
        shutil.copy2(raw_img, args.output)

    print(f"Patched image created: {args.output}")


if __name__ == "__main__":
    main()

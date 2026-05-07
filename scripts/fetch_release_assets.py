#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, urllib.request
from pathlib import Path


def fetch_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "rmx2189-builder"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode("utf-8"))


def download(url: str, out: Path):
    req = urllib.request.Request(url, headers={"User-Agent": "rmx2189-builder"})
    with urllib.request.urlopen(req) as r, out.open("wb") as f:
        f.write(r.read())


def pick(assets, contains):
    for a in assets:
        n = a["name"].lower()
        if all(c.lower() in n for c in contains):
            return a
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", type=Path, default=Path("downloads"))
    ap.add_argument("--base-img-url", default="")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    if args.base_img_url:
        name = args.base_img_url.rstrip("/").split("/")[-1]
        print(f"base_img: {name}")
        if not args.dry_run:
            download(args.base_img_url, args.out_dir / name)

    rel = fetch_json("https://api.github.com/repos/microg/GmsCore/releases")
    assets = rel[0].get("assets", [])
    gms = pick(assets, ["com.google.android.gms", ".apk"]) or pick(assets, ["org.microg.gms", ".apk"])
    fake = pick(assets, ["com.android.vending", ".apk"])

    if not gms or not fake:
        raise SystemExit("Could not resolve MicroG GmsCore/FakeStore assets from latest release")

    for label, asset in [("GmsCore.apk", gms), ("FakeStore.apk", fake)]:
        print(f"{label}: {asset['name']}")
        if not args.dry_run:
            download(asset["browser_download_url"], args.out_dir / asset["name"])

    print("ServicesFrameworkProxy.apk: not fetched (legacy/optional for modern MicroG releases)")


if __name__ == "__main__":
    main()

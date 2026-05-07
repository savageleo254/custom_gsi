# RMX2189 prebuilt-style GSI pipeline (Android 14 + MicroG)

Target output image:

- `out/crdroid10-rmx2189-microg.img`

## Quick start

1) Optional source prep:
```bash
./scripts/prepare_sources.sh
```

2) Fetch latest MicroG release APK names (and optionally download base image URL):
```bash
python3 scripts/fetch_release_assets.py --dry-run
```

3) Build tuned image (MicroG-ready only):
```bash
./build_rmx2189_tuned.sh crDroid-10.13-arm64_bvN-Unofficial.img
```

4) Build fully prebuilt MicroG image:
```bash
./build_rmx2189_tuned.sh \
  crDroid-10.13-arm64_bvN-Unofficial.img \
  com.google.android.gms-*.apk com.android.vending-*.apk
```

Optional legacy proxy APK as a 4th arg:
```bash
./build_rmx2189_tuned.sh base.img GmsCore.apk FakeStore.apk ServicesFrameworkProxy.apk
```

## Flash
```bash
fastboot erase system
fastboot flash system out/crdroid10-rmx2189-microg.img
fastboot reboot
```

## Publish/update on GitHub

If your local branch has the latest pipeline changes and built artifact metadata, publish with:

```bash
git remote add origin <your_repo_url>   # one-time, if needed
git push -u origin work
```

To attach the built image to a GitHub release:

```bash
gh release create rmx2189-microg-v1 \
  out/crdroid10-rmx2189-microg.img \
  --title "RMX2189 MicroG GSI" \
  --notes "Android 14 crDroid 10.13 tuned image for RMX2189"
```

### One-command GitHub release

```bash
./scripts/release_github.sh rmx2189-microg-v1 <owner/repo> out/crdroid10-rmx2189-microg.img
```

This will push branch `work`, force-update the tag, and upload the IMG to a GitHub Release.

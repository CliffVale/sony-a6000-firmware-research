# Known Issues & Future Work

This repository documents a single camera teardown done in a weekend. It is
published **as-is**: the parts that are solid are marked solid, and the parts
that are unfinished or buggy are listed below so nobody gets misled.

## Known issues in the scripts

### 1. `carve_fat16.py` — corrupted names in some subdirectories

**Status: known bug, not yet fixed.**

The FAT16 userdata partition on this camera's NAND has been written and
erased many times over the camera's life. In a few subdirectories
(e.g. `/local/com.sony.scalar.dlsys.*/`), the FAT chain and/or directory
entries contain stale data, so the tool emits files with garbage names and
skips some entries (`could not locate ... skipping`).

**Impact:** the top-level tree is clean, all 5 APKs and the WiFi/backup files
extract correctly, but `--outdir` extraction of the `/local/*` trees is
lossy. Do **not** treat the extracted `/local` files as authoritative.

**Planned fix:** validate each FAT chain walk (detect loops / reads past the
data area), verify the LFN checksum byte against the short name, and drop
entries whose cluster chain fails validation instead of emitting garbage.

### 2. `verify_partitions.py` — written but not yet run against the official dump

**Status: not yet validated.**

This script checks that each published partition file on disk matches the
region it was carved from (same bytes). It was written for this release but
has **not** been executed on a fresh download, so there may be path/argument
bugs. Run it with `--help` first; treat its output as unverified until then.

### 3. `map_regions.py` — heuristic region boundaries

**Status: works, but heuristic.**

Region boundaries are inferred from filesystem signatures + erase-block
alignment on a partially-erased NAND. Boundaries may be off by one erase
block (256 KB) in erased regions where no signature exists. See
`docs/05-region-map.md` for the assumptions.

## Future work

### 4. Shutter count from the settings backup (BKDA)

The camera's `nflasha` also holds a settings backup that is only readable
through the camera's `BKDA` USB command (part of the PlayMemories Camera Apps
protocol). Offline parsing of the `BK1.BAK` / `BK2.BAK` files found in the
dump does **not** yield the shutter count (they are Android app/package
backups, not the camera settings backup). To read the real backup you must:

1. Reconnect the camera over USB.
2. Use `pmca-console backup` (Sony-PMCA-RE) to issue the `BKDA` command.
3. Physically press OK on the camera when prompted.

This was deliberately not done during the teardown. Note the shutter count is
already known for this unit (42,536 actuations, read from ARW EXIF
`ImageCount`), so this only matters for reproducing the method.

### 5. Official firmware binaries — deliberately excluded from this repo

The decrypted `firmware.tar` / `firmware.fdat` / `firmware.dat` and the raw
`nflasha` dump are **not** published here (Sony proprietary). They live in a
private archive. To reproduce the unpacking you only need the official
updater from Sony's site (`Update_ILCE6000V321.exe`), which is freely
downloadable — see `docs/02-phase1-unpacking.md`.

### 6. WiFi credentials redaction check

The dump contains the camera owner's WiFi credentials
(`/dontpanic/systemkeys/wpa_supplicant*.conf`). These are **not** published.
If you reproduce this work on your own camera, double-check your own dump
before publishing anything — do not ship other people's credentials.

### 7. Cross-camera generalization

Everything here was verified on one ILCE-6000 at firmware 3.21. Partition
offsets, the Android userdata layout, and the updater structure are likely
similar on other 2014–2018 Sony E-mount cameras (A5100, A7 series, etc.) but
have **not** been tested. A natural next step is running the same pipeline on
a second body and diffing the region maps.

---

*Found a bug or did this work on your own camera? Open an issue or PR — the
point of publishing this is that it gets better with more data points.*

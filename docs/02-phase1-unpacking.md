# 02 — Phase 1: Unpacking the Official Firmware

> **Goal**: obtain and decrypt Sony's published A6000 firmware, without the camera.

## 2.1 Getting the updater

Sony publishes firmware updates on `support.d-imaging.sony.co.jp`. Two formats:

- `Update_ILCE6000V321.exe` (Windows, ~207 MB)
- `Update_ILCE6000V321.dmg` (macOS, ~205 MB)

**Gotcha**: Sony's support pages return HTTP 403 to non-browser clients (curl,
wget). The *real* CDN URLs are embedded in the pages and can be recovered from
**Wayback Machine snapshots** of the download page:

```
# Windows
https://support.d-imaging.sony.co.jp/download/IMT/Update_ILCE6000V321.exe?fm=am

# macOS
https://support.d-imaging.sony.co.jp/download/NEX/AcicwqgUEQ/Update_ILCE6000V321.dmg?fm=am
```

Verify integrity:

```
# macOS DMG  ->  sha256 844349ff...a3e
# Windows EXE -> sha256 0c3e61b0...d57
```

## 2.2 Extracting the .dat payload

**macOS path (works out of the box):**

```bash
7z x Update_ILCE6000V321.dmg        # DMG container
# -> inside: FirmwareData_ILCE6000V321.dat   (203 MB)
```

**Windows path (fwtool.py can't handle it):**

`fwtool.py` has an EXE unpacker, but the Sony installer is an LZH self-extracting
archive that it rejects (`Unknown exe file`). The DMG route is the reliable one —
the `.dat` payload is identical in both.

`.dat` integrity:

```
sha256 FirmwareData_ILCE6000V321.dat
29aef21ab9b5c2e98388974ac9749c2cbfb1815273b444e62f2e41398aa8892f
```

## 2.3 Decrypting

```bash
git clone https://github.com/ma1co/fwtool.py
cd fwtool.py && pip install -r requirements.txt

python3 fwtool.py unpack FirmwareData_ILCE6000V321.dat
```

The `.dat` is encrypted with the **CXD90014** crypter. Because the A6000's SoC
does not enforce cryptographic signature verification on its firmware (a design
choice Sony made for this generation), `fwtool.py` decrypts it fully offline.

## 2.4 The unpacked tree

```
firmware-3.21-unpacked/
├── config.yaml                  crypter info (CXD90014, USB descriptors)
├── firmware.dat / .fdat         decrypted image / header
├── firmware.tar                 the real payload
├── firmware.tar_unpacked/
│   ├── 0100_config               config data
│   ├── 0110_backup               backup region (SYSMUSASHI-DSLR)
│   ├── 0300_partconf             partition config
│   ├── 0600_gps / 0630_ca / 0640_darwin / 0650_prfile   calibration data
│   ├── 0700_part_image/dev/      nflasha3, nflasha5, nflasha7,
│   │                             nflasha15, nflasha16  ← the partitions
│   └── 0800_appli/               android/, lens/, setting/
└── updater.img                   updater OS (VMLINUX.BIN, INITRD.IMG, busybox)
```

### The published partitions

| Partition | Size | Notes |
|---|---|---|
| nflasha3 | 10.96 MB | TPZL partition |
| nflasha5 | 40.30 MB | TPZL partition |
| nflasha7 | 3.17 MB | TPZL partition |
| nflasha15 | 80.15 MB | TPZL partition (largest) |
| nflasha16 | 56.28 MB | TPZL partition |

"TPZL" is Sony's partition container format (Sony's Android boot / partition
layering). `updater.img` is the rescue/updater OS the camera boots into when you
run an official firmware update.

## 2.5 What Phase 1 proves

- The **published** firmware is fully readable offline — no camera required.
- These 5 partitions will be the **ground truth** for verifying the raw dump
  in [Phase 2](03-phase2-raw-dump.md) / [Verification](04-verification.md).

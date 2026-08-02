<div align="center">

# Sony ILCE-6000 (A6000) Firmware Research

**Complete reverse-engineering of a consumer camera's firmware: from Sony's official
updater to a byte-verified raw NAND dump — including the discovery of the camera's
internal Android runtime.**

</div>

---

## TL;DR

| | Result |
|---|---|
| **Camera** | Sony ILCE-6000 (A6000), Firmware **3.21**, USB ID `054c:07c4` |
| **SoC** | Qualcomm **CXD90014** — *not* crypto-signed (that's why this works) |
| **Phase 1** | Official updater (EXE/DMG) → `.dat` → decrypted firmware tree ✅ |
| **Phase 2** | `pmca-console updatershell` → `pull /dev/nflasha` → **483 MB raw NAND dump** ✅ |
| **Verification** | All 5 published partitions found **byte-identical** in the dump ✅ |
| **Biggest find** | The A6000 runs **Android internally** — the dump contains a live FAT16 `/data` filesystem with **5 installed apps**, Wi-Fi configs, and settings backups |

This repository is the **written-up methodology and findings**. Raw binaries and
personal camera data are **not** distributed here (Sony firmware is proprietary;
the camera dump contains personal data). See [docs/01-overview.md](docs/01-overview.md)
for what's public vs. preserved privately.

---

## Repository contents

```
docs/
├── 01-overview.md              What this project is, scope, safety
├── 02-phase1-unpacking.md      Download + decrypt the official firmware
├── 03-phase2-raw-dump.md       Dump the camera's NAND via updatershell
├── 04-verification.md          Byte-identical partition verification
├── 05-region-map.md            Full layout of the 483 MB raw dump
└── 06-android-userdata.md      The camera's Android runtime, discovered
scripts/
├── verify_partitions.py        Re-check published partitions in a dump
├── carve_fat16.py              Carve the Android FAT16 /data out of nflasha
└── map_regions.py              Map non-erased regions of a raw dump
ACKNOWLEDGEMENTS.md             Full credits for every tool & app referenced
KNOWN_ISSUES.md                 Known bugs, caveats, and future work
LICENSE
```

---

## Key results

### 1. Official firmware unpacked (no camera needed)
- `Update_ILCE6000V321.dmg` → `FirmwareData_ILCE6000V321.dat` (203 MB)
- `fwtool.py unpack` (crypter **CXD90014**) → full firmware tree:
  config, backup regions, `0700_part_image` (nflasha3/5/7/15/16), `0800_appli`
  (Android + lens + setting), updater.img (VMLINUX.BIN / INITRD.IMG / busybox)

### 2. Raw NAND dump from the camera (non-destructive)
- `pmca-console updatershell -m ILCE-6000` → `pull /dev/nflasha` → 483 MB
- ⚠️ **Gotcha documented**: the camera asks for a physical **OK button press**
  ("reset device OK") to enter updater mode — the dump hangs without it.

### 3. Verification: the dump matches the published firmware exactly
| Partition | Offset in dump | Size | Match |
|---|---|---|---|
| nflasha3 | `0x01340000` | 10.96 MB | ✅ `diff_bytes = 0` |
| nflasha5 | `0x03b40000` | 40.30 MB | ✅ `diff_bytes = 0` |
| nflasha7 | `0x07c40000` | 3.17 MB | ✅ `diff_bytes = 0` |
| nflasha15 | `0x08b40000` | 80.15 MB | ✅ `diff_bytes = 0` |
| nflasha16 | `0x0ef40000` | 56.28 MB | ✅ `diff_bytes = 0` |

Ground truth: camera FW 3.21 == published 3.21.

### 4. The camera runs Android — and we have its `/data`
At `0x14200000` in the dump sits a ~100 MB **FAT16 filesystem** — the camera's
Android userdata. Inside:

- **Installed apps (APKs recovered):**
  - `com.github.ma1co.openmemories.tweak` — **OpenMemories: Tweak** (the open-source jailbreak)
  - OpenMemories: AppStore, FocusBracket, BetterManual, TimeLapse (Jonas Juffinger)
- **Settings backups** `BK1.BAK` / `BK2.BAK` (1.3 MB each)
- **Wi-Fi supplicant configs** (WPS/Wi-Fi Direct, `device_name=ILCE-6000_*`)
- **Battery calibration** file, Dalvik caches, Sony system services

---

## Why this matters

- The A6000 is a **fully Android-powered camera** — confirming that modern Sony
  ILCs run Android internally, with a scalar/launcher layer on top.
- The **updatershell route** is a clean, non-destructive way to dump these devices
  without a soldering iron — the physical OK-press gotcha is documented here so
  others don't hit the same 5-minute hang.
- The byte-identical verification proves the published firmware and the flashed
  firmware are one and the same, and anchors the region map.

---

## Who this is for

- **Sony Alpha owners** — learn exactly what is on your camera's flash, how to
  dump it read-only, and why the physical OK-press is needed.
- **OpenMemories / camera-homebrew developers** — a complete worked example of
  the updatershell route plus a documented NAND region map to build against.
- **Firmware / embedded-Linux researchers** — a clean case study of a
  Qualcomm CXD90014 device, updater extraction, and NAND dump forensics.
- **Android forensics folks** — a consumer device where the Android userdata
  partition is carved straight out of raw NAND, with the recovery scripts.

---

## Reproduce it yourself

```bash
# Phase 1 — unpack official firmware (needs: python3, fwtool.py, 7z)
#   (URLs in docs/02-phase1-unpacking.md — Sony's support site 403s on curl;
#    the real CDN URLs were recovered from Wayback Machine snapshots)

# Phase 2 — dump your own camera (needs: Sony-PMCA-RE, camera in updater mode)
pip install git+https://github.com/ma1co/Sony-PMCA-RE
pmca-console updatershell -m ILCE-6000   # press OK on the camera screen!
# then, inside the shell:
#   pull /dev/nflasha  nflasha
#   pull /dev/bootloader  boot1
#   quit

# Verify against the published firmware
python3 scripts/verify_partitions.py nflasha <firmware-tree>/0700_part_image/dev/
```

> ⚠️ **Safety**: `updatershell` is a raw shell into the updater firmware. We only
> used *read-only* commands (`pull`). You can brick a camera by writing to the
> wrong region — don't write anything unless you know exactly what you're doing.

---

## Tools & credits

- [Sony-PMCA-RE](https://github.com/ma1co/Sony-PMCA-RE) — pmca-console, updatershell, Backup.bin parser
- [fwtool.py](https://github.com/ma1co/fwtool.py) — firmware decryption (`crypter CXD90014`)
- [OpenMemories-Tweak](https://github.com/ma1co/OpenMemories-Tweak) — the jailbreak found on the camera
- [OpenMemories website](https://openmemories.github.io/) — community project for Sony camera jailbreaks

Full credits — including the third-party apps (BetterManual, FocusBracket,
TimeLapse) recovered from the camera — are in [ACKNOWLEDGEMENTS.md](ACKNOWLEDGEMENTS.md).

> ⚠️ **Known issues**: this repo is published as-is. See
> [KNOWN_ISSUES.md](KNOWN_ISSUES.md) for the unfixed bugs (e.g. `carve_fat16.py`
> emits garbage filenames in some stale `/local` subdirectories), the caveats,
> and the future-work list.

---

## License

Documentation and scripts in this repository: **MIT** (see [LICENSE](LICENSE)).
Sony firmware and third-party apps referenced here remain property of their
respective owners. **No copyrighted firmware binaries are distributed in this repo.**

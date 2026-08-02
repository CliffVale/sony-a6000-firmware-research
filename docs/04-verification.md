# 04 — Verification: The Dump Matches the Published Firmware

> **Question**: is the firmware Sony publishes *the same* firmware Sony flashes?

> **Answer**: yes — proven byte-for-byte on all 5 published partitions.

## 4.1 Method

The published firmware tree (`0700_part_image/dev/nflashaN`) contains 5
partitions. The raw dump (`nflasha`, 483 MB) should contain the same bytes at
their expected offsets. We:

1. **Located** each published partition inside the raw dump (searching for its
   header at sector-aligned offsets).
2. **Compared** every byte of each partition against the dump slice.
3. Recorded `diff_bytes` — the count of differing bytes (0 = identical).

Reference script: [`scripts/verify_partitions.py`](../scripts/verify_partitions.py)

## 4.2 Results

| Partition | Offset in dump | Size | Bytes compared | Diff |
|---|---|---|---|---|
| nflasha3 | `0x01340000` | 10.96 MB | 11,493,888 | **0** ✅ |
| nflasha5 | `0x03b40000` | 40.30 MB | 42,254,336 | **0** ✅ |
| nflasha7 | `0x07c40000` | 3.17 MB | 3,326,976 | **0** ✅ |
| nflasha15 | `0x08b40000` | 80.15 MB | 84,044,288 | **0** ✅ |
| nflasha16 | `0x0ef40000` | 56.28 MB | 59,018,240 | **0** ✅ |

All offsets are sector-aligned (multiples of 512 B) and fall inside the dump.

## 4.3 What this means

- **Ground truth confirmed**: the camera's flashed FW 3.21 == Sony's published
  FW 3.21. (The camera's UI reported 3.21 before the dump.)
- **The region map is anchored**: because the published partitions match at
  known offsets, everything *else* in the dump (bootloader, gaps, Android
  userdata) is a real, meaningful region — not corruption or misalignment.
- **The dump is trustworthy**: if the partitions hadn't matched, we'd know the
  dump was somehow mangled before trusting any analysis on it.

## 4.4 Caveats

- Only the 5 *published* partitions can be verified this way. The bootloader
  and Android userdata have no published counterpart — they're analyzed on
  their own terms in [05](05-region-map.md) and [06](06-android-userdata.md).
- Verification was performed on **one** camera at FW 3.21. Other units/firmware
  versions may differ (e.g., region-specific builds).

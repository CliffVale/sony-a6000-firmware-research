# 05 — Region Map of the 483 MB Raw Dump

The annotated layout of `nflasha` (483 MB), based on byte-level analysis.
Erased NAND reads as `0xFF` — we used runs of `0xFF` to find real data regions.

## 5.1 The map

| Region | Start offset | Size | Content |
|---|---|---|---|
| **Boot / header** | `0x00000000` | 19.25 MB | Bootloader + 2× FAT filesystems (updater OS: `VMLINUX.BIN`, `INITRD.IMG`, busybox) |
| **nflasha3** | `0x01340000` | 10.96 MB | TPZL partition (verified, see [04](04-verification.md)) |
| gap | `0x01e34f10` | 29.04 MB | erased NAND (`0xFF`) |
| **nflasha5** | `0x03b40000` | 40.30 MB | TPZL partition (verified) |
| gap | `0x0638da35` | 24.70 MB | erased NAND |
| **nflasha7** | `0x07c40000` | 3.17 MB | TPZL partition (verified) |
| gap | `0x07f6ba4f` | 11.83 MB | erased NAND |
| **nflasha15** | `0x08b40000` | 80.15 MB | TPZL partition (verified) |
| gap | `0x0db664e1` | 19.85 MB | erased NAND |
| **nflasha16** | `0x0ef40000` | 56.28 MB | TPZL partition (verified) |
| **Android userdata** | `0x14200000` | ~100 MB | **FAT16 filesystem** — the camera's Android `/data` (see [06](06-android-userdata.md)) |
| trailing | `0x1a5c0000+` | 187.47 MB | erased NAND + extra FAT areas |

## 5.2 Notes

- **~86% of the dump is erased NAND** (`0xFF`). That's expected: the published
  firmware is ~200 MB total, spread across a 483 MB flash with generous gaps.
- The **boot/header region** contains not one but **two FAT filesystems** — this
  is the updater OS (Linux kernel + initramfs + busybox) used by Sony's own
  update procedure. The same content appears in `updater.img` from Phase 1.
- The **Android userdata at `0x14200000`** is the standout: a live FAT16
  filesystem with the camera's runtime state, not a firmware partition at all.
  Full analysis in [06](06-android-userdata.md).
- Region boundaries (gap edges) were detected as transitions between `0xFF`
  runs and non-erased data; exact edge offsets may vary by ±1 sector.

## 5.3 Reproduce the map

```bash
python3 scripts/map_regions.py nflasha
```

This finds non-erased runs, reports start/end/size, and flags known partitions
by offset.

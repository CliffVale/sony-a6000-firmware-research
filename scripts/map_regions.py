#!/usr/bin/env python3
"""Map the non-erased regions of a raw nflasha dump.

Erased NAND reads as 0xFF. This script scans the dump sector-by-sector,
groups consecutive non-erased sectors into regions, and prints a table with
offsets, sizes, and a guess at each region's identity based on known
partition offsets (from docs/05-region-map.md).

Usage:
    python3 map_regions.py nflasha [--min-size 256K] [--json out.json]

Notes:
    * A sector counts as "erased" only if ALL its bytes are 0xFF.
    * Partial sectors at region edges are common (FAT/TPZL headers land in
      the middle of a sector); boundaries are reported at sector granularity.
"""

import argparse
import json
import sys

SECTOR = 512

# Known partition starts from the A6000 region map (docs/05-region-map.md)
KNOWN = [
    (0x00000000, "boot/header (bootloader + 2x FAT updater OS)"),
    (0x01340000, "nflasha3"),
    (0x03B40000, "nflasha5"),
    (0x07C40000, "nflasha7"),
    (0x08B40000, "nflasha15"),
    (0x0EF40000, "nflasha16"),
    (0x14200000, "Android userdata (FAT16)"),
]


def human(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.2f} {unit}" if unit != "B" else f"{n} B"
        n /= 1024
    return f"{n} GB"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dump", help="raw nflasha dump file")
    ap.add_argument("--min-size", default="256K", help="min region size to report (e.g. 1M, 256K; default 256K)")
    ap.add_argument("--json", metavar="FILE", help="also write regions as JSON")
    args = ap.parse_args()

    min_bytes = int(float(args.min_size.rstrip("KkMmGg")) * (
        1024 if "K" in args.min_size.upper() else
        1024**2 if "M" in args.min_size.upper() else
        1024**3 if "G" in args.min_size.upper() else 1
    ))

    with open(args.dump, "rb") as f:
        data = f.read()
    total = len(data)
    print(f"dump: {args.dump} ({human(total)})")

    # find erased / non-erased sector runs
    regions = []
    start = None
    for off in range(0, total, SECTOR):
        sector = data[off : off + SECTOR]
        erased = sector == b"\xff" * len(sector)
        if not erased and start is None:
            start = off
        elif erased and start is not None:
            regions.append((start, off))
            start = None
    if start is not None:
        regions.append((start, total))

    # label regions against known partitions
    rows = []
    for rstart, rend in regions:
        size = rend - rstart
        label = "erased NAND" if size == 0 else "?"
        # match known partition starts inside this region (even if tiny)
        for koff, kname in KNOWN:
            if koff < rstart or koff >= rend:
                continue
            label = kname + (f" (+0x{rstart-koff:x} lead)" if rstart < koff else "")
            break
        # suppress erased runs and small unknown regions
        if size < min_bytes and label == "?":
            continue
        rows.append({"start": hex(rstart), "end": hex(rend),
                     "size": human(size), "bytes": size, "label": label})
        print(f"  0x{rstart:08x} - 0x{rend:08x}  {human(size):>10s}  {label}")

    erased = sum(r[1] - r[0] for r in regions if False)  # placeholder
    pct = 100 * (1 - sum(r[1] - r[0] for r in regions) / total)
    print(f"\n{len(rows)} regions reported; {pct:.1f}% of dump is erased NAND (0xFF)")

    if args.json:
        with open(args.json, "w") as f:
            json.dump(rows, f, indent=2)
        print(f"wrote {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

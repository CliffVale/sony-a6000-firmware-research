#!/usr/bin/env python3
"""Verify that partitions from the published firmware exist byte-identically
in a raw nflasha dump.

Usage:
    python3 verify_partitions.py nflasha <published_partitions_dir> [--show]

The published partitions directory is the `0700_part_image/dev/` folder from
fwtool.py's unpacked firmware tree, containing files named nflasha3, nflasha5,
nflasha7, nflasha15, nflasha16 (and possibly nflasha1, etc.).

For each published partition:
  1. Locate it in the dump by searching for its first 16 bytes at
     sector-aligned offsets.
  2. Byte-compare the full partition against the dump slice.
  3. Report offset, size, and diff count (0 == byte-identical).

Exit code is 0 iff every partition was found and is byte-identical.
"""

import argparse
import os
import sys


def find_partition(dump: bytes, header: bytes) -> int | None:
    """Return the sector-aligned offset of `header` in `dump`, or None."""
    sector = 512
    pos = 0
    end = len(dump) - len(header)
    while pos <= end:
        if dump[pos : pos + len(header)] == header:
            return pos
        pos += sector
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dump", help="path to the raw nflasha dump")
    ap.add_argument(
        "partitions_dir",
        help="dir containing published partitions (nflashaN files)",
    )
    ap.add_argument("--show", action="store_true", help="also print first 64 bytes of each partition")
    args = ap.parse_args()

    with open(args.dump, "rb") as f:
        dump = f.read()
    print(f"dump: {args.dump} ({len(dump) / 1048576:.1f} MB)")

    parts = sorted(
        f for f in os.listdir(args.partitions_dir) if f.startswith("nflasha")
    )
    if not parts:
        print(f"no nflasha* files found in {args.partitions_dir}")
        return 1

    ok = True
    for name in parts:
        path = os.path.join(args.partitions_dir, name)
        with open(path, "rb") as f:
            part = f.read()
        header = part[:16]
        off = find_partition(dump, header)
        if off is None:
            print(f"  {name:12s} NOT FOUND in dump")
            ok = False
            continue

        slice_ = dump[off : off + len(part)]
        diff = sum(1 for a, b in zip(slice_, part) if a != b)
        truncated = len(slice_) < len(part)
        status = "BYTE-IDENTICAL" if (diff == 0 and not truncated) else "MISMATCH"
        if status != "BYTE-IDENTICAL":
            ok = False

        print(
            f"  {name:12s} @ 0x{off:08x}  {len(part)/1048576:6.2f} MB  "
            f"diff_bytes={diff}{'  (truncated!)' if truncated else ''}  {status}"
        )
        if args.show:
            print(f"             header: {part[:64].hex()}")

    print()
    print("RESULT:", "ALL PARTITIONS VERIFIED" if ok else "FAILURES FOUND")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

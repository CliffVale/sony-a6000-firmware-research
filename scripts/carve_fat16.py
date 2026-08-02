#!/usr/bin/env python3
"""Carve the Android userdata FAT16 filesystem out of a raw nflasha dump.

The ILCE-6000 stores its Android /data in a FAT16 filesystem located at
offset 0x14200000 in the raw NAND dump (see docs/05-region-map.md).

Usage:
    python3 carve_fat16.py nflasha [--offset 0x14200000] [--dump OUTDIR]

Without --dump, prints the filesystem parameters and a directory tree.
With --dump, extracts every file into OUTDIR using the short (8.3) names
as stored on disk (subdirectories recreated).

Filesystem parameters (sector size, cluster size, FAT count, reserved
sectors, FAT size, root entries) are read from the FAT16 boot sector itself,
so the script works on any FAT16 image, not just this camera's.
"""

import argparse
import os
import struct
import sys

# Default offset of the Android userdata partition in the A6000 raw dump
DEFAULT_OFFSET = 0x14200000

EOC = 0xFFF8  # first "end of chain" cluster value (0xFFF8..0xFFFF)
BAD = 0xFFF7


class Fat16:
    def __init__(self, raw: bytes, base: int):
        self.raw = raw
        self.base = base
        bs = raw[base : base + 512]
        if len(bs) < 512:
            raise ValueError(f"offset 0x{base:x} out of range")
        self.bps = struct.unpack_from("<H", bs, 0x0B)[0]      # bytes per sector
        self.spc = bs[0x0D]                                   # sectors per cluster
        self.rsvd = struct.unpack_from("<H", bs, 0x0E)[0]     # reserved sectors
        self.nfats = bs[0x10]                                 # FAT copies
        self.root_entries = struct.unpack_from("<H", bs, 0x11)[0]
        self.fat_sz16 = struct.unpack_from("<H", bs, 0x16)[0]  # sectors per FAT

        if self.bps != 512 or self.spc == 0 or self.nfats == 0:
            raise ValueError(
                f"not a FAT16 boot sector at 0x{base:x} "
                f"(bps={self.bps} spc={self.spc} fats={self.nfats})"
            )

        self.fat_off = base + self.rsvd * self.bps
        self.root_off = base + (self.rsvd + self.nfats * self.fat_sz16) * self.bps
        # data area starts at the first cluster boundary after the root dir
        root_end = self.root_off + self.root_entries * 32
        self.data_off = base + (
            ((root_end - base) + self.spc * self.bps - 1) // (self.spc * self.bps)
        ) * (self.spc * self.bps)
        self.first_data_sector = (self.data_off - base) // self.bps

    def cluster_off(self, cluster: int) -> int:
        return self.data_off + (cluster - 2) * self.spc * self.bps

    def next_cluster(self, cluster: int) -> int:
        return struct.unpack_from("<H", self.raw, self.fat_off + cluster * 2)[0]

    def chain(self, cluster: int):
        """Yield cluster numbers following the FAT chain until EOC."""
        seen = set()
        cl = cluster
        while 2 <= cl < EOC and cl != BAD and cl not in seen:
            seen.add(cl)
            yield cl
            cl = self.next_cluster(cl)

    def read_chain(self, cluster: int) -> bytes:
        return b"".join(
            self.raw[self.cluster_off(c) : self.cluster_off(c) + self.spc * self.bps]
            for c in self.chain(cluster)
        )

    def short_name(self, ent: bytes) -> str:
        name = ent[0:8].decode("latin1").rstrip(" ").replace("\x05", "\xe5")
        ext = ent[8:11].decode("latin1").rstrip(" ")
        return f"{name}.{ext}" if ext else name

    def entries(self, cluster: int | None):
        """Yield (name, attr, size, start_cluster) for a directory.

        cluster=None reads the fixed root directory area (FAT16 root dir is
        NOT a cluster chain); otherwise walks the cluster chain. Long file
        names (LFN) are decoded and take precedence over the 8.3 short name.
        """
        if cluster is None:
            chunk = self.raw[self.root_off : self.root_off + self.root_entries * 32]
        else:
            chunk = self.read_chain(cluster)
        lfn_parts: list[bytes] = []  # LFN fragments, decoded bottom-up
        for i in range(0, len(chunk), 32):
            ent = chunk[i : i + 32]
            if ent[0] in (0x00, 0xE5):
                lfn_parts = []
                continue  # end marker / deleted
            if ent[0x0B] == 0x0F:
                # Long File Name entry: 13 UTF-16 chars, sequence in ent[0]
                chars = ent[1:11] + ent[14:26] + ent[28:32]
                try:
                    part = chars.decode("utf-16-le").rstrip("\x00\uffff")
                except UnicodeDecodeError:
                    part = ""
                lfn_parts.insert(0, part)  # LFNs are stored in reverse order
                continue
            name = self.short_name(ent)
            lfn = "".join(lfn_parts).rstrip("\x00\uffff")
            lfn_parts = []
            if lfn and not lfn.startswith("."):
                name = lfn
            if name in (".", ".."):
                continue
            attr = ent[0x0B]
            start = struct.unpack_from("<H", ent, 0x1A)[0]
            size = struct.unpack_from("<I", ent, 0x1C)[0]
            # sanity: skip stale/partially-erased entries
            if size == 0xFFFFFFFF and not (attr & 0x10):
                continue
            if any(ord(c) < 0x20 or ord(c) == 0x7F for c in name):
                continue
            yield name, attr, size, start

    def walk(self, cluster: int | None, prefix: str, depth: int, on_entry):
        for name, attr, size, start in self.entries(cluster):
            path = f"{prefix}/{name}" if prefix else f"/{name}"
            if attr & 0x10:
                on_entry("DIR ", path, 0)
                if depth > 0:
                    self.walk(start, path, depth - 1, on_entry)
            else:
                on_entry("FILE", path, size)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("image", help="raw nflasha dump file")
    ap.add_argument("--offset", default=hex(DEFAULT_OFFSET), help="userdata offset (default 0x14200000)")
    ap.add_argument("--outdir", metavar="OUTDIR", help="extract files to OUTDIR")
    ap.add_argument("--depth", type=int, default=3, help="directory recursion depth for tree (default 3)")
    args = ap.parse_args()

    with open(args.image, "rb") as f:
        raw = f.read()
    base = int(args.offset, 0)
    fs = Fat16(raw, base)

    print(f"FAT16 @ 0x{base:x}")
    print(f"  bps={fs.bps} spc={fs.spc} fats={fs.nfats} rsvd={fs.rsvd} "
          f"fat_sz16={fs.fat_sz16} root_entries={fs.root_entries}")
    print(f"  FAT table @ 0x{fs.fat_off:x}, root dir @ 0x{fs.root_off:x}, "
          f"data @ 0x{fs.data_off:x}")

    entries = []
    fs.walk(None, "", args.depth, lambda k, p, s: entries.append((k, p, s)))

    print(f"\n{len(entries)} entries:")
    for kind, path, size in entries:
        print(f"  {kind} {path}" + (f"  ({size} B)" if kind == "FILE" else ""))

    if args.outdir:
        os.makedirs(args.outdir, exist_ok=True)
        saved = 0
        for kind, path, size in entries:
            if kind != "FILE" or size == 0:
                continue
            # re-locate the entry's start cluster by walking its parent dir
            parent = os.path.dirname(path)
            name = os.path.basename(path)
            start = _find_cluster(fs, parent, name)
            if start is None:
                print(f"  !! could not locate {path}, skipping")
                continue
            data = fs.read_chain(start)[:size]
            out_path = os.path.join(args.outdir, path.lstrip("/"))
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, "wb") as f:
                f.write(data)
            saved += 1
        print(f"\nextracted {saved} files to {args.outdir}")
    return 0


def _find_cluster(fs: Fat16, parent: str, name: str) -> int | None:
    """Find the start cluster of `name` inside directory `parent`."""
    # walk from root, descending one component at a time
    def resolve(cluster: int | None, components: list[str]) -> int | None:
        if not components:
            return cluster
        head, rest = components[0], components[1:]
        for n, attr, size, start in fs.entries(cluster):
            if n == head:
                if not (attr & 0x10) and rest:
                    return None
                return resolve(start, rest)
        return None

    comps = [c for c in parent.split("/") if c]
    parent_cluster = resolve(None, comps) if comps else None
    if parent_cluster is None and comps:
        return None
    for n, attr, size, start in fs.entries(parent_cluster):
        if n == name and not (attr & 0x10):
            return start
    return None


if __name__ == "__main__":
    sys.exit(main())

# 01 — Project Overview

## What this is

A complete, documented reverse-engineering pass over the firmware of a consumer
mirrorless camera — the **Sony ILCE-6000 (A6000)**, firmware **3.21**.

Two distinct artifacts were produced:

1. **The published firmware, decrypted** — Sony ships `Update_ILCE6000V321.exe`
   (Windows) and `.dmg` (macOS). The `.dat` payload was extracted and decrypted
   with `fwtool.py` (crypter `CXD90014`) into a full firmware tree.

2. **The camera's actual NAND, dumped** — via `pmca-console updatershell`, the
   full `nflasha` device (483 MB) was pulled off the live camera over USB.
   This is a **raw, byte-level** image of the flash, including regions the
   published firmware never ships (bootloader, Android userdata, settings).

## Goals

- Preserve the camera's firmware and runtime state for future research.
- Document a **reproducible, non-destructive** dump route for CXD90014 cameras.
- Verify that the published firmware matches what's actually flashed.
- Discover and catalog what's really inside the flash (spoiler: Android).

## Scope & non-goals

| In scope | Out of scope |
|---|---|
| Reading the firmware & flash (read-only) | Writing/modifying the camera |
| Documenting the region map | Defeating encryption (CXD90014 isn't signed — no need) |
| Extracting data from the dump | Reverse-engineering Sony's Android apps |
| Verification against published firmware | Distributing Sony firmware binaries |

## What is public vs. private

This repository is **findings and methodology only**:

- ✅ **Public**: write-ups, region map, scripts, verification results, hashes of
  the *published* partitions.
- 🔒 **Private** (separate repo, not linked here): the raw `nflasha` dump, the
  decrypted firmware tree, the camera's personal data (Wi-Fi configs, backups,
  serial-adjacent identifiers), and the recovered APKs.

**Why:** Sony's firmware is proprietary — redistributing it publicly is both
legally risky and unnecessary, since anyone with the same camera model can
download the official updater themselves and reproduce Phase 1. The raw dump
additionally contains *personal* data (device name, Wi-Fi supplicant config,
usage counters), which should never be public.

## The camera

| Property | Value |
|---|---|
| Model | Sony ILCE-6000 (A6000) |
| Firmware | 3.21 |
| SoC | Qualcomm CXD90014 |
| USB (normal) | `054c:07c4` (MSC/PTP) |
| USB (updater) | `054c:03e2` |
| Internal storage | `nflasha` (483 MB raw NAND) + bootloader region |
| Runtime | Android (userdata = FAT16 @ `0x14200000`) |

## How to read this repo

1. [02 — Phase 1: unpacking](02-phase1-unpacking.md) — no camera needed
2. [03 — Phase 2: raw dump](03-phase2-raw-dump.md) — the fun part
3. [04 — Verification](04-verification.md) — proof it all lines up
4. [05 — Region map](05-region-map.md) — the annotated flash layout
5. [06 — Android userdata](06-android-userdata.md) — the surprise discovery

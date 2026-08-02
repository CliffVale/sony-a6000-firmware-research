# 03 — Phase 2: Raw NAND Dump via Updatershell

> **Goal**: pull the camera's actual flash over USB, non-destructively.

## 3.1 Why this works

The A6000's SoC (CXD90014) has no enforced signature check on its updater
firmware. Sony's updater mode exposes a **raw shell** (`updatershell`) with
filesystem-level access to the camera's devices — including `/dev/nflasha`,
the raw NAND block device. The [Sony-PMCA-RE](https://github.com/ma1co/Sony-PMCA-RE)
project implements the host side of this protocol.

## 3.2 Requirements

- Sony ILCE-6000 (any CXD90014 Sony camera should work similarly)
- USB cable (camera's micro-USB port)
- `pmca-console` from Sony-PMCA-RE
- **Fully charged battery** (dump takes several minutes)

## 3.3 Procedure

**1. Install pmca-console:**

```bash
pip install git+https://github.com/ma1co/Sony-PMCA-RE
# or: cd Sony-PMCA-RE && pip install -r requirements.txt
```

**2. Connect the camera, enter updater shell:**

```bash
pmca-console updatershell -m ILCE-6000
```

**⚠️ The critical gotcha:** after the USB connection handshake, the camera's
LCD shows:

```
Reset device OK (boxed)
```

This is Sony's standard "are you sure you want to enter updater mode?"
confirmation — **not** a factory reset. You MUST physically press **OK** on the
camera within a short window. Without it, `updatershell` hangs and eventually
times out with `Operation timed out` (~5 minutes wasted).

> We initially hit exactly this. First attempt timed out; the second attempt
> succeeded within seconds of pressing OK. Documenting so you don't repeat it.

**3. Pull the flash (read-only):**

Inside the updater shell:

```
# Raw NAND (483 MB) — the whole flash
pull /dev/nflasha  nflasha

# Bootloader region (96 KB)
pull /dev/bootloader  boot1

# There is also a boot5 (256 KB); boot2/boot3/boot4 are empty (normal)
pull /dev/bootloader  boot5   # after navigating to the right slot, or via a second pull

quit
```

> We only ever used **read-only** commands. `updatershell` can also write
> (`push` / firmware update commands) — writing to the wrong region **will brick
> the camera**. Do not experiment.

## 3.4 Result

```
nflasha   483 MB   sha256 23a3364ec17d1fc7bed7a0a0bb8e5ba19f048c0c59f2645a4e8bb40d43914049
boot1      96 KB   sha256 f9d64802e65f735883680a545b0c648ea775c68c2e2b41604c59090db4ceb594
boot5     256 KB   sha256 75b65c187bdecad8573240217aa5f55ceaddc42ccb50f82d722674ceecaee1b0
```

After `quit`, the camera returns to normal operation (MSC mode, `054c:07c4`).
The dump is **non-destructive**: no writes were made to the camera.

## 3.5 Why dump at all?

The published firmware (Phase 1) contains only the *replaceable* partitions.
A raw dump additionally captures:

- the **bootloader** (never shipped in updates)
- the **Android userdata** — the camera's live state (see [06](06-android-userdata.md))
- **settings backups** (BK1/BK2) and calibration data
- the actual **flashed vs. published** comparison baseline (see [04](04-verification.md))

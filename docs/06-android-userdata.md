# 06 — The Camera's Android Runtime (userdata discovery)

> **The surprise find.** The A6000 isn't just "a camera with Android inside"
> in some abstract sense — the raw dump contains the **live filesystem** the
> camera's Android actually runs on.

## 6.1 Discovery

At offset `0x14200000` in `nflasha` sits a **~100 MB FAT16 filesystem**.
Structure: `512 B/sector`, 4 sectors/cluster, 2 FATs, 1 reserved sector,
200 FAT sectors, 512 root entries. Filesystem parameters were read directly
from the boot sector.

This is the camera's **userdata partition** — the Android `/data`.

## 6.2 The filesystem layout

```
/data
├── DATA / SYSTEM / BACKUP / LIB / APP / PROPERTY / MISC / LOCAL / DALVIK*1
├── SECURE/            Android secure storage (system)
├── LOST_F~1/          lost+found
├── RESUME~1TXT        resume state (100 B)
└── APP/               ← installed apps (APKs)
```

Key directories:

| Path | Content |
|---|---|
| `APP/` | Installed application APKs (see below) |
| `BACKUP/` | Settings backups `BK1     BAK`, `BK2     BAK` (1.3 MB each), `PENDING/JOURNA~1TMP` |
| `LIB/` | Per-app native lib dirs — mirrors installed apps (tweak, appstore, focusbracket, bettermanual, timelapse + Sony scalar services) |
| `MISC/WIFI/` | **wpa_supplicant configs** — `WPA_SU~1CON` (734 B), `WPA_SU~2CON` (514 B) |
| `MISC/DHCP/` | dnsmasq + dhcpcd lease files |
| `MISC/BLUETO~1`, `BLUETO~2` | Bluetooth state |
| `SYSTEM/` | `BATTER~1BIN` — battery calibration (648 B) |
| `DALVIK~1/` | Dalvik cache (`*.dex`, 20–59 KB each — the apps' compiled bytecode) |
| `PROPERTY/` | Android persistent properties (`persist.*`) |

## 6.3 Installed apps (recovered APKs)

The camera's `/data/APP` directory held **5 APKs** — including the jailbreak:

| APK (8.3 name) | App | Package | Size |
|---|---|---|---|
| `COMGIT~1APK` | **OpenMemories: Tweak** | `com.github.ma1co.openmemories.tweak` | 84,606 B |
| `COMGIT~2APK` | OpenMemories: AppStore | — | 28,101 B |
| `COMOBS~1APK` | FocusBracket | `com.obsidium.focusbracket` | 15,481 B |
| `COMOBS~2APK` | BetterManual | `com.obsidium.bettermanual` | 35,848 B |
| `COMJON~1APK` | TimeLapse | `com.jonasjuffinger.timelapse` | 31,924 B |

These are the well-known **OpenMemories ecosystem** apps — Tweak is the
open-source jailbreak (by ma1co) that unlocks root-like access on these cameras;
AppStore, FocusBracket, BetterManual and TimeLapse are companion camera apps.

## 6.4 Wi-Fi supplicant (personal data — redacted here)

`MISC/WIFI/WPA_SU~2CON` confirms WPS / Wi-Fi Direct capability:

```
manufacturer=Sony Corporation
model_name=ILCE-6000
device_name=ILCE-6000_*      # user-chosen device name (truncated here)
device_type=4-0050F204-1
os_version=80000000
```

> The full configs (including a per-device UUID and any stored network
> credentials) are **personal data** and are kept only in the private archive,
> not in this repository.

## 6.5 What this tells us about Sony's architecture

1. **Modern Sony ILCs are Android devices.** The A6000 runs a full Android
   userland (system services like `com.sony.scalar.*` were visible in the data),
   with Sony's "scalar" layer providing the camera UI on top.
2. **The jailbreak ecosystem works because of this.** OpenMemories: Tweak
   running on `/data` is exactly how the community gains deeper access.
3. **The firmware update mechanism is Android-aware.** The updater OS in the
   boot region coexists with this userdata — Sony updates both the Android
   system partitions and the camera firmware through the same updater.

## 6.6 Extraction tooling

```bash
python3 scripts/carve_fat16.py nflasha            # carve the FAT16 region
python3 scripts/carve_fat16.py nflasha --dump .   # + extract every file
```

The script reads the FAT16 boot sector, walks the FAT chain, and reconstructs
files into `APP/`, `MISC/`, etc. (8.3 short names as stored on disk).

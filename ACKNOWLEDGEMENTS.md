# Acknowledgements

This research would not have been possible without the work of the
[OpenMemories](https://openmemories.github.io/) community, which reverse-engineered
the Sony Alpha ecosystem and built the tools this project builds on. All credit
for the *tools* goes to their original authors; this repository only documents
how one person used them on a single camera.

## Tools & libraries

| Tool | Author(s) | What it does | License |
|---|---|---|---|
| [Sony-PMCA-RE](https://github.com/ma1co/Sony-PMCA-RE) | Markus Maussang (ma1co) & contributors | Reverse-engineering suite for Sony PlayMemories Camera Apps: `pmca-console` USB shell, firmware unpacking, backup parsing, Android app tooling | AGPL-3.0 |
| [fwtool.py](https://github.com/ma1co/fwtool.py) | Markus Maussang (ma1co) | Extract Sony firmware updaters (`.exe`/`.dmg`) and unpack the encrypted `FirmwareData` into its `firmware.tar` / `.fdat` / `.dat` parts | GPL-3.0 |
| [OpenMemories-Tweak](https://github.com/ma1co/OpenMemories-Tweak) | Markus Maussang (ma1co) | Jailbreak / app-install toolkit for Sony Alpha cameras; enables developer mode and user app sideloading | GPL-3.0 |
| [OpenMemories-AppStore](https://github.com/ma1co/OpenMemories-AppStore) | Markus Maussang (ma1co) | Community app store / install server for OpenMemories-compatible cameras | GPL-3.0 |

## Third-party apps found on this camera

These user apps were installed on the camera (via OpenMemories-Tweak) and were
recovered from the NAND dump's Android `userdata` partition. Copyright and
credit belong to their respective authors:

| App | Author | Purpose |
|---|---|---|
| [OpenMemories-Tweak](https://github.com/ma1co/OpenMemories-Tweak) (apk) | ma1co | Camera settings tweaks & jailbreak app |
| [OpenMemories-AppStore](https://github.com/ma1co/OpenMemories-AppStore) (apk) | ma1co | App store client |
| [BetterManual](https://play.google.com/store/apps/details?id=com.obsidium.bettermanual) | obsidium | Enhanced manual-mode control app |
| [FocusBracket](https://github.com/obsidium/FocusBracket) | obsidium | Focus bracketing app |
| [TimeLapse](https://github.com/jonasjuffinger/timelapse) | Jonas Juffinger | Interval / timelapse app |

## Other references

- [OpenMemories blog](https://openmemories.github.io/blog/) — background on the
  Sony camera jailbreak and how the platform works.
- [personal-view.com forum threads on Alpha firmware dumps](https://www.personal-view.com/talks) —
  community discussions that informed the NAND dump / partition identification.

## Methodology note

Every script in this repository was written from scratch for this project
(using the OpenMemories tools as reference for file formats where noted), and
every claim in the docs was verified against the actual dump or the official
firmware files before publication.

---

*If your work is referenced here and you would like it credited differently or
removed, please open an issue.*

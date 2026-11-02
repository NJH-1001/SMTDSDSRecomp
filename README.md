# SMTDSDSRecomp

ROM-free setup/build kit for **Shin Megami Tensei: Devil Survivor (USA)**, CVIE,
revision 0. Setup compiles a private native player from your own ROM, ARM9 BIOS,
ARM7 BIOS and firmware. Public downloads contain only the original setup host,
audited framework source, configuration and licenses. No playable game binary,
Nintendo dump, generated game code, save or capture is distributed.

Windows x86-64 gameplay and an official PS5 DualSense controller have been
verified locally. The clean Windows build reproduces the independently verified
opening screen hash. macOS/Linux native compiler checks do not imply verified
gameplay, controller behavior or performance on those systems.

## Required user-provided files

No ROM, BIOS, firmware, generated game code, saves, or captures may be included
in a public release. The playable local executable also contains generated
proprietary code and must not be uploaded. A public setup/build kit must generate
it locally from each player's own legally obtained files. There are no download
links for those files.

The supported ROM is **Shin Megami Tensei - Devil Survivor (USA)**, game code
**CVIE**, revision **0**, 64 MiB. These are exact whole-file identities, measured
from the input files used by the verified local build:

| Input | Bytes | CRC-32 | SHA-1 | SHA-256 |
|---|---:|---|---|---|
| `Shin Megami Tensei - Devil Survivor (USA).nds` | 67,108,864 | `B771BBC4` | `20a16088f0f1b67a11dd93a5a1976a702f8eaef7` | `df72364a1d6aa034c227b3b7a73e4e5c1107f3437d9d1833e72db99c31266c4a` |
| `biosnds9.rom` | 4,096 | `2AB23573` | `bfaac75f101c135e32e2aaf541de6b1be4c8c62d` | `1693983a7707ae394786fa526c0552457888a51d4e410d715ef07acd5a540555` |
| `biosnds7.rom` | 16,384 | `1280F0D5` | `24f67bdea115a2c847c8813a262502ee1607b7df` | `ba65f690eb04ec92db67c0e299e21ad71de087d6d5de8a9cb17a62eaab563c17` |
| `firmware.bin` | 262,144 | `6133798D` | `ae22de59fbf3f35ccfbeacaeba6fa87ac5e7b14b` | `dda30945f375dcefa14127a4924f7c8757e56c7c2fb0b61f80302ef586a8da45` |

CRC-32 uses CRC-32/ISO-HDLC (the ZIP/zlib CRC). All three hashes cover the entire
unmodified file, including the ROM header. Filenames may differ; contents must
match. BIOS files named `bios9.bin` and `bios7.bin` are accepted by the verifier
when passed explicitly. Modified, trimmed, translated, or different-region ROMs
are unsupported. Firmware is exactly 256 KiB; other firmware revisions/settings
may hash differently and are not verified with these static banks. Keep a
pristine original; runtime state/saves belong only in the ignored local directory.

Verify your own files without copying or uploading them (Python 3.9+):

```powershell
python tools/verify_inputs.py --rom "path/to/game.nds" --bios9 "path/to/bios9.bin" --bios7 "path/to/bios7.bin" --firmware "path/to/firmware.bin"
```

The same command works in a macOS/Linux shell with `python3`. It checks size,
CRC-32, SHA-1, and SHA-256 and exits nonzero on a mismatch. Matching dumps are
necessary; this verifier is not yet a complete game installer.

## Setup

Extract the complete platform ZIP to a writable folder. Keep its `tools`,
`config`, `deps`, and `game.toml` beside `SMTDSDSRecomp-Setup`. Setup is a console
application; on macOS/Linux, run it from Terminal. Windows targets Intel/AMD
x86-64; macOS has separate Intel x86-64 and Apple Silicon arm64 builds; Linux
x86-64 is built on Ubuntu 24.04. The macOS setup hosts require macOS 15 or newer.
Builds are unsigned and macOS is not notarized.

Install **Python 3.11+**, **Git**, **CMake 3.20+**, **Ninja**, and a C/C++ compiler
and put them on PATH. Setup builds pinned SDL 3.4.10 locally unless you provide
an existing development prefix with `--prefix`.

- Windows: use an x86-64 [LLVM-MinGW](https://github.com/mstorsjo/llvm-mingw/releases)
  toolchain, with its `bin` on PATH. Python/CMake/Ninja/Git are separate tools.
  The verified local build uses Clang/LLVM-MinGW. From PowerShell set
  `$env:CC='clang'; $env:CXX='clang++'` before setup if another compiler is first.
- macOS: install Apple's Command Line Tools (`xcode-select --install`); a package
  manager can provide Python, Git, CMake and Ninja. Apple Clang is selected by
  CMake. Select the ZIP matching your CPU.
- Linux: install your distribution's C/C++ build tools, Python 3.11+, Git, CMake,
  Ninja, pkg-config, and the audio/window development headers SDL needs (for
  example ALSA/PulseAudio, X11 and/or Wayland). Setup reports SDL configuration
  failures rather than silently providing a noninteractive player.

Run the setup host without arguments for local file-path prompts, or use the
Python installer directly (substitute `python3` in macOS/Linux shells):

```powershell
python tools/install.py --rom "path/to/game.nds" --bios9 "path/to/bios9.bin" --bios7 "path/to/bios7.bin" --firmware "path/to/firmware.bin" --work "path/to/new-private-install"
```

Choose a new empty private directory **outside this source kit**. The ROM stays
in its original location. BIOS/firmware working copies, compiler output, captures,
private generated C, logs, saves and settings remain under that directory. No
private input is uploaded. First build needs internet for pinned open-source
build dependencies and can take several minutes; keep the source kit and ROM
in place after installation. Retry an interrupted build with the same command
plus `--resume`; inputs are checked again before existing build files are used.

Setup boots the real retail BIOS/firmware, observes guest-copied RAM code locally,
recompiles it with live-byte validation, and rebuilds until it reaches the accepted
bounded dirty-RAM execution ceiling. It refuses success on input/provenance errors,
terminal execution, clean-RAM rejections or a mismatching verified boot image.
No direct boot, BIOS stubs, replacement OS functions or per-game runtime patches
are used. The optional BSD-licensed FreeBIOS framework dependency is fetched and
generated locally; this game still boots using your own retail BIOS files.

Play your completed private installation:

```powershell
python tools/play.py --work "path/to/private-install"
```

Or `SMTDSDSRecomp-Setup play --work "path/to/private-install"` (add `.exe` on
Windows or `./` before the host name in a macOS/Linux terminal). Saves, settings,
mutable firmware and diagnostics live in `state/` within the private directory.
Never upload the private directory or its playable executable.

## Controls and display

WASD moves the D-pad; **I/J/K/L** map to **X/Y/B/A**; **Q/E** are DS L/R,
**Enter** is Start, and **Right Shift** is Select. Bottom-screen mouse clicks
provide touch. SDL3 gamepad support includes mapped Xbox, PlayStation and Switch
families; physical verification here covers the official Sony DualSense.
Cross/Circle/Square/Triangle map to A/B/X/Y, L1/R1 to L/R, Options to Start,
and Create to Select. PS/Guide or Escape opens settings.

Display options include screen layouts, sizing, fullscreen, swapping, borders
and custom hex colors, LCD masks and JVC/Trinitron CRT styles. GPU glow preserves
bright highlights, works independently of CRT strength, and previews on the
other screen while settings are open. Both earlier CPU glow implementations
were removed. See [display options](docs/DISPLAY_OPTIONS.md) and
[keyboard controls](docs/KEYBOARD_CONTROLS.md).

## Distribution and verification

The original setup host/installer is MIT licensed. Vendored sources keep their
own licenses; read [NOTICE](NOTICE.md). The public setup executable contains no
emulation banks or generated commercial code. The player is built privately.
[Distribution policy](PUBLIC_DISTRIBUTION.md) describes the audit boundary.
Native CI builds use original synthetic ARM input for compiler/linker checks;
no commercial ROM/BIOS/firmware enters GitHub Actions. Only audited source plus
setup hosts are package assets. Full macOS/Linux gameplay remains unverified.

# Public distribution boundary

Release destination: <https://github.com/njh-1001/SMTDSDSRecomp>.

Release preparation now includes a clean local bank-generation installer.
The original Windows proof passed. Exported-source and native CI compiler/package
checks are tracked separately; never treat a prepared job as a passing build.

Public downloads must be source/build/setup kits that require each player to
provide their own legally obtained ROM, ARM9 BIOS, ARM7 BIOS, and firmware.
A setup application may contain only original host code, appropriately licensed
dependencies, and audited source/configuration metadata. It must generate and
compile the playable game privately on the player's computer. A platform label
on an archive must not imply that its native build was tested when it was not.

Never upload or commit:

- The playable `SMTDSRecomp` executable, debug symbols, or game/firmware banks:
  these contain code generated from proprietary input files.
- ROMs, BIOS/firmware dumps, decompressed modules, captured RAM, generated game
  C, disassemblies/Ghidra projects, saves/memory cards, firmware state, screenshots,
  audio/video captures, diagnostic dumps, or archives containing those files.
- Secrets, machine configuration, toolchain caches, or local research directories.

Required identities are in `config/required-inputs.json` and the README.
`tools/verify_inputs.py` checks all four inputs locally without copying them.
CRC-32 means CRC-32/ISO-HDLC of the entire unmodified file; SHA-1 and SHA-256
also cover the entire file. Firmware settings may change a dump's checksum;
the current static firmware banks support the exact listed image only. Do not
claim arbitrary same-size firmware images are supported or distribute a patched
firmware image. No game or firmware downloads are provided.

## Clean setup design and verification (2026-11-02)

`tools/install.py` checks all four original inputs before creating a private
workspace. It builds the recompiler, generates BIOS/main-module banks from those
inputs, and builds an isolated bank producer with no pre-existing captured banks.
The producer performs real BIOS/firmware boot; guest-written RAM execution uses
the framework's existing bounded dirty-RAM interpreter exception. It uses no
discovery override, forced interpreter, direct boot or BIOS stub. The installer
captures provenance locally, generates content-validated static banks, and
rebuilds the player. Newly exposed generations are promoted locally for at most
four passes. The installer fails unless both CPUs reach the verified hardware
event and image hash, no clean-RAM execution is rejected, and final interpreted
instruction counts are at most 16 ARM9 / 1 ARM7 on the accepted startup route.

The Windows development-source proof reached 0 ARM9 / 1 ARM7 instructions,
zero clean-RAM rejections, and exact opening RGB hash
`1852d602bb0bd94e6b0334292097ba7e4d16e8c1118b985b76bdc2d19e72d586`.
An exported-source proof is a separate required artifact check. Mutable build
inputs, captures, generated C, player binaries and proof logs stay private.

Public kits contain audited source snapshots of the exact framework, ARM core
and recomp-ui repairs, preserving license notices. They contain no BIOS images
or embedded BIOS byte arrays. The optional BSD FreeBIOS framework dependency is
fetched from pinned upstream files and generated locally, as are SDL and toml++
build dependencies. The game's actual boot continues to use the user's dumps.

The original setup host is compiled natively for Windows x86-64, Linux x86-64,
macOS Intel and Apple Silicon by GitHub Actions. Full player compiler/linker
checks use original synthetic ARM loops on CI, never commercial inputs. Only
manifest-listed source plus the small original setup executable are zipped;
the generated synthetic fixture executable is not a release asset. Source
audits reject unlisted files, binary payloads, generated banks and private paths.

The firmware oracle and user-confirmed gameplay evidence remain valid for the
local build; they do not establish a clean-install release. Follow the workspace
validation policy: do not repeat campaign/multiplayer runs or create performance
matrices to satisfy packaging. Artifact and clean-install build checks are still
required. Native macOS/Linux gameplay, physical input and performance remain
unverified even when compiler/package checks pass. Record each artifact's actual
build status before publishing; never upload a private player as a substitute
for a ROM-free setup host.

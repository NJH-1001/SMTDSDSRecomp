# Notices

SMTDSDSRecomp is an unofficial project, unaffiliated with Atlus, Sega, Nintendo,
or the owners of Shin Megami Tensei: Devil Survivor. Game names identify the
user-supplied input; no game artwork, code or audio is included in public kits.

The original setup host and installer scripts are under the project MIT license.
Bundled dependencies retain their own licenses and copyright notices:

- NDSRecomp: PolyForm Noncommercial 1.0.0 (`deps/ndsrecomp/LICENSE`), with
  separately licensed components and `LICENSE-GPL`/`LICENSE-MIT` notices.
- ARM recompilation core: see `deps/ndsrecomp/external/arm-recomp-core` licenses.
- recomp-ui: MIT (`deps/recomp-ui/LICENSE`).
- Vendored melonDS: GPL-3.0-or-later; per-file notices and the framework GPL
  license text are preserved. libslirp and its glib shim retain per-file terms
  and the bundled `COPYRIGHT` file. OpenGL/xxhash components retain their terms.
- FreeBIOS: BSD-2-Clause (`deps/ndsrecomp/third_party/freebios/LICENSE.txt`).
  No BIOS image or embedded BIOS byte array is included in the public kit.
  This optional framework dependency is fetched from pinned upstream files and
  generated locally. It is not used instead of the user's retail BIOS boot.
- toml++: MIT, fetched by the pinned framework CMake helper.
- SDL3: zlib license, supplied by the player's development environment.

First build needs internet access for pinned open-source dependencies. User
ROMs, retail BIOS/firmware and generated outputs are never uploaded by setup.

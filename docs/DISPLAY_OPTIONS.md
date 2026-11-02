# Display options

Open settings with **Escape** or the controller's **PS/Guide** button.
Use Up/Down (or Tab) to select, Left/Right to adjust, Enter/Cross to open or
cycle an option, and Backspace/Circle to return. Options remains DS Start.

**Display** provides stacked, side-by-side, independent windows, top-only,
and bottom-only views. It also offers 1x–6x window sizing, fullscreen modes,
integer scaling versus an aspect-preserving fit, screen swapping, and a gap
between the screens. Large requested windows fit within the available desktop.
Swapping applies to the combined layouts. Hiding the bottom screen disables
mouse touch on that hidden screen.

**Borders** provides frame thickness (zero hides it), six color choices
(including Custom), and separate frame/background colors. For a custom color,
activate its hex row, use Delete or Ctrl+A to clear, and type `#RRGGBB`.
Enter commits, Escape cancels, and Backspace edits. Pasting is supported.
Invalid values leave the previous color intact. These settings style the
screens and surrounding canvas; the operating system owns the window chrome.

**LCD Mods** offers independent LCD scanline and pixel-grid effects, adjustable
strength, and Original, Warm LCD, and Vivid color styles. They work on host
presentation copies; they do not alter emulated memory or the game image used
by the oracle. Settings-menu text is composited after the effect to remain crisp.
Filters default to Off and color style defaults to Original.

**CRT Mods** adds JVC-style CRT and Trinitron-style CRT profiles with adjustable
strength. Selecting a CRT profile switches off the LCD mask; selecting an LCD
mask switches off CRT. The generic color-style setting applies to either.
CRT defaults to Off and uses the same saved preferences and crisp menu overlay.

**Pixel bleed** blends neighboring colors smoothly across pixel edges
(0–100, default 45). **GPU glow** adds soft colored light through SDL's hardware
renderer (0–100, default Off). It extracts bright pixels into a small 64×48
texture per physical DS screen, softens that small image with integer arithmetic,
then lets the renderer interpolate and add it over the CRT image. No glow work
is added to the enlarged 4× CPU filter. Try 40–65; zero disables it. Glow is
independent of CRT strength, so it also works with scanlines/masks at zero.
Extraction preserves small bright peaks instead of averaging thin highlights
away. Each screen is processed separately, with no afterimages.
While settings are open, glow stays visible on the other screen; only the screen
containing menu text suppresses it. Close settings to see both screens. Unsupported
or software renderers disable glow and log the reason; there is no CPU fallback.

The earlier **Phosphor glow** and **Beam glow** CPU implementations were removed
after reported gameplay slowdown and sound disruption. Their old `mods.crt_glow`
and `mods.crt_beam_glow` preferences are ignored. The replacement uses
`mods.crt_gpu_glow` and starts off, preserving CRT strength and bleed settings.

The references are MiSTer's
[JVC preset](https://github.com/MiSTer-devel/Presets_MiSTer/blob/main/Presets/Display%20Specific/JVC.ini)
and [Sony Trinitron preset](https://github.com/MiSTer-devel/Presets_MiSTer/blob/main/Presets/Display%20Specific/Sony%20Trinitron.ini).
Both combine a scaling filter, adaptive scanlines, gamma, and a mask. Our
independent approximations use a neutral staggered slot pattern for JVC and
RGB aperture-grille stripes with subtle wire lines for Trinitron, plus beam
softening and brightness-dependent scanlines. The added bleed takes
inspiration from MiSTer's
[multi-tap scaler](https://github.com/MiSTer-devel/Main_MiSTer/blob/master/video.cpp)
composition. The new glow path was informed by inspecting
[RCRness](https://github.com/NJH-1001/RCRness) at
`2b6730091cb408d798d8e65efe848cb08e1b8389` and its pinned
[CRT source](https://github.com/NJH-1001/nesrecomp/blob/a546dfef41f5aa82ef50965fc3d5d55abb8f28a2/runner/src/crt_filter.c).
That implementation uses 3× integer beam reconstruction, neighboring luma for
warm halation, a small Gaussian finishing pass, and cached aspect resampling.
Our independent implementation keeps the working DS mask/bleed and moves glow
composition into SDL's existing renderer; it is not a port of that source.
Our effects do not import MiSTer filter
tables or reproduce the FPGA scaler exactly. Integer scaling at 2x or above
helps retain the fine mask structure. The synthetic CRT preview contains no
game assets.

The design reference was
[jdgleaver/drastic_ds_shaders](https://github.com/jdgleaver/drastic_ds_shaders).
Its shader sources carry GPL notices. This implementation uses independently
written presentation effects and does not bundle or claim to reproduce those
shader ports, their NDS Phat calibration, or Natural Vision.

Settings apply during play. Layout changes recreate presentation resources
without resetting either emulated CPU. The normal `tools/run.ps1` launcher
saves preferences beside `local/runtime-settings.ini` in a `.display` file,
and restores them the next time it starts. The private game save is separate.

Verification includes focused geometry/touch tests, filter source-buffer
integrity, hex acceptance/rejection/editing tests, and scaled-menu bounds.
Glow tests verify that toggling GPU glow leaves the enlarged CPU image unchanged,
small-texture dimensions/edge handling, source integrity, and black-frame clearing.
`smtds_crt_gpu_test` checks actual accelerated additive blending using synthetic
pixels and rendered-pixel readback. It requires at least 12/255 of visible light
outside both a colored shape and a one-pixel line at glow 100, with CRT strength
zero. These checks do not establish gameplay speed.
The cartridge-free live preview verified separate and side-by-side windows,
saved-setting restoration, visible LCD grid, and border rendering.

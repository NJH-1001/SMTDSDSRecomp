# Keyboard controls

Devil Survivor defaults to the WASD profile. Open **Escape / PS → Keyboard map**
to see every active binding, or **Input → Keyboard layout** to select Classic.
The map reflects the selected profile and any explicit launcher bindings.

| DS control | WASD profile |
|---|---|
| Up / Left / Down / Right | W / A / S / D |
| A | L |
| B | K |
| X | I |
| Y | J |
| L / R shoulders | Q / E |
| Start | Enter |
| Select | Right Shift |
| Stylus | Mouse on the bottom DS screen |
| Runtime settings | Escape or controller PS/Guide |

The face-button diamond matches the DS arrangement: I (X) above K (B),
J (Y) on the left, and L (A) on the right. Settings menus use arrow keys,
Tab, Enter, and Backspace; a focused hex editor consumes its own typing.

The Classic profile retains the earlier arrow-key, Z/X/S/A, Q/W, Enter,
Backspace layout. A chosen profile is saved with the other runtime preferences.
Explicit `--keyboard-bindings` arguments take precedence on startup.

The cartridge-free `tools/verify_wasd_input.py` check injects SDL key events,
verifies their active-low DS KEYINPUT bits, and verifies release. It refuses to
run against a loaded cartridge and is not a physical keyboard hardware test.

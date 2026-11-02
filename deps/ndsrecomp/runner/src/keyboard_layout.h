#pragma once
#include "../../launcher/nds_input_bindings.h"

// Stable SDL scancodes: W S A D, L K I J, Q E, Return, Right Shift.
// The I/J/K/L diamond follows the DS: X above Y, B below A.
inline constexpr NdsButtonBindings kNdsWasdKeys = {
    26,22,4,7,15,14,12,13,20,8,40,229};
inline int nds_keyboard_profile(const NdsButtonBindings& bindings) {
    return bindings==kNdsDefaultKeys ? 0 : bindings==kNdsWasdKeys ? 1 : 2;
}

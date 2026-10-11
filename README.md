# esp32-vanvent

Home Assistant control for the **Carbest VanVent 400 × 400** roof fan
(Reimo article 318028 / 318029): fan on/off, speed 10–100 %, and the built-in
LED light, with **state kept in sync** with Home Assistant.

## Goal

| Requirement | |
|---|---|
| Fan on/off | `fan` entity |
| Fan speed 10–100 % | `fan` percentage |
| Light on/off (+ brightness/colour temp if the hardware allows) | `light` entity |
| **Two-way sync** | Touch buttons and the original remote must update HA, not just HA update the fan |
| Local only | ESPHome, no cloud |

## Why not an IR/RF blaster

Replaying the remote's codes (Broadlink etc.) is one-way: HA never learns about
touch-panel or remote presses and drifts out of sync. It stays the **fallback**
if the hardware can't be tapped.

## Approach (pick once the board is known)

1. **Sniff the panel ↔ main-board link.** If the touch panel talks to the
   motor board over UART/I²C, an ESP32 can read and inject frames — full sync,
   original panel and remote keep working. Best case (same pattern as the
   Autoterm UART in [esp32-warmduscher-autoterm](https://github.com/LeanderM99/esp32-warmduscher-autoterm)).
2. **Replace the controller.** ESP32 drives motor (PWM MOSFET or the existing
   driver's speed input) and LED directly, reads the touch panel, and decodes
   the original remote with an IR receiver / 433 MHz receiver. Full sync, more work.
3. **Fallback:** IR/RF blaster, one-way.

## Status

Hardware not opened yet. Nothing below is verified.

## Next steps

- [ ] Remote: IR or RF? (phone camera on the remote LED; RF → which frequency)
- [ ] Open the fan, photograph both sides of the main board and the touch panel
- [ ] Identify: MCU, motor type (2-wire DC vs 3-phase BLDC + driver), LED driver,
      connector/wires between panel and main board
- [ ] Measure supply voltage/current at each speed step, and the signals on the
      panel ↔ board wires (logic analyser)
- [ ] Decide approach 1 or 2, then ESPHome config

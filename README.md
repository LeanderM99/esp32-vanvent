# esp32-vanvent

Home Assistant control for the **Carbest VanVent 400 × 400** roof fan
(Reimo article 318028 / 318029): fan, lid and light, with **state kept in sync**
both ways. Same idea as the AUTOTERM bus in
[esp32-warmduscher-autoterm](https://github.com/LeanderM99/esp32-warmduscher-autoterm):
ESPHome, local only, the original touch panel keeps working.

## Goal

| Function | HA entity | Panel button |
|---|---|---|
| Fan on/off, speed 1–10 | `fan`, `speed_count: 10` | ON/OFF, FAST +, SLOW − |
| Direction in/out | `fan` direction | IN/OUT |
| Lid open/close | `cover` | to verify (remote has dedicated buttons) |
| AUTO mode | `switch` | AUTO |
| Light on/off, 3 brightness levels, 3 colour temperatures | `light` | LAMP |
| Indoor temperature, fault code | `sensor` | — |

- **Two-way sync:** a touch-panel press updates HA, an HA command updates the
  panel (LCD, backlight). The original controller stays the master wherever
  possible, so the panel stays in sync by itself.
- The original remote is **not** needed.

## What is known

Sources: the [manual](https://d2rqvrnppmk7he.cloudfront.net/pdfpool/60/90/M318028_carbest_vanvent_web.pdf)
(EN section, §5, §7, §9, §10) and photos of an installed unit with the indoor
frame lowered (wire colours confirmed). Nothing measured yet.

**Electronics location.** The outdoor (roof) unit carries the motors only. The
three motor connectors and the 12 V feed all go to the indoor trim frame, which
holds the touch panel, LCD and LED strip, so the controller is in there too.
The manual mentions a separate "mainboard" and a "button bar".

**Harness outdoor ↔ indoor** (manual §7 steps 5–6):

| Connector | Wires | Manual says | Guess, to verify |
|---|---|---|---|
| 1# 3P | green, blue, yellow | fan motor | 3 phases of a sensorless BLDC motor (3 wires, no ground) |
| 2# 2P | red, black | lifting motor | brushed DC lid motor |
| 3# 3P | green, orange, yellow | lifting motor | lid end switches or position sensor |
| bare | red (+), black (−) | vehicle power | |

**Supply** (manual §5, §6):

- 12 V nominal, 9–16 V working. Outside that range the fan refuses to run.
- "DC12V, max. 5A". The manual explicitly forbids 24 V.
- 20 W fan + 8 W light at full load. ≤ 0.25 A at speed 4, ≤ 1.6 A full load,
  ≤ 2.0 A locked rotor.

**Functions** (manual §5, §9, §10):

- Fan: speeds 0–10, reversible (IN/OUT), stops on blocked blades (anti-pinch).
- Lid: motorised with anti-pinch, plus a hand crank (knob + square shaft) as a
  manual backup.
- Light: LED strip in the trim frame. Colour temperature white → white+yellow →
  yellow (remote only), brightness 3 levels. LAMP held 3 s toggles the panel
  backlight.
- AUTO: temperature sensor in the controller. Above set point + 2 °C it opens
  the lid and exhausts; below set point − 2 °C it closes both. Set point is
  26 °C from the panel, −2…40 °C from the remote.
- Buzzer in the controller.
- Remote: paired within 20 s of power-up ("code matching") → radio, not IR.
  It has its own LCD with voltage and fault-code icons, so the link may report
  state back. Frequency and chip unknown.

## Approach

1. **Tap the button bar ↔ mainboard link** (preferred). If the button/LCD bar
   is its own board talking UART/I²C to the mainboard, the ESP32 listens and
   injects frames. The mainboard stays the master: anti-pinch, voltage guard and
   the panel display keep working unchanged.
2. **Act as the remote over radio.** No wiring into the fan at all. Works if the
   remote uses a common chip (nRF24-compatible 2.4 GHz, CC1101 sub-GHz) and the
   fan answers with its state. Then ESP32 + matching radio module, polling for
   state.
3. **Replace the controller.** ESP32 + 3-phase BLDC driver + H-bridge for the
   lid + 2-channel LED PWM + own touch input. Most work, and the anti-pinch and
   panel LCD would have to be rebuilt. Last resort.

A one-way replay of the remote stays the fallback only (HA would drift out of
sync on every panel press).

## Power

The VanVent stays on its existing 12 V feed. The ESP board takes the same 12 V.
With an 8–36 V regulator (the MORNSUN K7805-1000R3 used on the Warmduscher
board) it would also run from 24 V, so the board does not need a 24 → 12 V
stage for the fan. Whether the link needs a level shifter depends on its logic
level (3.3 V or 5 V), measured below.

## Next steps

- [ ] Open the indoor unit: photograph the mainboard and the button/LCD bar,
      both sides, chip markings legible
- [ ] Is the button bar a separate board? Connector between it and the
      mainboard: pin count, wire colours, silkscreen labels (TX/RX/SDA/SCL/VCC/GND)
- [ ] Multimeter, fan powered: voltage of each of those wires against GND,
      idle and while pressing a button → logic level, which lines idle high
- [ ] Open the remote (battery side), photograph the PCB → radio chip
- [ ] Which panel button opens/closes the lid? (manual unclear)
- [ ] Logic analyser on the link (8-ch 24 MHz + PulseView), one capture per
      button press → protocol notes, then ESPHome config

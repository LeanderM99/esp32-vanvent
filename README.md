# esp32-vanvent

Home Assistant control for the **Carbest VanVent 400 × 400** roof fan
(Reimo article 318028 / 318029): fan, lid and light, with **state kept in sync**
both ways. ESPHome, local only, the touch panel keeps working. Sister project:
[esp32-warmduscher-autoterm](https://github.com/LeanderM99/esp32-warmduscher-autoterm),
where the ESP32 replaced the original control unit and is the master on the
heater's UART bus.

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
  panel (LCD, backlight).
- The original radio remote is **not** needed. Radio is not an option for HA:
  no state back.

## Manual

[Manual](https://d2rqvrnppmk7he.cloudfront.net/pdfpool/60/90/M318028_carbest_vanvent_web.pdf),
EN section §5–§10:

- **Supply:** 12 V nominal, 9–16 V working, refuses to run outside that.
  "DC12V, max. 5A", 24 V explicitly forbidden. 20 W fan + 8 W light;
  ≤ 0.25 A at speed 4, ≤ 1.6 A full load, ≤ 2.0 A locked rotor.
- **Fan:** speeds 0–10, reversible (IN/OUT), stops on blocked blades.
- **Lid:** motorised with anti-pinch, hand crank (knob + square shaft) as backup.
- **Light:** white → white+yellow → yellow (remote only), 3 brightness levels.
  LAMP held 3 s toggles the panel backlight.
- **AUTO:** opens lid + exhausts above set point + 2 °C, closes below
  set point − 2 °C. 26 °C from the panel, −2…40 °C from the remote.
- **Remote:** paired within 20 s of power-up, has its own LCD.

## Controller board

Photos of the opened indoor frame, 2026-11. Board sticker `HY20250607-0067`.
Chip markings were not legible on the photos; roles below are inferred from
silkscreen and layout.

**One board does everything:** MCU, touch, LCD, radio, motor and LED drivers.
There is no separate button bar and no internal cable to tap. It sits in the
indoor frame, back side towards the roof.

**U2 is the only processor.** The LQFP-48 footprint U6 with its crystal Y2, SWD
header J4 and the CAN transceiver U8 are all **unfitted**: the PCB is laid out
for a second variant with an extra ARM MCU and CAN bus. In this unit the
wireless SoC U2 (24 MHz crystal, PCB antenna) runs the whole fan.
Its marking is generic (`AMM QFN40 251701`: package + date code), so the part
is deliberately unidentifiable.

**Front side** (towards the room): silkscreen `FAN-CONTRL 2025-05-17`. Segment
LCD U5 soldered on through two pin rows. The 6 buttons are coil springs that
press against the front panel, each with a backlight LED inside. The springs
are the capacitive touch electrodes. No other parts.

**Size:** 270 × 55 mm. The frame has room for up to 300 × 75 mm, but its
standoffs only fit the original outline, so a replacement board (approach B)
keeps 270 × 55 mm and the original hole pattern.

### Connectors

| Ref | Silkscreen | Goes to |
|---|---|---|
| J9 | `DC 12V`, `+` | supply, through PTC1 (polyfuse) and D2 |
| J8 | `U` `V` `W` | fan motor, 3-phase BLDC. Test pads `FG`, `BLDC_SDA`, `BLDC_SCL` next to it |
| — | `NC` `M_OUT+` `M_OUT-` | lid motor (2 wires) |
| J7 | `3V3` `GND` `HALL_1` `HALL_2` | lid position sensors. Cable has only 3 wires |
| J10 + 1 | `LED+` `LED-` | LED strip, two channels (colour temperature) |
| **J2** | `3V3` `PRG` `GND` `UTX` `URX` | **UART + boot pin of U2**, pads only, **2.0 mm pitch** |
| J4 | `3V3` `SWDIO` `SWCLK` `GND` | SWD of the unfitted U6 |
| J11 | `TOUCH_INT` `I2C_SDA` `I2C_SCL` `TOUCH_RST` | touch controller ↔ MCU, pads only |
| J5 | `CANH` `CANL` | CAN, pads only. Transceiver U8 (SOIC-8) **not fitted** |

### Chips

| Ref | Package | Role (inferred) |
|---|---|---|
| U2 | QFN-40, 24 MHz crystal Y1, PCB antenna | **the MCU**: wireless SoC, also the radio for the remote. Marked `AMM QFN40 251701`, no known part |
| U6, Y2, U8 | LQFP-48, crystal, SOIC-8 | **not fitted** (MCU + CAN variant) |
| U9 | small QFN, 6 series resistors | touch controller for the 6 buttons |
| U10 | small SMD inside milled slots | temperature sensor (slots isolate it thermally) |
| U7 | SOP-24 next to a pin row | segment-LCD driver |
| U3 | QFN next to J8 | BLDC driver, configured over I²C (`BLDC_SDA`/`BLDC_SCL`) |
| U11 | TSSOP-16, shunt R47 0.2 Ω | lid motor driver + current sense (anti-pinch) |
| U1 | SOT-23-6 + L1 10 µH | 12 V → logic buck |
| LS1 | | buzzer |

## Approach

**A. ESP32 on J2 (preferred).** J2 is U2's own UART. In the CAN variant it
probably links U2 to U6, so U2's firmware may speak a state/command protocol
there even with U6 missing. If it does, the ESP32 takes U6's place, and U2
keeps doing everything else (touch, LCD, anti-pinch, voltage guard, AUTO), so
the panel stays in sync by construction. Hardware: ESP32 + 12 V regulator +
3 wires. J2 is 3.3 V logic, so no level shifter.

New firmware on U2 is out: the chip can't be identified.

**C. Read the LCD, press the buttons** if J2 is silent. The ESP32 sniffs the
bus between U2 and the LCD driver U7 (state: speed, AUTO, direction, icons) and
"touches" the 6 springs through analog switches (virtual finger). Original
firmware stays in charge. Hacky, and light/lid state only if the LCD shows them.

**B. Replace the board** if neither A nor C works. New board with the same
outline: ESP32, BLDC driver, lid H-bridge + current sense, 2 LED PWM channels,
touch input, segment LCD, buzzer, temperature sensor. Full control, but sensorless
BLDC start, both anti-pinch functions and lid end positions become ours to rebuild.

## Power

The VanVent stays on its 12 V feed (9–16 V only). The ESP takes the same 12 V
through an 8–36 V regulator (the K7805-1000R3 from the Warmduscher board).
Do not power an ESP32 from J2's 3V3: the board's small buck is not sized for it.

## Sniffing J2

Only `UTX` (U2's output) matters for now: with U6 unfitted, nothing drives `URX`.

1. Board out, VanVent unpowered. J2 has 2.0 mm pitch, so 2.54 mm headers and
   JST XH don't fit. Solder thin wires straight into `GND` and `UTX`
   (and `URX` for later): push the stripped end through from the labelled side,
   solder on the LCD side, trim flush. Jumper wires with a female end are handy.
   Leave `3V3` and `PRG` free (PRG is a boot pin).
2. Board back in, everything plugged in, VanVent on. Multimeter: `UTX` against
   `GND` must stay ≤ 3.6 V.
3. Listen with either tool:
   - **USB-UART adapter** set to 3.3 V: adapter RX → `UTX`, GND → `GND`, then
     `python sniff.py COM5 9600` (hex + ASCII per burst, timestamped).
   - **ESP32** with [`sniffer.yaml`](sniffer.yaml): `UTX` → GPIO27, `URX` → GPIO26,
     `GND` → GND, ESP on USB. `python -m esphome run sniffer.yaml` (PowerShell),
     live log + baud selector at `http://<ip>/`.
4. Start listening **before** switching the VanVent on: boot messages come first.
5. Wrong baud shows as garbage or runs of `00`/`FF`. Try 9600, 115200, then
   2400…57600.
6. Press every panel button one at a time and note what you pressed when.
   Also leave it idle for a minute (periodic status frames?).

### J2 measurements (2026-11-14)

Running VanVent, multimeter against `GND`:

| Pin | Idle | While pressing buttons |
|---|---|---|
| `3V3` | 3.3 V | |
| `PRG` | 3.3 V | |
| `UTX` | **0 V** | 0 V |
| `URX` | 0 V | |

An active UART idles high (3.3 V). `UTX` at 0 V means U2's UART is not
running on these pads in normal operation, or the pads are not connected to U2
(they may lead only to the unfitted U6). Still open before falling back to C:

1. ~~**Boot output**~~ **done, silent:** `sniff.py` @ 115200 (FT232, RX → `UTX`),
   listener started first, then power on, LAMP pressed twice, ~30 s idle.
   **Not a single byte.** A UART at any other baud would still toggle the line
   and show up as garbage, so other baud rates were skipped: `UTX` never moves.
2. **Trace check** ([measuring points](photos/measure-j2.jpg)):
   - Multimeter, board unpowered: `UTX`–`GND` shows ~1.5 MΩ for a moment, then
     over range on 2 MΩ. No pull-up, no pull-down, no direct link to `GND`.
   - Photos ([wired](photos/back-j2-wired.jpg), [front](photos/front-lcd-touch.jpg)):
     `UTX` and `URX` each run a few mm from J2 into a via. On the LCD side a
     short bundle of traces crosses **under** the long signal bus towards the
     U6/J4 edge, and comes back up in vias right next to U6. No trace from these
     vias towards U2 is visible. Not checked for continuity; read off photos.
   - **Conclusion (photos + meter, not proven):** J2 is the UART header of the
     unfitted U6, not of U2. That explains 0 V at idle: the net floats and the
     meter pulls it to 0 V. In this unit nothing ever drives it.
3. **Bootloader** (`PRG` to `GND` at power-up): skipped. Where `PRG` goes is
   not visible on the photos, and with `UTX`/`URX` not on U2, a U2 bootloader
   would not show up on J2 anyway.

**Approach A is out for this board variant.** Next is C.

### Notes for approach C

- U7 (SOP-24, LCD driver): marking not legible under the conformal coating
  ([photo](photos/back-logic-u7.jpg)). Only **four** traces from the signal bus
  reach U7 (plus R33/C23), the other pins go to the LCD. Four lines suggest a
  serial interface (chip select, clock/write, data, …), which an ESP32 can
  sniff. Which line is which: logic analyser on those four traces while
  pressing buttons.
- Buttons: U9 reads the 6 springs and talks to U2 over J11 (`TOUCH_INT`,
  `I2C_SDA`, `I2C_SCL`, `TOUCH_RST`). Sniffing that I²C bus would give
  button events directly; injecting presses there is an alternative to
  "touching" the springs with analog switches.

## Photos

[`photos/`](photos/): both sides of the board, close-ups of U2, J2, the power
and motor section, and `measure-j2.jpg` with the J2 measuring points.

## Next steps

- [ ] Legible chip markings: U6, U2, U9, U7, U10, the QFN by J8, the TSSOP-16
      (phone macro mode, light from a flat angle)
- [ ] Front side of the board: touch pads, LCD connection (needed for B)
- [ ] J7: which of the four pins is unused?
- [ ] Which panel button opens/closes the lid?
- [x] J2: voltages (UTX idle at 0 V, see above)
- [x] J2: boot output (silent)
- [x] J2: trace check (photos + meter): J2 belongs to U6, approach A is out
- [ ] C: identify the four U7 lines and the J11 I²C traffic (logic analyser)
- [ ] Decide C or B

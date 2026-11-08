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

**Size:** 270 × 55 mm. The frame has room for up to 300 × 75 mm, but its
standoffs only fit the original outline, so a replacement board (approach B)
keeps 270 × 55 mm and the original hole pattern.

### Connectors

| Ref | Silkscreen | Goes to |
|---|---|---|
| J9 | `DC 12V`, `+` | supply, through PTC1 (polyfuse) and D2 |
| J8 | `U` `V` `W` | fan motor, 3-phase BLDC. Test pads `FG`, `BLDC_SDA` next to it |
| — | `NC` `M_OUT+` `M_OUT-` | lid motor (2 wires) |
| J7 | `3V3` `GND` `HALL_1` `HALL_2` | lid position sensors. Cable has only 3 wires |
| 2× | `LED+` `LED-` | LED strip, two channels (colour temperature) |
| **J2** | `3V3` `PRG` `GND` `UTX` `URX` | **UART + boot pin**, pads only |
| — | `GND` `SWCLK` `SWDIO` | SWD of the main MCU, pads only |
| J11 | `TOUCH_INT` `I2C_SDA` `I2C_SCL` `TOUCH_RST` | touch controller ↔ MCU, pads only |
| J5 | `CANH` `CANL` | CAN, pads only. Transceiver U8 (SOIC-8) **not fitted** |

### Chips

| Ref | Package | Role (inferred) |
|---|---|---|
| U6 | LQFP-32, crystal Y2 | main MCU (ARM, it has SWD) |
| U2 | QFN, crystal Y1, PCB antenna | 2.4 GHz radio for the remote |
| U9 | small QFN, 6 series resistors | touch controller for the 6 buttons |
| U10 | small SMD inside milled slots | temperature sensor (slots isolate it thermally) |
| U7 | SOP-24 next to a pin row | segment-LCD driver |
| — | QFN next to J8 | BLDC driver |
| — | TSSOP-16, shunt R47 0.2 Ω | lid motor driver + current sense (anti-pinch) |
| — | SOT-23-6 + L1 | 12 V → logic buck |
| LS1 | | buzzer |

## Approach

**A. ESP32 on J2 (preferred).** J2 is the UART next to the radio chip. If the
radio talks to the MCU over it, the ESP32 takes the radio's place: it sends the
remote's commands and reads the state the MCU reports (the remote's LCD
suggests it does). The original MCU keeps doing everything else (touch, LCD,
anti-pinch, voltage guard, AUTO), so the panel stays in sync by construction.
Hardware: ESP32 + 12 V regulator + 4 wires. J2 is 3.3 V logic, so no level shifter.

**B. Replace the board** if J2 carries nothing usable. New board with the same
outline: ESP32, BLDC driver, lid H-bridge + current sense, 2 LED PWM channels,
touch input, segment LCD, buzzer, temperature sensor. Full control, but sensorless
BLDC start, both anti-pinch functions and lid end positions become ours to rebuild.

## Power

The VanVent stays on its 12 V feed (9–16 V only). The ESP takes the same 12 V
through an 8–36 V regulator (the K7805-1000R3 from the Warmduscher board).
Do not power an ESP32 from J2's 3V3: the board's small buck is not sized for it.

## Sniffing J2

[`sniffer.yaml`](sniffer.yaml) listens on both J2 data lines and logs every burst
in hex. It never drives a pin.

1. VanVent powered, multimeter: J2 `UTX`, `URX`, `PRG` against `GND`.
   UTX/URX must idle at ≤ 3.6 V.
2. VanVent unpowered. Solder three thin wires onto the J2 pads from the back,
   board stays mounted. No pin header: its pins would poke through towards the
   LCD and touch side. For a quick test, pressing male jumper pins into the
   pads works too. Scrape the pad if the conformal coating stops the solder.
   `GND` → ESP GND, `UTX` → GPIO27, `URX` → GPIO26. Leave `3V3` and `PRG`
   unconnected (PRG is a boot pin). ESP powered by USB.
3. Copy `secrets.yaml.example` to `secrets.yaml`, then
   `python -m esphome run sniffer.yaml` (PowerShell, not Git Bash).
4. Open `http://<ip>/`: live log + baud selector. Wrong baud shows as garbage
   or runs of `00`/`FF`. Try 9600, then 115200, then the rest.
5. Press every panel button and every remote button, one at a time, and note
   what you pressed when. Also leave it idle for a minute (periodic status frames?).

## Next steps

- [ ] Legible chip markings: U6, U2, U9, U7, U10, the QFN by J8, the TSSOP-16
      (phone macro mode, light from a flat angle)
- [ ] Front side of the board: touch pads, LCD connection (needed for B)
- [ ] J7: which of the four pins is unused?
- [ ] Which panel button opens/closes the lid?
- [ ] J2: voltages, then sniff (above)
- [ ] Decide A or B

# AGENTS.md

ESP32/ESPHome control for a Carbest VanVent roof fan. Read `README.md` first:
it holds the goal, the candidate approaches and the open hardware questions.

- **Two-way sync is the requirement.** Radio (emulating or replaying the remote)
  is ruled out: no state back to HA.
- ESPHome builds on Windows: PowerShell only (ESP-IDF refuses Git Bash/MSYS).
- **Do not state electrical specs from memory** (voltage, current, motor type,
  pinouts). Sources are the manual (linked in the README) or measurements and
  photos; say which. The board internals are not published anywhere.
- The VanVent itself is 12 V only (9–16 V). Never wire it to 24 V.
- Public repo: no personal data, credentials, IPs or tokens.

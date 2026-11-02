# Ledger

Every design decision made through this skill. Newest first.

Read the last five before constructing a new set, and state the rotation out loud
(SKILL.md § Rotation). Write the new entry **before** building anything with the
chosen look, not after.

## Row fields

| Field | Meaning |
|---|---|
| `date` | Decision date, not build date |
| `project` | Repository or one-word project name |
| `artefact` | deck · landing · report · dashboard · diagram-set · app |
| `chosen` | Name of the winning direction |
| `axes` | ground band / display style / accent hue. Used by the rotation rule |
| `house` | Slug when this look is the standard for a recurring artefact type, else `-` |
| `artifact-url` | The bench or comparison page, if it was published |
| `moved-from` | On a bench: which preset it started from and what was changed away from it |

Under each row: palette as roles, type pairing, the one-line reason, and **the
rejected presets with why each lost**. The rejected half is the half that pays off
later.

## Tallies

Counts across all entries. Used to constrain the next choice, not for decoration.

| Ground | n | Display | n | Accent | n |
|---|---|---|---|---|---|
| light | 0 | roman serif | 0 | cool | 1 |
| mid | 1 | high-contrast serif | 0 | warm | 0 |
| dark | 0 | geometric sans | 0 | green | 0 |
| | | grotesk | 0 | neutral | 0 |
| | | condensed | 1 | | |
| | | mono | 0 | | |
| | | display-heavy | 0 | | |

Counted from **what shipped**, not from what was chosen.

---

| date | project | artefact | chosen | axes | house | artifact-url | moved-from |
|---|---|---|---|---|---|---|---|
| 2026-11-02 | robotic-jetbot | deck | Tape | mid / condensed / cool | - | https://claude.ai/artifact/7ouqyvgcrb5CUUG33WFbTV | themes, no change away from the preset |

- **Palette as roles:** ground `#DEDCD5` (lab floor grey), raise `#EFEEE9`, ink `#1B1E23`, muted `#535962`,
  accent `#1E5FA8` (the blue of our own tape), alarm `#7A2418`, categorical `#9C5120` and `#4C7A8C`.
- **Type:** Archivo Narrow 700 for display and body, IBM Plex Mono for every figure and threshold.
- **Reason:** it borrows the look of the thing being presented. The lane the robot drives in runs along the
  foot of every slide, which gives the deck its structural rule for free.
- **Rejected, with why:** *Instrument* (dark, grotesk, green) lost because the team wanted the subject in the
  look rather than a lab readout, and it is the default technical deck. *Plate* (light, display-heavy, warm)
  lost because a drafting grid needs a dense diagram at its centre and our slides are mostly runs and numbers.
- **Measured during the choice:** the first alarm red carried text at 4.4:1 and the first baseline bar fill at
  2.7:1; both were darkened before the theme was locked. Full table in `design/THEME.md`.
- **Grain:** themes, not a bench. The team asked for the big decision only, and took it in one pass.
- **Cost during the build:** to be filled in after the deck is given.

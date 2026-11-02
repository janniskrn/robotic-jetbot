# Deck theme: Tape (locked)

**Decided 2026-11-02.** Chosen by the team from three directions rendered live on two real slides at
<https://claude.ai/artifact/7ouqyvgcrb5CUUG33WFbTV> (the Deck Lab). Rejected: Instrument (dark readout, mono
figures) and Plate (drafting grid, prussian ink). **Do not re-open this decision while building the deck.** If
a value genuinely does not work on a real slide, change that one value, append an amendment below with what
changed and what it cost, and keep going.

## The idea in one line

The deck looks like the thing it is about: the speckled grey of the lab floor, and the lane the robot drives in
as two blue tape lines along the foot of every slide.

## Tokens

```css
:root{
  --ground:#DEDCD5;   /* the track floor: speckled concrete grey */
  --raise:#EFEEE9;    /* cards, one step lighter than the floor */
  --ink:#1B1E23;      /* near black, slightly cool */
  --muted:#535962;    /* second-level text */
  --faint:#767C85;    /* captions, source lines */
  --rule:#C6C4BC;     /* hairlines, empty bar tracks */
  --accent:#1E5FA8;   /* the blue of the tape on our track, measured off a camera frame */
  --accent-soft:rgba(30,95,168,.12);
  --alarm:#7A2418;    /* a failed run. Darkened from #AF3B2A, which could not carry text (4.4:1) */
  --cat-1:#9C5120;    /* baseline runs. Darkened from #C2703A, which was under the 3:1 fill floor (2.7:1) */
  --cat-2:#4C7A8C;    /* our steering without the curve model; also the tape lines in figures */
  --ok:#2F6F5E;       /* a state that runs today, in status chips */
  --display:"Archivo Narrow",Helvetica,Arial,sans-serif;  /* condensed: long state names fit a headline */
  --body:"Archivo Narrow",Helvetica,Arial,sans-serif;
  --mono:"IBM Plex Mono",ui-monospace,monospace;          /* every figure, threshold and unit */
}
```

Rotation axes, read off these tokens for the next deck: **mid ground / condensed display / cool accent**.

## Measured contrast

Target is **7:1 for anything the room has to read**, not 4.5:1, because a hall projector gives back roughly a
third of what the screen shows. Measured with WCAG relative luminance against `--ground` unless stated.

| Pair | Measured | Verdict |
| :--- | :--- | :--- |
| ink on ground | 12.2:1 | headlines and figures, passes |
| ink on card | 14.4:1 | card text, passes |
| muted on ground | 5.2:1 | second-level text only, never a headline |
| alarm on ground | 7.3:1 | failed-run figures, passes |
| accent on ground | 4.7:1 | **fills and marks only, never text at projector size** |
| accent on card | 5.6:1 | small labels on a card, acceptable |
| cat-1 fill | 4.2:1 | bar fill, above the 3:1 graphical floor |
| cat-2 fill | 3.4:1 | bar fill and tape lines, above the floor |

## Sizing

The deck uses a 16:9 container and `cqw`, so one unit means the same on a laptop, a projector and a 297 mm
page: `.slide{width:min(100vw,177.78vh);aspect-ratio:16/9;container-type:inline-size}`.

| Element | Size |
| :--- | :--- |
| headline | `4.2cqw`, max 23 characters per line |
| eyebrow | `1.15cqw` mono, letter-spacing `.2em`, at most one per three slides |
| body | `1.45cqw` |
| figure label, value | `1.12cqw` mono, tabular figures |
| source line | `1.02cqw` |

Every class sized in `cqw` needs a `body.doc` twin in `rem`, or the document mode renders a 1 cqw source line
inside a text column.

## Second surface: doc mode and print

The palette does not change between deck, document and print: the ground is already pale, so the printed page
keeps the same colours and no dark override is needed. Two rules the print block has to carry:

- `print-color-adjust: exact`, or the lane lines, bar fills and status chips disappear.
- The lane at the foot of the slide stays. It is the one decorative element, and it costs nothing in ink.

## The known weakness, accepted with the choice

Two, in the words they were offered in:

1. **The lane motif is the strongest tie to the subject and the easiest to overuse.** It holds only if it stays
   at the foot of the slide and never wraps around the type.
2. **A pale ground lights the room rather than the screen.** There is no CSS fix for that. Ask whether the hall
   can be dimmed; if it cannot, the deck is still readable, but the projector will look washed out next to a
   dark deck.

## What this is not

No gradients, no glow, no second bright colour. The blue names the subject of a slide and nothing else: no blue
headings, no blue rules, no blue bullets. The moment a second bright thing appears on a slide, the theme is gone.

## Amendments

None yet. Append dated sections here with what changed, why, and what it cost.

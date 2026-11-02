# Building the bench

One HTML file, published as an Artifact. It exists to be driven, so it loads instantly,
it never blocks on a round trip, and the thing being judged is always on screen.

## Shape

```
  Title: the thing being decided, two to four words
  Two sentences: which screen this is, why this one, and that the specimen
  does not follow the viewer's theme

  ┌─ controls ─────┬─ THE SPECIMEN ────────────────────┐
  │ presets        │                                    │
  │ ground set     │   rendered once, real content      │   sticky
  │ accent         │                                    │
  │ display face   ├────────────────────────────────────┤
  │ body face      │   meters: contrast, computed       │
  │ figures        │   failures, then costs             │
  │ layout         ├────────────────────────────────────┤
  │ form           │   the handback block + copy        │
  │ density        │                                    │
  └────────────────┴────────────────────────────────────┘
```

Controls left, specimen right and sticky so it stays in view while the control column
scrolls. Under about 1000 px, stack with the **specimen first**: on a phone the thing
being judged must be above the fold, not below nine control groups.

Use CSS grid areas so the DOM order can serve both without duplicating markup.

## The page chrome is not a candidate

`system-ui` only, neutral palette, no accent of its own. A chrome with personality gets
compared against the specimen, and the person cannot tell which one they are reacting
to. The chrome follows the viewer's light or dark theme; **the specimen never does**.
Say that in one line near the top or it reads as a bug.

## Tokens live on the specimen, not on `:root`

```js
const st = slide.style;
st.setProperty('--s-ground', g.ground);
st.setProperty('--s-ink',    g.ink);
st.setProperty('--s-accent', acc.hex);
st.setProperty('--s-display', dsp.stack);
```

Every specimen rule reads `var(--s-*)`. Structural variants (layout, label treatment,
rule weight) ride on classes: `slide.className = 'slide lay-' + S.layout + ' lbl-' + S.label`.
Nothing about the specimen is hard coded, which is also what makes the handback block
trivially correct: it prints the same values the render used.

## Option tables drive everything

Declare the options as data, generate the controls from it, and render the chips *in
the thing they select*: the font chip set in its own face, the ground chip showing a
ground-and-ink pair, the accent chip showing its swatch. A control that names a font in
the interface font teaches nothing.

```js
const GROUNDS=[
  {id:'paper', name:'Paper', band:'light',
   ground:'#FBFAF7', raise:'#FFFFFF', ink:'#14120F', muted:'#6B665D', note:'bright stock'},
  ...
];
```

Carry the rotation **band** on every colour and type option. That is what lets the cost
band flag a repeat of the last design without a second lookup table.

## Derive, do not enumerate

Neutral tints come from the ink at fixed alphas, so they follow the ground set
automatically and a dark ground does not need a second table:

```js
const tints = ink => [.88,.62,.42,.28].map(a => rgba(ink, a));
```

Same for hairlines and soft rules. The only colour that is chosen rather than derived
is the accent, which is exactly why it gets its own control.

## Compute the checks

WCAG contrast is twenty lines of arithmetic. Write them and run them on every change.

```js
const lum = h => { const [r,g,b] = hex2rgb(h).map(v => { v/=255;
  return v <= .03928 ? v/12.92 : Math.pow((v+.055)/1.055, 2.4); });
  return .2126*r + .7152*g + .0722*b; };
const contrast = (a,b) => { const l1=lum(a), l2=lum(b);
  return (Math.max(l1,l2)+.05) / (Math.min(l1,l2)+.05); };
```

RGB distance is enough to catch "this accent is one step from the brand colour we are
avoiding". Hue in degrees gives the rotation band. None of this needs a library.

Three bands, in this order: meters, then failures, then costs. Failures use the alarm
colour, costs use a quiet rule. A page where everything is red teaches nothing.

## The handback block

A `<pre>` plus one copy button. First line is the state string, then the token block
with the measured numbers in a comment. `navigator.clipboard.writeText` with a
select-the-range fallback, and a 1.6 second confirmation on the button.

## Publishing

- Favicon: one or two emoji naming the decision, for example `🎛️`.
- Title: name the thing, not the word "options". `Lidl Deck Lab` beats `Design Options`.
- Fonts from `fonts.googleapis.com` only, one request, all families, weights trimmed to
  what the controls actually offer. Everything else inline. The CSP blocks external
  images, so any photograph in a specimen travels as a data URI.
- Must still work at 400 px. Someone will open it on a phone and reply from there.
- Look at it once before publishing. The preview may render as a static snapshot, in
  which case it proves the page loaded and nothing about the controls. Run the script
  through `node --check` instead of screenshotting it repeatedly. A syntax error is the
  one failure that leaves the bench blank, and it is the one a snapshot cannot rule out.

## After the decision

Write the ledger row, including the Artifact URL, what was changed away from the
preset, and every rejected preset with one line on why it lost. Then keep the bench.
The next decision for the same person opens it instead of rebuilding it.

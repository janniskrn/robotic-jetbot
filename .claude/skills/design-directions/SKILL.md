---
name: design-directions
description: Put a look to a decision instead of picking one. Builds an Artifact at the right grain for the person deciding: three or four finished themes to click through when they want only the big decision, a gallery when the fork is binary, or an interactive bench with every choice on its own control when they want to combine and drive. Contrast is computed, not estimated, and the choice is saved or handed back as a token block. Use whenever colours, typography, palette or overall feel are being settled for a page, deck, app, dashboard, report or diagram set, and whenever someone asks for "options", "Vorschläge", "mock it up", "show me a few looks", or an Artifact to decide from. Also covers what happens after the choice: writing the decision into the repository as a locked theme file with tokens, measured contrasts, the paper or print variant and the accepted weakness, amending it on the record when the build moves something, and the categorical ramp that lets a five-part chart coexist with a one-accent rule. Carries the ledger of what was chosen before, so a new look differs from the last one on purpose rather than by accident. Says what NOT to build: no swatch grids, no prose descriptions of a feel, no single take, no control panel for somebody who asked for a theme, and no decision that lives only in an Artifact.
---

# A look is chosen by looking, and settled by trying

Not by reading an adjective, not by studying a swatch. Both of those move the decision
into the other person's imagination, where it cannot be compared. Render the **same
real screen**, put every choice on its own switch, and let the person drive.

## The rule

**Never pick the palette and the type alone.** Build the bench, hand it over, let the
person decide. A single take presented as finished is not a decision, it is a default
wearing a confident face.

Exceptions, both narrow:

- A `design.md`, `tokens.css`, brand guide or existing product already owns the look.
  Then there is nothing to choose. Follow it and say so.
- The ledger marks a **house** entry for this artefact type (§ House style).

## Match the grain of the decision to the person

The commonest failure of this skill is not a bad palette. It is asking the wrong
**size** of question. Somebody who wants to settle the look in two minutes does not
want eleven controls, and somebody with strong taste does not want three sealed
packages. Both are the same mistake, in opposite directions.

Three shapes. Pick before building, and say which you picked and why.

| | **Themes** | **Gallery** | **Bench** |
|---|---|---|---|
| Shape | Three or four complete systems, one click each | The specimen rendered two to four times | The specimen once, every choice on its own control |
| The question | "Which world?" | "Which of these?" | "What should this be?" |
| Who decides the details | You | You | Them |
| Good when | They want the big decision and nothing else, or the deadline is near | The fork is genuinely binary | They have taste, want to use it, and the answer is a combination |
| Fails when | Their taste is specific and the themes all miss it | The right answer is B's figures on A's ground | Nobody wants to drive, and twelve controls read as homework |

**Default to themes.** It is the shape that respects the other person's time, and it is
the one that most often produces a decision rather than a conversation. Escalate to the
bench when they push back on the detail, or when they change something you offered.

**How to tell which you are in.** They will say. "I do not want to decide this in that
much detail, the rest is yours" is a theme request. "Can I combine these" is a bench
request. If they have not said, offer themes and put one line at the bottom: *"If you
want to take this apart control by control, say so and I will build that instead."*

**When the grain is wrong, it is your error, not theirs.** Rebuild at the right size
and say plainly that the first one asked too much or too little. Do not keep the wrong
artefact alive next to the right one.

## When a set is rejected

A rejected set is almost no information. "Try again" is not a brief, and building a
second set from it is guessing with more effort.

**After the first rejection, ask one question before building anything:**

> Which part is wrong: the ground, the accent, or the type? Or is it the whole
> direction?

One question, three named parts, because those are the parts a person can actually feel
without being a designer. Then build once against the answer.

If a second set is genuinely needed, **change the axis of variation, not the hues.**
Four warm palettes rejected, then four cool palettes, is the same page twice. What
breaks the deadlock is varying something structural: where the colour comes from, how
much colour there is at all, whether the ground is the colour or the mark is. A set
whose members differ in *kind* gets a decision; a set whose members differ in *taste*
gets another rejection.

Record every rejected set in the ledger with whatever reason was given, including "no
reason given". The absence is itself the thing to fix next time.

## What a theme carries

A theme is a **decision, finished**. Ground, raised surface, ink, muted ink, accent,
one support colour for a second series, chart neutrals, three typefaces with weights
and tracking, rule weight, margin, headline size. Nothing left as "to be settled".

Every theme still carries a name, a thesis and its own risk, exactly as a gallery
direction does. A set of themes where all four sound good is a sales pitch.

Render each theme on **two or three real screens**, not one. A theme is judged as a
world, and one screen cannot show whether the display face survives a long title or the
accent survives being a big number. That is the one place the single-specimen rule
bends, and only because the unit of choice is the whole system.

The bench keeps everything the gallery had. Named directions survive as **presets**,
each still carrying a thesis and a risk. They are starting points, not packages.

**A theme carries its second surface too.** Almost everything gets printed, exported or
unrolled into a document, and that surface is part of the decision, not a later problem.
A dark deck needs its paper palette decided by the same person on the same day, because
the substitution is never mechanical: on the Schwarz deck the accent measures 15.4:1 on
near black and **1.3:1 on white**, so on paper the yellow survives only as a fill with a
`0.5pt` ink outline, and every piece of accent-coloured *text* becomes ink at weight 600.
Wherever the accent carried meaning rather than decoration, the paper variant needs a
non-colour encoding for that meaning: an outline, a rule weight, a font weight.

```css
body.doc .band.ax        { outline:.5pt solid var(--ink); outline-offset:-.5pt }
body.doc .ccol.hot .cbar { outline:.5pt solid var(--ink); outline-offset:-.5pt }
body.doc .sbfill.tiny    { outline:.5pt solid var(--ink) }   /* a 1 px sliver, kept visible */
body.doc .mark           { color:var(--ink); font-weight:600 }  /* was the accent, in text */
```

**And its known weakness, accepted with the choice.** The risk that was written when the
theme was offered gets copied into the theme file as an accepted cost, in the same words.
It stops the weakness being rediscovered mid-build and relitigated as a bug. Two real
ones: *"a second chart series has to be grey, which is weaker than a second colour"*, and
*"a dark deck fails outright in a bright room, and nothing in this file fixes that"*.

## When one accent is not enough

One accent is the discipline that makes a theme better than a default. Then the deck
arrives with a five-part revenue chart, and one accent plus four greys reads, in the
person's own words, as *"the grey looks bad"*. Both halves of that are true. The
resolution is not a second accent.

**A categorical ramp is a different role from an accent.** Write it into the theme as its
own set, and it stops competing with the one-accent rule:

- **The ramp names things, the accent marks the argument.** Four divisions in blue,
  terracotta, sage and violet. The fifth, the one the whole deck is about, is the accent.
- **Derive the ramp once, reuse it everywhere.** Those four hues were already on the
  ranking chart two slides earlier, so blue means the same company on both. One palette in
  the file, not two.
- **Non-subject categories are dimmed, not greyed**: same hue at `opacity:.55`. They keep
  their identity and stop shouting.
- **Nothing decorative ever takes a colour from either set.** No coloured rules, bullets or
  headings. The moment a colour appears where it names nothing, the scheme means nothing.

The one-accent rule survives all of this intact: there is still exactly one accent object
per slide, and it is still reserved for the subject of the argument.

## Order of work

1. **Read the brief.** Kind of thing, audience, room it will be seen in, subject
   matter. The subject matters more than taste: a deck about warehouses and a deck
   about a bank should not arrive at the same page.
2. **Pick the specimen** (§ Specimen). One real screen, with real content.
3. **Check the ledger** (`ledger.md`) before inventing anything. Read the last five
   entries and state the rotation out loud (§ Rotation).
4. **Decide what is a control and what is welded** (§ Controls). This is the design
   work of the bench itself.
5. **Write two to four presets.** Each gets a name, a thesis and a risk, exactly as a
   gallery direction would.
6. **Build the Artifact** with the recipe in
   [`references/artifact-recipe.md`](references/artifact-recipe.md).
7. **Hand it over with the ask**: *"Load a preset, pull it apart, send back the line
   at the bottom."*
8. **Record the outcome in the ledger before building anything else.** This step is
   not optional. A ledger that is updated when convenient is a ledger that teaches
   nothing.

## Specimen

The single screen every choice is judged on. Choose the one that is **hardest to make
look good**, not the prettiest:

| Kind of thing | Specimen |
|---|---|
| Presentation | The densest data slide, the one with the chart or the table |
| Landing page | The hero plus the first section under it, together |
| Dashboard | One real panel with real numbers, including a long label |
| Report | A page carrying a heading, running text, one table and one footnote |
| Diagram set | The diagram with the most nodes |

Real content, real numbers, real strings. Lorem ipsum hides every flaw that matters:
a headline that wraps, a figure column that will not align, a label that collides.

**One specimen.** The temptation on a bench is to add a second screen so more can be
checked. Resist it. Two screens halve the attention on each and double the build, and
the hard screen already carries every problem the easy one has.

## Controls

The judgement that makes a bench good: **bundle what is only valid together, split
what is genuinely independent.**

Ground, raised surface, ink and muted ink are **one control**. Letting someone choose
ink separately from ground produces unreadable combinations, and every second spent in
that space is wasted. Ship them as named ground sets: *Paper*, *Concrete*, *Rack*.

These are genuinely independent and each earns its own control:

| Control | Why it stands alone |
|---|---|
| **Accent** | The one colour that is a decision rather than a consequence |
| **Display face** | Carries the personality, and swaps cleanly against any ground |
| **Body face** | Different job, different constraint, often a different answer |
| **Figure face** | Tabular figures are a separate problem from running text |
| **Layout** | Where the words sit relative to the picture |
| **Density and scale** | Margin and headline size. Continuous, so a slider, not chips |
| **Form of the data** | Bar, columns, table. This is a content decision wearing a design control |

Two hard limits:

- **Every control must change something visible in the specimen.** A control whose
  effect is off screen is a lie about what is being decided.
- **Around ten control groups is the ceiling.** Past that the bench reads as homework
  and the person picks a preset to escape it.

## Presets

Two to four. Each one is a direction in the gallery sense and carries the same three
things:

- **A name.** One word, memorable, so the reply can be "Rack" and not "the dark one".
- **A thesis.** One sentence on what it borrows from and why that fits *this* subject.
  "Clean and modern" is not a thesis.
- **A risk.** What goes wrong when this one is chosen.

The thesis and the risk live in the handover message and in the ledger. The bench
itself shows the preset as a button with two words under it, because a paragraph next
to a button does not get read.

## Live checks replace the risk box

A gallery writes one risk per direction, in advance. A bench cannot: the risk belongs
to the **combination**, and there are hundreds. So compute it.

Three bands, all rendered under the specimen and updated on every change:

**Meters.** Contrast of ink on ground, muted on ground, accent on ground, as numbers.
Computed, never estimated. For a deck, 7:1 is the target for the headline and not
4.5:1, because a hall projector gives back roughly a third of what the screen shows.

**Failures.** Contrast below the floor. An accent that cannot carry a word. A missing
accent when the chart depends on one to make its point. Phrased as what breaks, not as
a caution.

**Costs.** True statements about the current combination that are not failures:

> **Dark plus grotesk plus mono.** That is the default technical look, the one a deck
> arrives at when nobody decided anything. It works, but only held flat.

This band is where the ledger becomes live. When the current combination repeats the
axes of the last recorded design, say so on the page, at the moment it happens. That
is worth more than a rotation sentence in a handover nobody rereads.

Never hedge. *"May be perceived as slightly informal in some contexts"* is not a risk,
and the reader will skip it and everything under it.

## The handback

A bench is worthless if the state cannot come back. Every bench ends with a block that
is copyable in one click and carries both halves:

- **One line of state.** `lab: ground=concrete accent=signal display=barlowc ...`
  Enough to reproduce the screen exactly.
- **The token block.** Real CSS custom properties, real font stacks with fallbacks,
  ready to paste into the build.

Comment the measured numbers into the block. Six months later the hex values are
recoverable and the reason they passed is not.

Persist state in `localStorage`, wrapped in try/catch, so a closed tab does not throw
away twenty minutes of fiddling.

## After the decision

The Artifact settles the look. It does not survive the build: an artifact URL is a page
somebody has to open, and a build that is three days and two sessions long will quietly
drift away from it. **Write the decision into the repository, next to the thing being
built**, on the day it is made. One file, for example `design/THEME.md`. The skill's author kept one this way through a
three-day build and three correction rounds.

What that file carries, in this order:

1. **A lock line.** *"Decided 2026-09-16. Chosen from the third set on `<artifact URL>`,
   rendered live on three real slides. Do not re-open this decision while building. If
   something in it genuinely does not work on a real slide, change that one value, write
   down what changed and why, and keep going."* This sentence is the entire point of the
   file. It converts a hundred small future decisions into either "follow it" or "amend it
   on the record".
2. **The idea in one line**, so the discipline is repeatable by someone who was not there.
   *"The founding family is called Schwarz. The palette is the name: near black, cold
   white, and exactly one yellow, the company's own, used once per slide and never
   twice."*
3. **The tokens**, as real CSS, with a comment on any value that looks arbitrary
   (`#FFE500 /* the brand yellow, deepened to cut projector bloom */`).
4. **The measured contrasts**, as a table with the target named and the reason for the
   target. A deck target of 7:1 rather than 4.5:1, because a hall projector returns about
   a third of what the monitor shows.
5. **The sizing scale**, in whatever unit the build actually uses.
6. **The second surface**: paper, doc, print, dark, whichever exists.
7. **The known weakness, accepted.**
8. **What this is not.** *"No glow, no gradient, no glassmorphism, no neon. The moment a
   second bright thing appears on a slide, the theme is gone."*

**Amend it in place, never silently deviate.** Two things moved during the Schwarz build,
and both were appended to the file as dated sections with the reason and the cost:

> **Changed 2026-09-16, correction round: the display face.** Anton is out, Libre Franklin
> 800 is in. Anton is a poster face, ultra-condensed, and its capital I looked wrong beside
> other capitals in a real headline. **What this costs, accepted with the change:** Libre
> Franklin is much wider at the same size, so every headline came down by roughly 18
> percent and headlines now wrap to two lines more often.

That is what an amendment looks like: what changed, why, and what it cost. A theme file
without amendments after a three-day build is not a clean build, it is an unmaintained
file.

**Close the loop back to the ledger.** When the build is finished, read the theme file
again and correct the ledger row from it (§ Recording). This is not bookkeeping: the
ledger's only job is to constrain the *next* look, and a row recording a typeface that was
abandoned on day one will misdirect the next rotation. It happened here. The row said
Anton and display-heavy; what shipped was Libre Franklin 800, which is a grotesk.

## Rotation

Two consecutive designs for the same person must differ on **at least one** of three
axes. Say which one, out loud, before building, and wire it into the bench's cost band
so it fires live.

| Axis | Bands |
|---|---|
| **Ground** | dark (L < 30 %) · mid (30 to 85 %) · light (> 85 %) |
| **Display type** | high-contrast serif · roman serif · geometric sans · grotesk · condensed · mono · display-heavy |
| **Accent hue** | warm (10 to 60°) · cool (200 to 300°) · green · neutral, no chromatic accent |

Format for the statement:

> *Last three: Receipt (light / mono / warm) · Plate (light / grotesk / cool) ·
> Instrument (dark / grotesk / warm). Light ground used twice. This set leads with a
> mid ground and a serif.*

**Classify the axes from what shipped, not from what was chosen.** The bands are read off
the built tokens at the end of the build, because a display face that was replaced on day
one will otherwise misdirect every rotation after it. Anton is display-heavy; the Libre
Franklin 800 that actually shipped in its place is a grotesk, and those are two different
constraints on the next deck.

On a bench, rotation does not constrain what is offered. Offer the full space and let
the repeat be flagged when it is chosen. A control the person cannot reach is a
decision taken away from them, which is the thing this skill is against.

**Do not rotate for its own sake.** Rotation stops the drift back to whatever the
model reaches for by default. It does not override a fit that is genuinely right. When
the correct answer repeats a previous axis, say why and keep it.

## House style

Some things should look the same every time: a recurring report, a series of decks for
one course, a family of internal tools. Recognition beats novelty there.

Mark those in the ledger with `house: <slug>`. A house entry:

- skips the rotation rule
- skips the Artifact on later runs
- still gets a ledger line, so drift is visible

Ask once before declaring something house: *"Should this become the standard look for
X, or is it a one-off?"* Never declare it unilaterally.

## Recording

After the choice, append to [`ledger.md`](ledger.md). One row, plus the detail block
underneath it. The fields are in that file's header.

From a bench, record **what was changed away from the preset**. That is the sharpest
signal the method produces: it is the person's taste, isolated, without a builder's
guess in the middle of it. "Started from Rack, moved to Concrete, kept the mono
figures" says more than any winning hex value.

Record the rejected presets too, one line each on why they lost. A later pass compares
against them instead of re-deriving them, and "we already tried the dark one and it
washed out in that room" is worth more six months later than a palette.

Keep the Artifact URL in the row. The bench is reusable: the next decision for the
same person starts by opening it, not by building a new one.

**The row is written twice.** Once when the choice is made, because a ledger written later
is a ledger written from memory. Once again when the build is finished, read back from the
theme file and its amendments (§ After the decision), because what shipped is what the
next rotation has to differ from. The second pass is three minutes and it is the one that
keeps the ledger true: this project's row claimed a typeface that had been dropped on the
first day of the build.

Record **what the look cost during the build**, in one line. "Zero of 24 correction items
touched the theme" is a stronger endorsement of a method than any adjective, and "every
headline had to shrink 18 percent when the display face changed" is the kind of warning
that is worth having before repeating a choice.

## Not this

- **No swatch grids.** Five rectangles of colour decide nothing.
- **No prose descriptions of a feel.** "Warm, editorial, a bit brutalist" is a brief,
  not an option.
- **No single take.** If nothing can be changed, this skill has not run.
- **No asking for detail that was not wanted.** A theme request answered with a control
  panel is the same failure as a bench request answered with three sealed packages.
- **No row of sealed packages** when the real answer is a combination.
- **No dead controls.** Every switch must move something in the specimen.
- **No second specimen.** One screen, the hard one.
- **No lorem, no placeholder numbers.** The bench exists to catch what real content
  breaks.
- **No state that vanishes on reload.**
- **No bench without a handback block.** A decision that cannot be copied out is a
  decision that gets retyped wrong.
- **No decision that lives only in an Artifact.** If it is not written into the repository
  as tokens, it will be re-decided by accident on day three.
- **No silent deviation during the build.** Change the value, write the amendment, say what
  it cost.
- **No second accent because a chart needs five colours.** That is a categorical ramp, and
  it is a different role (§ When one accent is not enough).
- **No skipping the ledger write.** It is the step that makes the skill worth having.

## Prose

Every visible string goes through `slop-prose` and `slop-tells`. No em dashes. No
banned vocabulary. The check and cost lines especially: they are where hedging creeps
in, and a hedged risk is no risk at all.

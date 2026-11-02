---
name: presentation-html
description: Build a presentation as one self-contained HTML file with a deck mode, a doc mode and a print mode that gives a PDF of either. Carries the running order, the visual directions to choose between, the sizing architecture and its doc-mode twin rule, the rules that keep numbers honest in front of a room, the reusable blocks, the static pass that checks the file without a browser, how to run a correction round, and the traps that each cost a rebuild. Use whenever a talk, slide deck, lecture, pitch, defence or conference presentation is being planned, outlined, restructured, styled, built, corrected, reviewed or published,. Also read it before picking a look for one, before a final review, and before publishing one as an Artifact. Says what NOT to build: no slide framework, no second artifact, no interaction a projector cannot use.
---

# A presentation is one HTML file

Not a framework, not a deck of images, not a PDF. One file that opens in any browser,
navigates by arrow keys in front of a room, and unrolls into a readable document for the
people who ask for it afterwards, and prints to PDF from either. Three modes over one
content tree, because a second artifact drifts from the first within a day.

**One worked example.** Read it before building anything. It is the only place the details
below exist as code.

```
examples/jetbot/        (next to this file)
  deck.template.html    vw and clamp() sizing, a canvas opening, expandable blocks
  build.py              inlines assets, checks placeholders, refuses over 16 MB
```

The example is the reference for an animated opening and for interaction. Where this file
mentions the **Schwarz** and **Omada** decks, they are earlier decks by the skill's author
that are not in this repository; only the lessons they taught are kept here. Copy blocks out
of the example. Copy neither its content, sections or subject.

## Four rules before anything else

1. **One content tree, three modes.** `body.deck` gives each `<section>` the full viewport
   with scroll-snap and projector-sized type; `body.doc` unrolls the same sections into a
   centred column; `@media print` turns whichever mode is on screen into a PDF (§ Print).
   The mode decides layout only, never palette, never which facts appear.
   `.deckonly` / `.doconly` handle the few places one mode needs a sentence the other does
   not.
2. **Every number says what it is a number of, inside the number.** A bare `380 s`,
   `15.1×` or `2028` means nothing to the room, and a caption under it does not repair
   that, because the caption is read second if at all. The unit goes in the big type:
   `200 MW`, `13 ha`, `Year 2028`. The caption then says what happened. Everything that
   can still go wrong after this rule passes is in § Numbers that survive the room.
3. **Figures standing next to each other come from the same run.** The fastest way to put
   nonsense in front of an audience is to source each panel of a slide from whichever
   measurement flatters it. One slide, one run. A figure borrowed from elsewhere says so on
   the slide.
4. **Pick one structural rule and hold it everywhere.** Client left and server right, or
   past left and future right, or problem above and answer below. Whatever it is, a slide
   that breaks it costs the audience the orientation the deck was handing them for free.

## Order of work

1. **Content before appearance.** Draw every claim from where it already lives and link,
   never copy. A deck is a view of the project, not a second source of truth for it.
2. **Get the section list approved before writing any CSS.** One line per section: what it
   says, where it comes from. Cutting three sections is cheap here and expensive later.
   Write two more things next to that list while it is cheap: **what was left out and
   why**, and **the cut order for the room**. The second one is a single line and it is
   worth an hour at the podium: *"Under time pressure, 3 folds into 2 and 13 folds into
   14, leaving 13 slides. Not cuttable: 5, 8, 11."* Deciding that while calm beats
   deciding it while talking, and the non-cuttable list is the more useful half.
3. **Offer visual directions as a comparison page, never pick alone.** Run the
   `design-directions` skill: it owns the protocol (which slide to use as the specimen,
   what each direction must carry, the rotation rule against previous decks, the ledger
   write afterwards). The table below is this skill's contribution to it: three
   directions that have carried a real deck, ready to offer or to rotate away from.
4. **Ask which form every figure takes** (§ Ask before you draw a figure). Collect the
   whole deck's figures and ask once, not eight times.
5. **Build the deck.**
6. **Prose pass over every visible string** (§ Prose).
7. **Static pass over the file** (§ The static pass). Cheap, and it catches what a
   screenshot cannot.
8. **Publish** (§ Publishing).
9. **Run the correction rounds** (§ Correction rounds). Expect three. They are not a sign
   that the build went badly; they are where the deck becomes the person's own.
10. **Walk the checklist before the talk** (§ Before the talk).
11. **Write the ledger entry after the talk** (§ What the last decks taught).

## Visual directions

Three that work, as starting points. A fourth is better when it borrows the look of the
thing being presented. That is what makes a deck feel specific rather than styled.

| | Thesis | Type | Under hall lighting |
|---|---|---|---|
| **Instrument** | The vernacular of lab equipment: dark readout, monospace figures, hairline scale ticks. The numbers are the hero. | Chivo 800 · IBM Plex Mono | Strongest, a dark ground survives a bright room |
| **Emergence** | Soft translucent blooms resolving into form; the page feels like the thing it describes. | Fraunces 600 · Karla | Weakest, a pale ground washes out |
| **Plate** | A technical manual: drafting grid, prussian ink, square status marks, figures that read as plates. Says "documented machine". | Bricolage Grotesque 800 · Azeret Mono | Good, high contrast, but a pale ground lights the room |

Risks worth naming while offering them: Instrument sits one step away from a generic dev
dashboard and needs its tick rail and tabular figures to earn its keep; Emergence turns to
decoration the moment a bloom sits *around* the type instead of behind it; Plate wants a
real diagram at its centre or the grid is empty ceremony.

Mixing is allowed and usually right: Emergence type on an Instrument status board, say.

## Palette as roles, not colours

Name every colour by what it does, then a direction is a change to one block of variables
rather than a rewrite. The set that has carried a full deck:

`--ground` `--raise` `--ink` `--muted` `--faint` `--rule` `--rule-soft` `--accent`
`--accent-soft` `--secondary` `--ok` `--warn` `--idle` `--shadow` `--step`

Three blocks, in this order, or the toggle only works in one direction:

```css
:root{ /* the complete light palette, on bare :root */ }
@media (prefers-color-scheme:dark){ :root:not([data-theme="light"]){ /* same names */ } }
:root[data-theme="dark"]{ /* same names again, so the button wins */ }
```

## Sizing: two ways, and the second is better for a deck

**`clamp()` against `vw`** serves one page to a projector and to a phone:
`h1: clamp(30px,4.9vw,66px)` · `h2: clamp(24px,3.3vw,45px)` · body `clamp(15px,1.6vw,17px)`.

**A 16:9 container plus `cqw`** is stronger as soon as the deck has to print. Give the
slide a fixed aspect ratio and make it a container, then size everything on it in `cqw`.
One percent of the slide width means the same thing on a laptop, on a projector and on a
297 mm page, so nothing needs re-tuning for print and no scale factor can disagree with
the frame:

```css
.slide{width:min(100vw,177.78vh);aspect-ratio:16/9;container-type:inline-size;overflow:hidden}
.inner{position:absolute;inset:0;padding:5cqw;display:flex;flex-direction:column;gap:2.2cqw}
h2{font-size:4.3cqw;line-height:1.07;max-width:20ch}
.src{font-size:1.0cqw}
```

**The twin rule is the trap that comes with it.** Doc mode unrolls the same markup into a
text column, where `cqw` is meaningless: a `1cqw` source line inside a 53 rem column is
unreadable, and nothing looks wrong while you are building the deck. **Every class with a
`cqw` size needs a `body.doc` rule in `rem`.** Adding a class in a correction round and
forgetting its twin is the commonest defect in this architecture. It has its own check in
§ The static pass.

Give the display font a real fallback (`"Libre Franklin",Helvetica,Arial,sans-serif`) and
cap headline widths in `ch`, measured in the page rather than guessed.

## Blocks to take, not invent

All of these exist in the template. Take what the content needs and leave the rest.

- **`.eyebrow`**: a small uppercase line above the headline that says what kind of slide
  this is. The cheapest orientation device there is.
- **`.stat`**: a large figure plus its label. Three or four across, `.stats` wraps them.
- **`.card` in `.grid.g2/.g3/.g4`**: collapses to one column under 820 px.
- **`.tag`** with `.t-ok/.t-warn/.t-idle/.t-open`: a state word inline in running text.
- **`.lanes`**: two columns with a join between them: the structural rule made visible.
  Colour the top edge of each lane to fix which side is which for the whole deck.
- **`.stagebar`**: a row of blocks whose *widths are the measured seconds*. Clicking one
  reveals its detail underneath. A bar drawn to look balanced is a lie about the process.
- **`.oschip` → `.osdetail`**: small chips that expand into one shared detail panel with a
  picture. Good for tools, dependencies, prior art. Keeps a dense slide readable.
- **`.branch` / `.bdots` / `.legend`**: a status board: one row per workstream, one square
  per package, three colours and a legend. **Arrives open**; clicking folds a branch away.
  Three collapsed bars read as an empty slide, and the detail is the point of it.
- **`.viewer`** with a poster and an explicit load button: anything heavy (a 3D model, a
  video, a map) loads on a click, never on page load.
- **`.scroller`**: the one wrapper allowed to scroll sideways, for a wide table.
- A **`<canvas>` object** behind the headline, turning slowly, if the project produces one.
  It is the strongest opening a technical talk has and it costs one file.

From the Schwarz deck, all static, all print clean, none of them needing a library:

- **`.facts`**: a four-cell row across the foot of a big-number slide. Each cell is one
  figure with its unit in the figure, plus one line of what it is. The cheapest way to
  turn a single headline number into a slide that answers the obvious follow-ups.
- **`.bleed`**: a full-slide photo behind the text, greyscaled and darkened, with a
  one-sided gradient over it so the type side stays readable and the picture side stays a
  picture. `filter:grayscale(.35) brightness(.62)` plus a `linear-gradient(100deg, …)`
  pseudo-element. In doc mode the same markup becomes a normal 13 rem banner with the
  gradient switched off.
- **`.statement`**: one short accent sentence, display face, roughly 2.6cqw. Replaces a
  bullet list when the slide has one thing to say. Needs the layout care in § The empty
  middle or it floats.
- **`.qbox` + `.ql`**: a pull quote with a thick left rule, for the honest limit of the
  argument. Every deck that makes a claim needs one slide that states what would falsify
  it, and this is where it goes.
- **`.pattern`**: a lane grid: one row per instance, one column per stage, a header row
  above. Three rows of three cells proved the argument of that whole deck. Better than a
  flowchart whenever the point is that the *same* sequence happened more than once.
- **`.flow`** with `.fstep.off`: a four-stage chain where the stages with no evidence are
  drawn as outlines instead of fills, and the arrow into them is dimmed. Showing which
  half of a model is not running is worth more than showing the model.
- **`.stack`** with `.seg.dim`: a single stacked bar where the subject segment is at full
  strength and the others are their own hue at `opacity:.55`. See § Charts that carry
  colour.
- **`.hb.ref`**: a bar drawn as an outline instead of a fill, for a reference quantity
  that is not the subject's. Used for a state budget next to a company's spending, so the
  comparison is on the same axis without implying it is the same money.
- **`.names`**: a four-by-two grid of tiles, each a customer name plus one line. The
  answer to "put the logos on a slide": plain type on a raised tile, no borrowed marks, no
  licence problem, and it reads faster than a logo wall.
- **`.tlwrap`**: a timeline with labels alternating above and below the line, that
  collapses to a two-column list of year plus text in doc mode. Compute the mark positions
  from the dates (§ Numbers that survive the room).
- **`.srclist`**: the sources slide as a two-column list, bold label, URL in a muted
  roman. Fifteen sources fit on one slide and stay readable in the report.

## Optional block: motion between slides (the stage)

Take it only when asked for. By default a deck jumps between slides, and that is enough. When
the person wants the transitions of the scroll-stage landing page (skill `scroll-stage-landing`,
`references/stage-engine.md` §3 and §9), this is the tested port, built on the Omada deck
(not in this repository; React 19 + Vite + GSAP + three.js, output `dtx-stage.html` next to `dtx-deck.html`).

**The shell reads the built deck, it never holds content.** `src/deck.ts` imports the built
`dtx-deck.html` as a raw string, lifts the `<style>` and the `<section>` blocks out of it, and
renders them with `dangerouslySetInnerHTML`. `deck.template.html` stays the one content tree, a
correction round edits it as before, and the plain deck stays as the fallback file. Rewriting
the slides in JSX would be a second artifact that drifts.

**What the stage adds, and nothing else.** A small stylesheet after the deck's own:
`body.deck.stage` stops scrolling, every section is `position:fixed; inset:0;
visibility:hidden`, and `.slide` turns transparent so a canvas behind it shows. Doc mode and
print never see the stage: `@media print` puts the sections back into the flow with
`!important` against GSAP's inline styles, hides the canvas, and both PDFs come out page for
page like those of the plain deck.

**The swap, with the landing page's timing, per key press** (one drive = 0.9 s):

| Step | Start | Duration | Move |
|---|---|---|---|
| old slide out | 0.10 s | 0.27 s | `autoAlpha 0`, `y −40px × dir` |
| new slide in | 0.45 s | 0.27 s | from `y +40px × dir` |
| its parts, staggered | +0.05 s | 0.22 s, 0.03 s apart | from `y +18px × dir` |
| bars grow | +0.16 s | 0.6 s `power3.out`, 0.08 s apart | **height** from 0 to the built value |
| 3D state | 0.08 s | 0.72 s `power3.inOut` | tween of a plain state object |

Pixel values are per 900 px of viewport height and scale with it. `dir` is −1 going back, so
backwards is the mirror image. Parts are the direct children of `.inner`, with `.head` and
`.cols` opened one level. Tween bar **height**, not `scaleY`, so the value label above the bar
rides up with it.

**Input: one step per key, one step per gesture.** Keys as in § Standing preferences. A wheel
or trackpad gesture steps once, then its momentum is swallowed until a new gesture: a pause
over 120 ms, a change of direction, or a delta ≥ 6 px and more than 2.2 × the mean of the last
six (the landing page's thresholds). Tested: 25 decaying trackpad events → one slide, three
fast mouse notches → one slide. Touch: a swipe over 50 px steps once. Scroll-scrubbing like the
landing page was offered and not chosen: a presenter wants a clicker that cannot overshoot.

**A 3D object only if it carries the argument, and a solid object is the weaker choice.** The
first build used a procedural flywheel (four rim segments for the four stages). It was correct
and it was called *"langweilig"* the next day. What replaced it: **the subject's own count as
particles**, 1,020 points for 1.02 million members, one dot per 1,000, with the scale written
on the slide where they first appear. Each slide gives the swarm a form (cloud, stream, loop,
a loop whose last three quarters sag and drop out) and every point flies to its place with its
own delay of up to 0.4 s. `stage/src/particles/Particles.ts`: CPU positions, a soft-disc point
shader, additive blending, an orthographic camera mapped to the slide, depth faked by point
size. It reads as premium where the wheel read as clip art, and it is honest by construction
because the count is a real number. Keep the object off photo slides (form `hidden`). In the
wheel version segments 2 to 4 turned into outlines, the same convention as the outlined cells on the flywheel
slide. No accent colour on the object: the accent belongs to the slide. Rules that held:

- One state per slide in a JSON file (`x`, `y`, `size` relative to the **16:9 slide**, not the
  window, so a 4:3 projector letterboxes it with the slide; `tilt`, `yaw`, `dim`, `spin`,
  `stall`, `lit`). Each entry carries a `match` phrase from its slide's text, and the build
  refuses when a phrase is missing, so a reordered deck fails at build time and not in the room.
- Bright only where the object is the subject (title, its own slide, the break, the
  conclusion). Everywhere else dim ≥ 0.55 and in the corner the slide leaves empty.
- Speed has its own tween outside the timeline (spin up 1.2 s, run down 2.4 s `power2.out`),
  so a quick second key press does not snap the wheel to a halt.
- `prefers-reduced-motion`: instant swap, still wheel. No WebGL: the deck runs without it.

**Traps, each found once:**

- **Dimming via `renderer.toneMappingExposure` does nothing per frame.** three.js uploads it
  only when a material is rebound. Fade the canvas instead (`style.opacity` over the ground
  colour): exact, and the compositor does it.
- **Vite cannot run from a path containing `#`.** Build through a symlink in the temp directory
  with `resolve.preserveSymlinks`, and copy the deck into `src/generated/` first. The dev server
  fails even then (its own client resolves back to the `#` path and 404s); a `vite build
  --watch` plus the static server replaces it.
- **A hidden browser pane pauses `requestAnimationFrame`, so GSAP freezes.** Every key press
  then shows the previous slide, which looks like an off-by-one bug. Test in headless Chrome
  (`scroll-stage-landing/scripts/cdp.mjs`, flags `--disable-background-timer-throttling
  --disable-renderer-backgrounding`).
- **A photo added late pushes the printed report around.** On the Omada deck a title bleed moved
  the last paragraph of section 1 to a page of its own. Hide `.bleed` (and its credit line) in
  `@media print` for doc mode; the slide PDF keeps it. Count report pages before and after.
- **A bleed whose subject sits mid-frame lands behind the headline.** Let the photo fill only
  the right 60 % and fade it into the ground from the left, instead of darkening the whole slide.
- **A fast double press leaves a third slide mid-fade.** Finish the running timeline with
  `progress(1)` before starting the next, and hide every section that is neither leaving nor
  arriving.

## The empty middle

The single most repeated complaint across three correction rounds on one deck, in the
person's own words: *"the middle of the slide looks empty"*, *"to much empty space in the
midle"*, *"Check all pages for padding and empty spaces"*. Never once about the top or the
bottom. It happens because a slide is a fixed 16:9 box, the content is a flex column
inside it, and a two-column row whose children are short dumps all its slack in the one
place the eye reads first.

Three fixes, in the order to try them.

**1. Split the slack, do not centre it.** A single trailing `.spacer{flex:1}` pushes
everything up and piles the gap at the bottom. Centring the lot leaves a headline floating
in the middle of nowhere. Put a small spacer above the content and a full one below, and
the free space divides in a ratio you chose:

```html
<h2 class="small">What I take from it</h2>
<div class="spacer" style="flex:.6"></div>      <!-- some air under the headline -->
<div class="cols" style="flex:none">…</div>     <!-- flex:none, or it stretches instead -->
<div class="spacer"></div>                       <!-- the rest of the slack, at the bottom -->
```

`flex:none` on the content block is the part that gets missed. Without it the block
absorbs the free space itself and grows the hole down its own middle instead.

**2. Centre one column against its taller neighbour.** `.cols{align-items:flex-start}`
top-aligns both columns, so a three-line list beside a one-line statement strands the
statement at the top of an empty half. `align-self:center` on that one child fixes it
without inventing a container:

```html
<div class="c-1" style="align-self:center"><p class="statement">Collecting data is the point.</p></div>
```

**3. Ask whether the slide is simply too empty.** Sometimes the hole is the slide telling
the truth. Folding it into its neighbour beats stretching three bullets to fill a frame.

## Charts that carry colour

A four-grey ramp with one accent is correct, defensible, and was described on sight as
*"the grey looks bad"*. The room reads flat grey as unfinished. What replaced it, and it
is narrower than it looks:

- **Every category gets its own hue, the subject stays the accent.** Four divisions in
  blue, terracotta, sage and violet; the fifth, the one the slide is about, in the deck's
  single accent yellow.
- **The other categories are dimmed, not greyed**: same hue, `opacity:.55`. They keep
  their identity, they just stop competing.
- **The hues are borrowed from a chart earlier in the deck, never invented per slide.**
  The five colours on the revenue split are the same five as on the ranking pie, so the
  file has one colour system instead of two, and blue means the same division on both.
- **Hue names a thing; it never decorates.** The moment a rule, a bullet or a heading
  takes a colour, the scheme stops meaning anything.

This is the one place the one-accent rule has to bend, and the bend is safe because a
categorical ramp is a different role from an accent. Settle it in the theme file, not per
slide (`design-directions` § When one accent is not enough).

## Eyebrows are rationed

The small uppercase label above a headline is the cheapest orientation device there is,
which is exactly why it ends up on every slide. A deck where all fifteen slides open
with a tracked-caps label has one rhythm, repeated fifteen times, and it reads as
templated rather than designed.

**At most one eyebrow per three slides.** The title slide counts as one. Everywhere
else the headline stands alone: a slide's position in the deck already says what kind
of slide it is, and the audience has been watching the previous fourteen.

Keep the eyebrow for the slides where orientation genuinely changes: the first slide of
a new movement, the one slide that breaks the running order, the summary. Count them
before publishing. `slop-taste` makes the same count mechanical for landing pages and
the reasoning carries over unchanged.

## Ask before you draw a figure

Whenever a slide carries numbers, shares, a structure, a sequence or a comparison, the
**form is a decision and it is not yours to take alone.** The same data usually admits
three or four honest forms, and they say different things. Pick the wrong one and the
slide is still true and no longer lands.

**Think first, then ask.** An open question hands the work back: *"how should I show
this?"* is not a question, it is an absence of one. Do the thinking, then put a short
list in front of the person with your recommendation already in it, one line for and
one line against each, and wait for the answer before building.

> Slide 5 carries the revenue split. Five divisions, one of them 1.2 percent.
>
> - **Stacked bar.** *For:* the proportion reads in one second and the small one is
>   visibly a sliver. *Against:* five labels have to fit under one bar.
> - **Columns.** *For:* brutal and honest, the smallest one nearly vanishes.
>   *Against:* harder to see that the five make up a whole.
> - **Pie.** *For:* nobody needs instructions. *Against:* two slices are too thin to
>   see, and a pie cannot be compared with next year's pie.
> - **Table.** *For:* exact figures, no reading error. *Against:* nobody takes in five
>   rows in two seconds.
>
> I would take the stacked bar, because the slide's job is the proportion and not the
> figures. Which one do you want?

Four options is the ceiling. Two is fine when the fork is real.

### Forms worth offering, by what the slide has to do

| The slide's job | Offer | Usually wrong |
|---|---|---|
| Parts of a whole, 2 to 6 parts | stacked bar · columns · table · pie | a donut with a number in the hole |
| Parts of a whole, 7 or more | fold the tail into one "Other", then as above | any pie |
| Change over time | line · area · slope chart between two dates | one pie per year |
| Comparing magnitudes | bar chart sorted by value · dot plot | 3D anything, a bar not starting at zero |
| One dominant figure | the number itself, set large, with unit and source | a chart of a single value |
| Two quantities of wildly different size | the ratio stated in words · an inset · a log scale that announces itself | a bar chart where one bar is invisible by accident |
| Structure or architecture | node diagram · layered stack · a table of layers | a flowchart where every box is the same shape |
| A sequence of years | timeline with bands · table of dates | a curved arrow with milestones stuck on it |
| Before and after | two column table · paired bars | two pies side by side |
| Relationship between two measures | scatter | a dual axis line chart, which is never the answer |

Once a form is picked, the `dataviz` skill owns how it is drawn: colour by job, the
validator, mark specs, the legend rule.

### What the answers are worth

Write the choice down next to the section list. A form chosen twice for the same kind
of data is the deck's default from then on: stop asking and say that you have stopped.
The question exists to catch the cases where the default is wrong, not to collect
approval.

**What a real answer looks like, and what it licenses.** Eight figures were put to one
person in a single message. The whole answer came back as: *"Slide 2 - Kuchendiagramm
(Runder kreis, klar unterscheidbare farben nutz). For the rest - do it. You decide."* That
is the good case, not a brush-off: one figure was decided by the person against the
recommendation (a pie, where columns had been recommended), and the remaining seven were
handed over with a constraint attached, which is *clearly distinguishable colours*. Carry
that constraint into all seven. An answer like this closes the question for this deck and
does not close it for the next one: ask again on the next deck, once, in one message.

Asking well is mostly batching. Eight separate questions would have been eight
interruptions and would have got a worse answer than one message with eight named slides,
four forms each, and a recommendation on every one.

## Numbers that survive the room

Rule 2 is the floor. These are the ways a number that already passes rule 2 still loses
the room. All of them were found on one deck, most of them late.

**The identifier belongs in the number, not in the caption.** A facts row reading
`100,000` · `200 MW` · `13 ha` · `2028` has one cell the eye cannot classify. The first
repair rewrote the caption under it, which is what the complaint literally asked for and
not what the slide needed; it was rejected. The accepted fix was `Year 2028`, matching the
*pattern of its three neighbours*. When a complaint names one element, look at what the
elements beside it do.

**One denominator per slide, or name the bases.** A stacked bar built from five divisions
sums them to 188.9 bn and gives the smallest 1.16 percent. The sentence beneath it says
1.2 percent of group revenue, and group revenue is 185.6 bn, because internal revenue is
consolidated out. Both numbers are right. The slide never says they are different bases,
which makes it look like an arithmetic error to anyone who checks. Compute every share on
a slide from one total, or put the base in the footer.

**A ratio across two currencies says so.** `128.7 bn USD` against `46.5 m EUR` is not
`1 : 2,700`, it is `1 : 2,700 before any conversion`. Convert it, or mark it.

**The qualifier is what a rewrite loses.** That same ratio first shipped as *"about
1 : 2,700, and the order of magnitude survives any exchange rate"*. A later round trimmed
the sentence for length, kept the number, and dropped the clause that made the mixed
currencies defensible. It went unnoticed for two rounds, precisely because the number was
still correct. **When you rewrite a sentence carrying a number, diff the qualifiers, not
the prose.**

**A figure drawn against time is drawn to scale, or it says it is not.** Marks at 19, 34,
53, 68, 83 and 96 percent for 2018, 2019, 2022, 2023, 2024 and 2026 draw the two-year gap
*narrower* than the one-year gaps. Nobody in the room does the arithmetic and everybody
sees that something is off. Compute positions from the dates, or label the axis schematic.

**The text and the picture carry the same comparison.** If the prose compares the spend to
a national budget, that budget is a bar on the chart, drawn as an outline because it is
not the subject's money. A comparison that exists only in the sentence makes the chart
look like it is hiding something.

**No proper noun the room cannot place.** A second site "near Rostock" is fine.
"Dummerstorf" is a question from the audience. A failed project referred to by its
internal codename is the same. Give it a clause or take it out.

**Say where a number came from when it is not a filing.** *"Press research, not an audited
company disclosure"* on the slide costs six words and converts the sharpest question in
the room into a nod.

## Interaction: the limit

Pick a small closed list and say so out loud in the plan. What a real deck needed:
mode toggle · theme toggle · one expanding diagram · one expanding catalogue · foldable
status · one heavy embed behind a click. Nothing else.

**Every interaction pays back more than it costs to understand.** A slider that asked the
audience to understand decibels before it showed anything was cut and replaced by a static
figure with plain-language axes and one claim written on it, which is what the interaction
existed to produce. Anything beyond the list is decoration a projector cannot use.

## Standing preferences

- **Light is the default in both modes and on any host theme.** Dark is a real toggle
  (`t`, remembered in `localStorage`), for a hall where a pale ground washes out. That is a
  call made at the podium, not at build time. Never tie the palette to the mode.
- **Keyboard first**: `→ ↓ Space PageDown` forward, `← ↑ PageUp` back, `Home` `End`,
  `d` mode, `t` theme. Ignore keys while focus is in an input.
- **Own material before borrowed.** A screenshot of our own run beats a stock image and
  carries no licence question. Borrowed material appears once and carries project · licence
  · link on the same card.
- **Measured before estimated, and nothing shown that has never run.** "We built the half
  that could be built and measured it instead of guessing" is the stronger claim anyway.
- **Three status colours, no fourth**: green built and tested · amber written but never run
  · grey open. One legend, stated on the slide.
- **Nothing private in anything projected or shared.** Swap a private dataset, room or
  document for a public one before the deck leaves the machine, and say in the notes why.
- Simplest path first. A working page beats a perfect plan.

## Prose

Run `stop-slop` and `no-ai-slop` over every visible string, and keep the result that way
when editing. In slide copy specifically: **no em dashes** (they survive fine in code
comments), no banned vocabulary, and no sentence that would not be said out loud in front
of the room.

## The static pass

Before opening a browser, before publishing, and again before handing the deck over. It
is fast, it needs no screenshots, and it catches the class of defect that survives a
visual check because it looks fine. Asked for in exactly these words once: *"dont check
visuals only the file itself"*.

```bash
python3 build.py                                    # placeholders filled, size, section count
grep -n "—" deck.template.html                      # em dashes in visible copy
grep -c 'class="eyebrow"' deck.template.html        # against section count: 1 per 3, title included
grep -oE '__[A-Z0-9_]+__' deck.template.html | sort -u   # tokens the build must fill
```

**Tag balance**, which catches a stray `</div>` that the browser silently repairs and the
PDF does not:

```python
from html.parser import HTMLParser
VOID = {"img","br","hr","input","meta","link"}
class C(HTMLParser):
    def __init__(s): super().__init__(); s.stack=[]; s.err=[]
    def handle_starttag(s,t,a):
        if t not in VOID: s.stack.append((t,s.getpos()))
    def handle_endtag(s,t):
        if s.stack and s.stack[-1][0]==t: s.stack.pop()
        else: s.err.append((t,s.getpos(),list(s.stack[-3:])))
c=C(); c.feed(open("deck.template.html",encoding="utf-8").read())
print("unclosed:",c.stack); print("errors:",c.err)
```

**Doc-mode twins**, the check that belongs to the `cqw` architecture in § Sizing. It lists
every class sized in `cqw` that has no `body.doc` rule. Expect a handful of benign hits
(containers, modifiers, and classes whose base already has a twin): read the list, do not
trust it blindly. It is worth running because the one real hit is always a class that was
added in a correction round.

```python
import re
css = re.sub(r'/\*.*?\*/','',open("deck.template.html",encoding="utf-8").read(),flags=re.S)
deck, doc = {}, set()
for sel, body in re.findall(r'([^{}]+)\{([^{}]*)\}', css):
    sel = sel.strip(); names = re.findall(r'\.([a-zA-Z][\w-]*)', sel)
    if sel.startswith('body.doc'): doc.update(names)
    elif 'cqw' in body:
        for n in names: deck.setdefault(n, []).append(sel)
print("sized in cqw, no body.doc twin:", ", ".join(sorted(c for c in deck if c not in doc)))
```

**The arithmetic**, by hand, once per deck: every percentage recomputed from its own
numbers, every bar width recomputed from its value against the series maximum, every sum
that is claimed on a slide actually added up. On the Schwarz deck this confirmed eight
column heights and five bar widths and found the denominator mismatch in § Numbers that
survive the room. Fifteen minutes, and it is the only way that class of defect is ever
found.

## Checking it in a browser

Worth doing, and easy to do wrong. Each of these produced a wrong conclusion in one
session before it was understood.

- **The mode is sticky.** The page remembers deck or doc in `localStorage`. A tab reopened
  for a deck screenshot can come back in doc mode from an hour ago, and the screenshot is
  then of the wrong artefact entirely. Set `document.body.className` explicitly before
  measuring or shooting anything.
- **A screenshot taken straight after a jump is black.** `scroll-snap-type:mandatory` is
  still settling. Call `scrollIntoView()`, wait on a timer, call it again, then shoot.
- **Overflow can only be measured on the section that is on screen.** In deck mode the
  off-screen sections return numbers that look alarming and mean nothing. Measure one
  section at a time, or measure in doc mode where everything is laid out at once.
- **Editing the template can pop a tab on `file://…/deck.template.html`** if a hook watches
  writes. That tab renders the *unbuilt* file, `__PLACEHOLDER__` tokens and all. Pass the
  intended tab id explicitly on every browser call.
- **Region-cropped screenshots are not available in every browser pane build.** Asking for
  one silently returns the full screenshot, which then gets read as if it were the crop.

The one measurement worth the trip:

```js
// deck mode, this section scrolled into view: how far the content overflows its slide
const inner = document.querySelectorAll('section')[i].querySelector('.inner');
inner.scrollHeight - inner.clientHeight;   // <= 0 is clear, > 0 is clipped on the projector
```

## Correction rounds

A built deck comes back as a numbered list. Three rounds on one deck produced the rules
below, and they matter more than the build rules, because this is the part where a deck
actually gets finished.

**Change only what is on the list.** Said in two rounds out of three: *"Only change what i
told you."* An unrequested improvement is a defect in a correction round, because it costs
the person a re-read of a slide they had already signed off. If something else is wrong,
say so in the reply and leave it alone until they answer.

**Report what you did not do, and why, in the same reply.** Two instructions on this deck
could not be followed literally: *"shorten the footer by removing the credit mention"* on a
slide carrying two CC BY-SA photos, where the licence requires the credit, and removing a
vendor's name that turned out to be load bearing two slides later. Both were done
partially and both were reported. Silent partial compliance is the failure to avoid: it
surfaces three rounds later and costs a full re-check.

**Read the complaint as a symptom.** *"This number is missing an identifier"* was answered
first by rewording the caption. Literal, and wrong. The number itself was the defect.

**A short line replacing a list needs a layout change in the same edit.** Swapping five
bullets for one sentence is usually right and almost always leaves that sentence orphaned
at the top of an empty column. Fix both at once or it comes back as *"seems kinda lost"*.

**Close the round properly**: template edited, build run, static pass green, one commit
for the round, artifact republished to the *same* URL, and a reply that maps one line to
each numbered item. A round that was never republished does not exist for the person who
asked for it.

**Then have a subagent audit the list against the diff.** Asked for explicitly in two
rounds, and it earned its keep both times. Hand it the numbered list *verbatim* and the
diff, and ask for one line per item plus anything broken in passing. Handing it your own
summary of the list means it audits the summary.

## Traps, each of which cost a rebuild

- **A canvas painted only from `requestAnimationFrame` stays blank in a background tab.**
  Draw the first frame synchronously, then start the loop.
- **A canvas created by an `innerHTML` swap has no box on that tick.** Drawing immediately
  sizes it 2×2 and the browser stretches four pixels across the card, which looks like a
  styling bug and is not one. Wait for layout on a timer, not on a frame callback (same
  background-tab reason).
- **`var` hoisting takes down the whole page, not one feature.** An initialiser that reads
  a `var` declared further down the same IIFE throws, and the throw ends the IIFE: the
  navigation, the status board and the canvas all silently do not exist, each looking like
  its own separate bug. Declare data before the code that reads it, or split the IIFE.
- **A smooth scroll inside `scroll-snap-type:mandatory` is cancelled by the snap.** Deck
  slides jump (`scrollTop = i * clientHeight`), doc mode glides (`scrollIntoView`).
- **A programmatic scroll fires scroll events all the way to its target.** Without a lock
  (~400 ms) the scroll listener reads a half-finished position, resets the index to the
  slide being left, and the next keypress goes nowhere.
- **Patching a large template between two anchors deletes everything that drifted between
  them.** One such patch swallowed 9681 characters of working script and reported success,
  because everything it asserted about was correct. Anchor on strings unique in the file,
  and check the byte delta against what was meant to change.
- **A fix applied to a build output has a lifetime of minutes.** Build outputs are
  gitignored; the next rebuild silently reverts them and `git status` shows nothing to warn
  about it. Fix the template, the asset recipe, or the script, never the output.

## Print and PDF

The same file gives two PDFs, and a talk usually needs both: slides to hand in or hand
round, and a readable document for whoever asks afterwards. On a course, that document
is frequently the assignment itself.

Print the **deck** and each `<section>` becomes one landscape page. Print the **doc**
and it flows as a normal document. The mode on screen is the mode that prints.

```css
@page { size: 297mm 167mm; margin: 0; }          /* 16:9 */
@media print {
  html, body { height:auto; overflow:visible; background:#fff; }
  body.deck section {
    height: 167mm; width: 297mm; page-break-after: always; break-after: page;
    display:flex; overflow:hidden;               /* a slide that spills is a lost slide */
  }
  body.doc { }                                   /* @page size overridden to A4 portrait */
  body.doc section { break-inside: avoid-page; }
  .chrome, .modetoggle, .themetoggle, .progress { display:none !important; }
  * { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
}
```

Five things that cost a reprint:

- **Force the light palette.** A dark deck prints as a black rectangle and eats a
  cartridge. Override the tokens inside `@media print` rather than asking the person to
  toggle first.
- **Backgrounds are dropped unless `print-color-adjust: exact` is set**, so every tinted
  lane, status square and accent rule disappears and the slide loses its structural rule.
- **`scroll-snap` and `100vh` do nothing on paper.** Give sections a real `mm` height in
  the print block or they collapse to their content and two slides share a page.
- **Anything behind a click is invisible on paper.** Expandable detail panels, folded
  status branches, load-on-demand viewers. Either force them open in print, or accept
  that the PDF is missing the part that was the point.
- **A canvas prints whatever frame it is on.** Draw the first frame synchronously (it is
  already required, see Traps) and it prints; leave it to `requestAnimationFrame` and the
  page prints blank.

Check the PDF, do not assume it. Page count is the fastest tell: it should equal the
section count exactly.

## Publishing as an Artifact

- **16 MB total, and the CSP blocks every external image, media and fetch.** Everything
  travels inside the file as a data URI. Stylesheets only from Google Fonts, scripts only
  from the allowlisted CDNs, pinned to an exact version.
- **The URL follows the file.** Republishing the same path keeps it. A deleted artifact's
  URL is gone for good and cannot be republished onto. Anyone holding the old link has a
  dead one. Record the live URL where the project keeps its state, on the day it changes.
- **Downloads are inert inside an artifact.** An export button in an embedded viewer will
  not work; do not promise it from the slide.
- **From a later conversation, the URL has to be passed back in explicitly.** Republishing
  by file path alone keeps the URL only inside the session that first published it. A new
  session that forgets the `url` silently creates a *second* artifact, and the person is
  then holding two links with different content. Keep the URL in the handover file and
  read it before publishing.
- Must still read at ~400 px wide and in the viewer's theme.

## When the assets are large

Split the page into `deck.template.html` plus an `assets/` directory plus one build script
that substitutes `__PLACEHOLDER__` tokens, inlines the assets as data URIs, prints the size
against the budget and refuses to write when a placeholder is unfilled or the page is over.
Scan the *template* for unknown placeholders, never the output: bundled libraries carry
token-shaped annotations of their own. An embedded HTML document goes into a
`<script type="text/plain">` block with `</script` swapped for a sentinel the page restores
at runtime, which costs nothing where base64 would cost a third.

Two more jobs worth giving the same script, both from the Schwarz build:

**Generate figure geometry from the data, in the script.** The pie on that deck is built
by a function that takes the same list of five companies that feeds the legend, converts
revenue to sweep angles, and emits the `<path d="…">` strings with the subject slice
exploded by 10 units. Nobody can nudge a slice without changing the number, and the legend
cannot drift from the chart, because there is one list:

```python
PIE = [("Volkswagen", 322.2, "#5B8DB8"), ("Schwarz Gruppe", 167.2, "#FFE500"), …]
def pie_paths(cx=200.0, cy=200.0, r=168.0, explode="Schwarz Gruppe", off=10.0):
    total = sum(v for _, v, _ in PIE)
    …  # sweep = v / total * 360, plus a <title> per slice carrying name, value and share
```

**Escape every non-ASCII character on the way out**
(`html.encode("ascii","xmlcharrefreplace")`). The artifact wrapper owns the `<head>`, so
the page cannot declare its own charset, and a stray `ü` or `€` is then at the mercy of
whatever the host declares. Entities are immune to that and cost nothing.

Edit the template. Never the generated file.

## Before the talk

- [ ] Static pass green (§ The static pass): build clean, tags balanced, no em dashes, no
      unfilled tokens, eyebrow count inside the ration, every doc-mode twin present
- [ ] Arithmetic recomputed by hand: every percentage from its own numbers, every bar from
      its value, every share on the same denominator, every cross-currency ratio marked
- [ ] Opened at projector size, in the actual room's lighting if possible, dark toggle tried
- [ ] Every slide checked for the empty middle at full size, not in a narrow pane
- [ ] Arrow keys, `Home`, `End`, `d`, `t` all work; nothing needs a mouse
- [ ] Every number traced to its source, labelled, and from the same run as its neighbours
- [ ] Anything not from a filing says so on the slide
- [ ] No proper noun on a slide that the room cannot place
- [ ] The structural rule holds on every two-sided slide
- [ ] Borrowed material credited **at the object**, naming the author, not only collected
      on the sources slide
- [ ] `prefers-reduced-motion` respected; the page still makes sense with animation off
- [ ] Readable at ~400 px wide, for the people who open the link on a phone afterwards
- [ ] Slop pass done; no em dashes in visible copy
- [ ] Printed to PDF from both modes; page count equals section count; nothing clipped,
      no dark ground, no missing tint
- [ ] One question asked of the person, out loud: can the hall be dimmed? A dark deck has
      no CSS fix for a bright room, and it is better known the day before than in it

## What the last decks taught

[`decks-ledger.md`](decks-ledger.md) carries one entry per deck actually given (empty at the start of this project): what it
was for, how long it ran against how long it was planned for, which slides were cut
live, and what broke in the room. Read it before outlining a new one and append to it
after the talk.

A skill that only records intentions never learns. Timing is the specific thing worth
recording, because the gap between planned minutes and spoken minutes is consistent per
person and impossible to guess from the outline.

Two numbers already in there, worth carrying into the next plan:

- **One build plus three correction rounds** is the realistic shape, not one build plus a
  polish. The rounds on the Schwarz deck ran 14 items, then 8, then 2: roughly halving,
  which makes the end predictable once the first round has landed.
- **Nothing in those 24 items touched the theme, the fonts or the grid.** The look had
  been decided separately, before the build, and was never reopened. Everything else was
  layout slack, plainer words, a number missing its unit, or something to cut.

## Not this

- **No figure whose form was chosen silently.** Numbers, structures, sequences and
  comparisons get the question in § Ask before you draw a figure, with a recommendation
  attached, every time until a default is established out loud.

No slide framework: reveal.js, Slidev and the rest buy nothing a page with scroll-snap
does not already do, and they lose the doc mode. No second artifact for the handout. No
video of something that has never actually run. No interaction that must be explained
before it pays. No content in the deck that contradicts the files it was drawn from: fix
the source, then the slide.

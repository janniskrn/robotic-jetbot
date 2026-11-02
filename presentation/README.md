# The weekly status update

`index.html` is the presentation. One file, no server, no internet needed after the fonts have loaded once.
Open it in a browser, present from it, print it to PDF. It is committed, so a `git pull` is all anyone needs.

Rhythm and course rules: [`WEEKLY.md`](../WEEKLY.md). Look: [`design/THEME.md`](../design/THEME.md), locked.

## Presenting it

| Key | What it does |
| :--- | :--- |
| click a week card, or `enter` | open that week's slides |
| `right`, `down`, `space`, `page down` | next slide |
| `left`, `up`, `page up` | previous slide |
| `home`, `end` | first, last |
| `escape` | close a code panel, or go back to the roadmap |
| `d` | the same content as a document, for reading and for the report |
| `t` | dark palette, for a hall that cannot be dimmed |

**PDF:** print from slides mode for one landscape page per slide, or from document mode for a report.
The light palette is forced in print even if the dark toggle is on. Code panels print in the document, not
on the slides.

## What is on which slide

Ten slides, in the order the Tuesday rules ask for.

| # | Slide | Answers |
| :--- | :--- | :--- |
| 1 | Status board | where the project stands |
| 2 | What we did since the last demonstration | Tuesday point i |
| 3 | How the robot decides, every frame | point ii, with a code panel |
| 4 | Six states, priority | point ii, with a code panel |
| 5 | What the models get right and wrong | point iii, the accomplishment half |
| 6 | Task 1 result | point iii, with a code panel |
| 7 | Stopping at a cup | point iii |
| 8 | Around the cup | point iii |
| 9 | Four things went wrong | point iii, the failure half, with causes |
| 10 | What we do before the next demonstration | point iv |

## The weekly update, in order

Most weeks only the first four steps change anything.

1. **Roadmap** (`<div class="cards">`): when a week is demonstrated, move its card from `card locked` to
   `card open`, give it an id, and wire it in the script next to `card-w1`. Set the state line and its dot
   color: green `var(--ok)`, amber `var(--amber)`, grey `var(--rule)`.
2. **Status board** (slide 1, `.board`): one `.brow` per task. The class on the row sets the color:
   `s-built`, `s-written` or `s-open`. Set the meter width to how far the task is and keep the right hand
   label to three words.
3. **Last week** (slide 2, `.week`): four `.wday` blocks, oldest first. Class `good`, `bad` or `now` colors
   the top rule. One date line, one headline, one sentence. If a week had five events, cut the weakest.
4. **Failures** (slide 9, `.chains`): one `.chain` per failure, three boxes: `c-sym` what we saw, `c-why` the
   cause, `c-fix` the fix. Use `c-open` instead of `c-fix` while the cause is unknown, and say so out loud.
5. **Next** (slide 10, `.steps`): one `.step` per step with its pass condition. Add `block` to the step that
   blocks other tasks.
6. **Numbers**: only if a new run happened. Sources are listed below.

## Where every number comes from

| On the slide | In the repository |
| :--- | :--- |
| Task 1 runs, wobble, speeds | `results/week1/task1_results.md` |
| Model percentages, frame counts, errors | `notebooks/mini_av/models/*.json` |
| Every threshold (rows, seconds, gains) | `notebooks/mini_av/config.py` |
| What each state does | `notebooks/mini_av/decision.py`, `STATE_MACHINE.md` |
| Failures, causes, dates | `DECISIONS.md`, newest entries first |
| What is done and what is next | `PLAN.md` section 6, `HANDOVER.md` |
| Run logs | `usb/logs/` on the robot |

**The honesty rule that keeps this defensible:** green means it completed runs on the track, amber means the
code exists and has never completed a run, grey means it is blocked on something physical. A slide never
claims more than the logs do, and anything measured in a test script says so.

## Code panels

Four slides carry one. They open as an overlay with their own scroll, because a 16:9 slide cannot grow.

```html
<div class="codeblock deckonly" style="flex:none">
  <button class="codebtn" type="button" data-code="c-name">Short label</button>
</div>
<div class="codewrap" id="c-name" data-open="false">
  <p class="why"><b>Why it looks like this.</b> One or two sentences: the decision and what forced it.</p>
<pre><span class="c"># file.py</span>
code goes here, five to eight lines</pre>
  <p class="where">file.py · where the numbers live</p>
</div>
```

Keep them to about eight lines and lead with the decision, not the syntax. The panel exists to answer "why is
this number 0.15", which is the question that actually gets asked.

## Checks before you present

```bash
python presentation/check.py
```

Tag balance, em dashes, unfilled placeholders, every `cqw` class having its document twin, the bar widths
recomputed from their own values, and the palette contrasts. It needs no browser and takes a second.

**Then the overflow check, which needs a browser.** Open `index.html`, press `F12`, paste this in the console:

```js
const deck=document.getElementById('deck'), secs=[...deck.querySelectorAll('section')];
document.body.className='slides'; await new Promise(r=>setTimeout(r,300));
const over=[];
for(let i=0;i<secs.length;i++){ deck.scrollTop=i*deck.clientHeight; await new Promise(r=>setTimeout(r,90));
  const n=secs[i].querySelector('.inner'); const o=n.scrollHeight-n.clientHeight; if(o>2) over.push({slide:i+1,over:o}); }
console.table(over.length?over:[{slide:'all fit',over:0}]);
```

Anything over about 2 px is text that will be cut off on the projector, and it is always the last line of the
slide, which is where the caveats live. Fix it by shortening the sentence or lowering the figure cap
(`figure svg{max-height}`), then run it again.

## Adding a new week of slides

The script shows whichever `<section>` blocks are in `#deck`, so a second week means a second group of
sections plus a switch on which group is shown. Until that is needed, keep one week's slides in the file and
start a new file per week only if two weeks have to be presented side by side.

## House rules for the text

- No em dashes. No sentence that would not be said out loud.
- Every number says what it is a number of, inside the number: `60 s`, `row 88 of 224`, `8 stops`.
- Figures standing next to each other come from the same run. If one is borrowed, the slide says so.
- At most one eyebrow per three slides. They lose their meaning when every slide has one.
- A slide carrying a claim carries its source line.

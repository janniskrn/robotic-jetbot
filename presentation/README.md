# The weekly status update

The presentation is one HTML file. No server, no internet needed after the fonts have loaded once.
Open it in a browser, present from it, print it to PDF. It is committed, so a `git pull` is all anyone needs.

| File | What it is |
| :--- | :--- |
| `index_v3.html` | **The current deck.** Follows the professor's presentation guideline: architecture, source code, explanation, results, next plan |
| `index_v2.html`, `index.html` | The 2 November decks, kept for the record. Their code snippets are paraphrased and no longer match the source |

Rhythm and course rules: [`WEEKLY.md`](../WEEKLY.md). Look: [`design/THEME.md`](../design/THEME.md), locked.

## The structure the professor asked for

His guideline, point by point, and where each one lives in `index_v3.html`:

| Point | Slides |
| :--- | :--- |
| i. Total architecture of the code | 3 module map, 4 one camera frame |
| ii. Show the source code | 5 to 11, the real file on the slide, never a paraphrase |
| iii. Detailed explanation of it | the numbered notes beside each listing |
| iv. Results from the executed code | 12 models, 13 task 1, 14 the stop, 15 the swerve, 16 failures |
| v. Next plan from results and bugs | 17 |

Slides 1 and 2 come before that: where the project stands, and what happened since the last demonstration.
The roadmap shows the same five points before anyone enters the slides, so he can see the order up front.

## Presenting it

| Key | What it does |
| :--- | :--- |
| click a week card, or `enter` | open that week's slides |
| `right`, `down`, `space`, `page down` | next slide |
| `left`, `up`, `page up` | previous slide |
| `home`, `end` | first, last |
| `escape` | back to the roadmap |
| `d` | the same content as a document, for reading and for the report |
| `t` | dark palette, for a hall that cannot be dimmed |

**PDF:** print from slides mode for one landscape page per slide, or from document mode for a report.
The light palette is forced in print even if the dark toggle is on. Code panels print in the document, not
on the slides.

## What is on which slide

| # | Slide | Carries |
| :--- | :--- | :--- |
| 1 | Status board | one row per task, colored by what actually ran |
| 2 | Since the last demonstration | four days, oldest first, failures included |
| 3 | Module map | the three layers, their line counts, who may touch the motors |
| 4 | One camera frame | the five stages and the timing |
| 5 | `drive.py` | the loop, the four exits and the guards, 7 notes |
| 6 | `perception.py` | models recognize, masks measure, 5 notes |
| 7 | The state machine | the six states and the four swerve phases |
| 8 | `decision.py` | priority as the order of the branches, 6 notes |
| 9 | `control.py` | the eight pieces of the steering, each from a failure |
| 10 | `config.py` and `safety.py` | no magic numbers, four guards |
| 11 | The learning pipeline | record, label, train, convert, judge |
| 12 | The three models | accuracy and the weakness under each |
| 13 | Task 1 | six runs against a 60 s cap |
| 14 | The stop at a cup | the three rows, the trigger code, what the runs measured |
| 15 | The swerve | the intended path, and which starts worked |
| 16 | Failures | symptom, cause, fix, one row each |
| 17 | Next plan | steps with their pass conditions |

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
4. **Failures** (slide 16, `.chains`): one `.chain` per failure, three boxes: `c-sym` what we saw, `c-why` the
   cause, `c-fix` the fix. Use `c-open` instead of `c-fix` while the cause is unknown, and say so out loud.
5. **Next** (slide 17, `.steps`): one `.step` per step with its pass condition. Add `block` to the step that
   blocks other tasks.
6. **Code slides** (5 to 11): only when that file changed. Re-copy the lines from the source and run
   `check.py`, which is the whole point of having it.
7. **Numbers**: only if a new run happened. Sources are listed below.

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

**The honesty rule that keeps this defensible:** green means it completed runs on the track to its pass
criterion, amber means it runs but has not reached that criterion, grey means it is blocked on something
physical. A slide never
claims more than the logs do, and anything measured in a test script says so.

## Code slides

A code slide is the real file on the left and numbered notes on the right. Copy the lines **verbatim** out of
the source; `check.py` reads the file and fails if a line is not there any more. A line may be cut short with
`...`, which only has to match the start of a real line. `<span class="m">N</span>` is the marker gutter, empty
on unmarked lines, and `<span class="c">` is a comment, which the checker ignores.

```html
<div class="codeslide">
  <div class="codesrc">
    <div class="cf">control.py · update() · lines 71 to 93, shortened</div>
<pre><span class="m">1</span>self.lane_x += config.LANE_SMOOTHING * (lane_x - self.lane_x)
<span class="m"></span>    a line with no note</pre>
  </div>
  <ol class="notes">
    <li><span class="nn">1</span><span><b>The claim in four words.</b> Then the evidence or the failure
      that forced it.</span></li>
  </ol>
</div>
```

Rules that keep these defensible: lead the note with the decision, not the syntax; name the failure that
forced the line where there was one; keep lines under about 90 characters or they scroll sideways; about 20
lines is the most a slide holds. `pre class="wrapcode"` wraps long comment lines, for `config.py`.

There are no hidden panels. Everything the slide claims is on the slide, because code behind a button reads
as code not shown, and nobody clicks it while presenting. If a listing has to grow, cut the figure cap
(`figure svg{max-height}`) or a sentence, and check the slide again.

## Checks before you present

```bash
python presentation/check.py index_v3.html
```

Tag balance, em dashes, unfilled placeholders, every `cqw` class having its document twin, the bar widths
recomputed from their own values, every quoted code line still present in its source file, and the palette
contrasts. It needs no browser and takes a second.

**Then the overflow check, which needs a browser.** Open `index_v3.html`, press `F12`, paste this in the console:

```js
const deck=document.getElementById('deck'), secs=[...deck.querySelectorAll('section')];
document.body.className='slides'; await new Promise(r=>setTimeout(r,300));
const over=[];
for(let i=0;i<secs.length;i++){ deck.scrollTop=i*deck.clientHeight; await new Promise(r=>setTimeout(r,90));
  const n=secs[i].querySelector('.inner'); const o=n.scrollHeight-n.clientHeight; if(o>2) over.push({slide:i+1,over:o}); }
console.table(over.length?over:[{slide:'all fit',over:0}]);
console.table([...document.querySelectorAll('.codesrc pre')].map((p,i)=>({block:i,sideways:p.scrollWidth-p.clientWidth})));
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

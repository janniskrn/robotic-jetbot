# Build: counter-moves by text type

The twelve counter-moves in `SKILL.md` come from fiction (StoryScope, stories of about 5,000 words). This file says what they mean in other text types, which fingerprints the individual models leave, and how the counter-moves themselves can turn into a template.

## From story to non-fiction

| Finding in AI fiction | What it looks like in non-fiction | Counter-move |
|---|---|---|
| Narrator states the theme | Conclusion, "Key takeaways", closing paragraph with a lesson, "This shows how important ..." | delete; end on the last fact, an action or an open question |
| One plot strand, no side strand | every section dutifully fulfils its function | a digression, a parenthesis, an anecdote that only half belongs |
| strictly chronological | problem, solution, benefit; step 1 to 5 | in short texts do not reorder (recognized as model in the blind test) but allow digressions; in long texts, give one piece of information late that recasts the earlier part |
| Resolution through inner insight | "And that is exactly when I understood ...", "My most important lesson" | do not announce the lesson; show what you do differently now, or admit you do not know yet |
| Hero solves everything alone | every turn is own achievement | name chance, luck, help from others, outside constraints |
| Feeling through the body | "My heart beat faster when the email arrived" | "I was nervous." |
| vague allusions | "as a well-known investor said", "studies show" | name names or leave it out |
| Text without an audience | detached explanatory tone | address the reader directly, ask a real question |
| morally unambiguous | all objections are cleared away | leave one objection standing, name an own failing |
| few places, little dialogue | only abstractions | a literal quote from a conversation, a place, a time of day |
| even tension | every paragraph the same length, the same importance | give one point a lot of room, dismiss another in half a sentence |

## By text type

**LinkedIn and social.** No one-liner as a hook with a blank line after it, no list with emojis as bullets, no mandatory question at the end ("What do you think?"). Paragraphs of uneven length. A concrete moment (date, place, person) carries more than any lesson. The ending may be abrupt.

**Blog and essay.** Start where the author started thinking, not with the state of the world and not artificially with the result. At least one digression. Subheadings only where readers want to jump, and never one that says "Conclusion". A thought may stay unfinished.

**Email.** The request in the first sentence. No "I hope you are well" as a mandatory formula, no summary of the conversation the recipient had themselves. Greet briefly.

**Story.** All twelve counter-moves apply fully. Time jumps across the whole story, not only an opening in the middle of a scene (Kimi does that too). A side character with an agenda of their own. Name feelings. No epiphany at the end, no epilogue. One real reference: a song, a book, a street.

**Product and web copy.** One concrete number instead of three benefit promises. One sentence that limits ("For teams under five people this is not worth it."). Client names only with approval.

**Report, analysis, term paper.** Found in a strategy analysis in English (2026-10-27) whose running text mostly carried AI build. The patterns there: almost every bullet as "Label: an explanatory sentence" (71 of them), tension headings "X vs. Y", freshly invented capitalized categories ("Compute-Dense Challengers"), favorite words of the genre ("moat" 11 times), every statement equally certain, no weighting of the author's own, and at the end a synthesis that says every section once more (and spoke of four sections where there were five). Counter-moves: reasons as running text, bullets only for real lists; a source for every number; name uncertainty where it exists ("the figure comes from a press estimate"); a weighting of your own with a reason, where the author has one, otherwise a placeholder asking for it; do not resolve counter-arguments when they are open; a synthesis only with what follows from reading the parts together. Outline requirements of the assignment (SWOT, Porter, VRIO) stay, they are not an AI pattern.

**Technical & engineering presentations (slide decks, defenses, walkthroughs).** Register is strictly academic and engineering-grade. Target audience: professors, domain experts, technical evaluators. Terminology must be exact: control theory (e.g. *proportional-derivative controller, gain scheduling, underdamped lateral oscillation, feedforward curvature compensation*), machine learning (e.g. *session-disjoint train/val split, inference latency, optical occlusion, MAE*), and robotics architecture (e.g. *distance-gated stop, circumvention maneuver, tri-modal recovery, watchdog timeouts*). Do not colloquialise or dumb down technical facts (never write "5 came back" or "learns cm"). Every metric states its unit and test condition.

**Cover letter and application.** One told case instead of a list of qualities. A weakness that is true.

**Speech and talk.** Repetition is allowed when spoken. Address, questions with a pause, one sentence that falls out of the manuscript.

## Fingerprints of individual models

From StoryScope, table 16 and section 5. Useful when it is known which model wrote the draft.

| Model | Fingerprint | Counter-move |
|---|---|---|
| Claude | flattest escalation of all sources, little event variety, uniform narrator voice, honors the conventions of the genre (62 % against 39 to 56 %), epilogue or look ahead at the end, calm endings, never dream sequences | sharpen an event, delete the epilogue, break one convention, change voice at one point |
| GPT | rumor and gossip as a driver (64 %), retrospection from decades of distance, dream sequences, subverts expectations more often than other models, half-open reconciliations | delete the retrospective frame and the dream, replace gossip with action |
| Gemini | character described from outside, cleanest endings, long fade-outs, gloomy settings (88 %), siege or trial scheme | introduce the character through speech or action, shorten the fade-out |
| DeepSeek | important context right at the front, visible narrator, feeling through behavior, backstory scattered evenly | deliver context later, backstory in one block or not at all |
| Kimi | generic middle of all models, character introduced in action, opening in the middle of the scene | fetch the author's material right here |

Humans introduce characters strikingly often in dialogue, stay with one perspective, hold the revelation until the end and mix genres.

## When the counter-moves themselves become a template

Every counter-move becomes recognizable once it is in every text. A text that always ends with "Whether that works, I don't know yet" has only learned a new punchline. So:

- choose three to five counter-moves per text, not all twelve
- align the choice with the material: where the author has a real open question, it stays open; where not, the text ends on a fact
- put parentheses, questions and address not in every paragraph but where the author would say them
- non-linearity only when it reveals something; a time jump without a reason is decoration
- across several texts by the same author, vary opening and ending

## Example

Before (typical draft):

> In today's fast-paced working world, feedback is more important than ever. Last week I learned a valuable lesson: good feedback is not criticism, but a gift. When my team lead told me that my presentation was too long, I felt my stomach tighten. But then it dawned on me: he was right. Since then I shorten every presentation, ask for feedback early and reflect regularly. At the end of the day, we only grow when we listen. A rocket emoji closes the post.

After (name, numbers and day come from the real author):

> Forty slides I had with me on Tuesday, and Jens asked after slide twelve whether we could skip ahead. I was angry. At him a little, but mostly at myself, because I had noticed it while building. (Slide nine was a diagram I did not fully understand myself.) For the next meeting it is eleven.

What changed: opening with the moment instead of the working world; lesson, contrast formula and closing wisdom deleted; feeling named instead of the stomach; one digression in parentheses; the triple "shorten, feedback, reflect" replaced by a number; ending on a fact.

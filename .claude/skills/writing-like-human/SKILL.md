---
name: writing-like-human
description: Master skill for writing text that sounds like a person wrote it. Works where readers and detectors spot AI today, in the build of a text (short sentences instead of chains, defused images, reordered chronology, a rounded ending, a stated moral, everything resolved, feelings shown through the body instead of named, no real names), backed by StoryScope and a blind test of its own, and hands the word and sentence level to slop-prose or slop-humanizer. Use when writing or revising any text people will read: blog post, LinkedIn, newsletter, email, essay, story, speech, about page, product copy, report, analysis, term paper, slide text, and for "sounds like AI", "make it more human", "humanize", "remove the AI patterns", "human writer", "writing like human", or the question whether a text sounds like AI. Not for code, commit messages, tables, or pure reference documentation.
---

# Writing like a human

Status 2026-10-28. This is the English copy for our repo, translated from the German original. The measurements behind it were made on German blog texts; the structural findings come from English fiction (StoryScope). Evidence with numbers is in [references/sources.md](references/sources.md). The raw blind-test files and the development log of the original are not included in this copy.

AI text gives itself away on three levels. Words ("delve", "seamless", em dashes) change with every model generation and are easy to replace. Sentences (the contrast formula, the triple, the punchline at the end of a paragraph) are more stubborn. The most stubborn is the build: what is told, in what order, what stays open. StoryScope (Google DeepMind and University of Maryland, 61,608 stories) recognizes AI fiction with 93.2 % accuracy from such build decisions alone, without a single style feature. Revising the surface lowered that detection by only 1.6 points. Swapping words therefore changes almost nothing.

This skill therefore works from the top down: first material and build, then sentence, then word.

**Measurements.** In blind test 1 (2026-10-27), a judge told eight real German blog texts from Claude versions with the same facts 8 out of 8 times, without the skill and with the first version of this skill. The rules below were rebuilt afterwards. Blind test 2 (2026-10-28, 16 new texts, seven instruments, holdout) checked them: no version, not even one with a real voice sample from the author, lowered detection on fresh texts. A Claude judge recognized the human text 10 of 10 in pairs and 6 of 6 on the holdout; in single-text judgments it ranked every human text below every model text, even after all typos of the humans were corrected. Whoever uses this skill gets a cleaner text without the known stock phrases and build patterns, but not one that an attentive reader with a comparison text cannot identify as model text. What still carries after the test: the author's own material (step 2), not the rules.

## What it can do and what it cannot

No skill guarantees "100 % human" on every detector. Trained classifiers also read token statistics that stay invisible while writing, and they flag real human text as AI in turn (commercial detectors flagged 9 to 15 % of real abstracts from 2023 to 2025 in one study). What is achievable is a text in which an attentive reader finds no pattern and whose build sits where people build it.

Since August 2026 there is also a watermark: Claude (including the model running this skill) and, from October 2026, ChatGPT in the EU choose their words according to a secret key. Whoever has access to the vendor's detector, which explicitly includes educational institutions in the EU, can prove the pattern over enough text. This skill does not remove it and claims nothing about it. What it can do: find invisible characters and clean them after approval (step 7), and get the author to contribute their own sentences.

The strongest lever is the person: a decision they made, a name, a number from their everyday life, a doubt they really have. A model cannot invent that without lying. So we ask for it.

Never: insert random typos or grammar errors, fake leftovers of a publication (a colon before a video that does not exist), invent experiences that will be read as true, make up sources or quotes. That makes the text worse and dishonest, and it does not hit what readers recognize: in blind test 2, human texts were recognized 10 of 10 even after all errors were corrected. Allowed and wanted are quirks the author really has (own words, writing habits, recurring errors), taken from their voice and in its density. Fiction is the exception; inventing is the job there.

Never swap words for synonyms to make a text look different. That is exactly what paraphrasing tools do, and it leaves a trace of its own that is easy to spot ("tortured phrases"): in a checked term paper (2026-10-27) it said "Model Concept Protocol" instead of Model Context Protocol, "Controlled Vertical Dominance" instead of Regulated Verticals, "almost hard" instead of almost impossible. Technical terms, proper names and fixed phrases stay verbatim. The build is rewritten, not the vocabulary.

In technical, scientific, and engineering documents (slide decks, specifications, project reports, architecture docs), standard domain terminology (e.g. *obstacle detection & distance-gated stop, circumvention maneuver, proportional-derivative controller, gain scheduling, feedforward curvature compensation, underdamped lateral oscillation, session-disjoint split, data leakage, empirical calibration, hysteresis*) is strictly required. Never replace technical terms with colloquial simplifications or conversational folk descriptions (e.g. do NOT write "backs away in pulses and learns cm", write "automated incremental empirical distance calibration ($d = 405 / \sqrt{A}$)").

A language model as judge ("does this sound like AI?") is only worth using once it has been checked on known pairs. The local Qwen3.8-27B got only 3.5 of 8 right on the pairs from blind test 1 (chance would be 4) and mostly took the smoother text for the human one. Claude got the same pairs 8 of 8.

## Who does what

| Level | Where | Note |
|---|---|---|
| Material, build, stance, procedure, final check | this skill | applies before all others |
| A specific author's voice | [references/voice-profile.md](references/voice-profile.md), `scripts/voice_profile.py` | swappable, kept outside the skill; beats all rules |
| Invisible characters, watermarks | [references/watermarks.md](references/watermarks.md), `scripts/invisible_chars.py` | find characters and clean them after approval; only explain statistical watermarks |
| Word and sentence patterns, keeping the voice | `slop-prose` (edit and audit) or `slop-humanizer` (stricter rewrite, 26 patterns, strongest first) | use one of the two per text, not both |

Where the skills disagree, this one wins. `slop-prose` in particular is too absolute: a rule that applies everywhere creates a pattern of its own. So here:

- Do not break up long sentences just because they are long. `slop-prose` pushes toward short sentences; what was measured is the opposite (see counter-move A below).
- Adverbs and small words stay when they carry voice.
- Passive is normal for processes ("the board is assembled here"). Replace it when it hides an actor the reader should know.
- Fragments and triples are allowed when the content calls for them. What is suspicious is the repetition, not the single occurrence.
- "Two items beat three" does not apply. What counts is how many things there really are.
- Dashes: none, unless a voice sample of the author uses them.
- The `eval.md` of `slop-prose` does not replace the reading check here and is not worked through in addition. From `slop-prose` the rules apply, not its procedure.

## Procedure

**0. Mode.** Write (new text), revise (a draft exists) or audit (findings only). When auditing, name each pattern with a quote and a short remedy, rewrite nothing and do not pass a verdict "written by AI". A pattern is evidence the user can check; an AI probability is a guess.

**1. Clarify and load the voice.** For whom, where does the text appear, what should the reader do or think afterwards? At most one question, and only if it does not follow from the conversation. Then the voice: if one is active or named ("in my voice", "voice: anna"), read `profile.md` and two or three samples of the matching text type from `$WLH_VOICES/<name>/` (default `~/.config/writing-like-human/voices`). If there is only a single old text, it is the voice sample. The voice beats every rule here, and the author's quirks come in at the measured density. Creating one, storage and rules: [references/voice-profile.md](references/voice-profile.md). If there is no voice and the user writes regularly, offer once to create one.

**2. Get the material.** What does only the author know? If it is missing, ask for one to three things, not more: a concrete experience, a number, a name (person, place, book, tool), an opinion they are not sure about. Without an answer, write more simply, do not invent. Placeholders like `[client name]` are better than an invented one. Without material a text cannot fully pass the reading check. Say so openly and leave the placeholders as a task for the author instead of filling them with generalities.

The length follows the material. If a word count is given and the material is thin, stay near the lower end and say so rather than padding with explanations.

**3. Fix the build, against your own default.** Models run toward the same middle, even with this skill: in the blind test almost every skill text began with a time jump and ended on a sober fact. So first note in three lines what the obvious text would do (opening, form, ending), then decide differently on at least two of these points. Then apply the counter-moves of group A below, and from group B those that fit the text type. Details per text type in [references/structure.md](references/structure.md).

**4. Write or revise.** When revising: as little as needed. Strong human sentences stay, even when they stumble.

**5. Sentence and word.** Apply the rules of `slop-prose` (or `slop-humanizer`).

**6. Check.** Measure first, then read:

```bash
python3 -I .claude/skills/writing-like-human/scripts/check.py text.md
```

The script counts, it does not judge, and its rules of thumb barely separate human and Claude on fresh texts (blind test 2: AUROC 0.57). Never write for the script: a writer who built in a parenthesis or an image to make a finding disappear was recognized by exactly that. The script finds stock phrases and build patterns; whether a text feels human, it does not say. Then the reading check below. Fix what fails and check again.

**7. Check characters.** Always, in every mode, also for pasted foreign texts:

```bash
python3 -I .claude/skills/writing-like-human/scripts/invisible_chars.py text.md
```

The script reports every invisible or swapped character with line, column, code point, name and context, in four classes: "remove" (zero-width, bidi, tag characters, variation selectors without an emoji, soft hyphen, control characters), "replace" (foreign spaces between words, Cyrillic or Greek look-alikes), "keep" (non-breaking space in "e.g.", before "%" or units, emoji sequences) and "typography" (em dash). Show the findings to the user and change nothing before they agree. After approval use `--clean`: that writes `text.cleaned.md` and lists every change (place, old character, new one, reason). Explain that list in your own words: what the character was, where it usually comes from (PDF, Word, web page, model), and that the visible text stays the same except for look-alikes. Align "keep" only on explicit request (`--spaces`); U+202F is a known trace of newer ChatGPT models but also appears correctly in typeset text. Never replace dashes mechanically; rebuild the sentence.

A clean scan does not mean "human" and not "without watermark". The watermarks of Claude, ChatGPT and Gemini sit in the word choice and cannot be checked without the vendor's key. If the user asks, say honestly what [references/watermarks.md](references/watermarks.md) says: Claude text has been marked since August 2026, this one too; light editing changes little; only sentences you reformulate yourself reliably do not carry the pattern. A duty to disclose AI use is untouched by any cleaning.

**8. Output.** The finished text. When revising, add a short note below on what changed, build first. This note is added only after the checks; the scripts get only the text. If another skill calls this one (presentation, landing page, docs prose), output only the text.

## Counter-moves, group A: derived from blind test 1, not confirmed in blind test 2

German blog, column and non-fiction texts of 250 to 400 words, humans against Claude with the same facts. What the judge named as the difference in blind test 1 and the counts there supported. On ten new texts these counter-moves did not work, and the judge recognized them as a fixed rule: chain sentences where the author writes short and hard, added images, parenthetical jokes in every text. So: use a counter-move only if the author writes that way according to the voice sample or the material, and never add anything that is not in the material (no image, no joke, no parenthesis, no explanation). The list is a collection of possibilities, not a mandatory program.

A. **Write chain sentences.** Humans: 19 words per sentence on average, every sixth sentence 30 words or more, 1.5 commas per sentence. Claude: 12 words, hardly a sentence over 30, 0.9 commas, and 17 % sentences of five words or fewer (humans 6 %). So let a thought run on in one long sentence with asides, afterthoughts and "and then", instead of chopping it into short sentences. Short sentences singly and rarely.
B. **Do not defuse.** Humans dare rough, odd, overdrawn images, wordplay, onomatopoeia and own monster words. Claude smooths them and explains the punchline. Inventing facts stays forbidden; an image, a comparison or an exaggeration is not inventing but craft. In the author's tone it may well be too much.
C. **Tell it in the order it happened.** In short texts humans order by experience and idea, with digressions; reordered chronology and an opening with the result were recognized by the judge as model. Time jumps belong in long texts (group B, point 3).
D. **No rounded ending.** No return to the image from the beginning, no closing punchline, no framing, no call to the reader the author does not have. Humans often simply stop, in the middle of the matter.
E. **Asides in the middle of the sentence.** Parentheses, afterthoughts, self-corrections ("well, that is not quite true") sit inside the sentence for humans. Claude moves them into paragraphs of their own or drops them.
F. **Choose one form and carry it through.** If the material has a form (live ticker, martial-arts metaphor, letter, list), write consistently in it instead of retelling it.
G. **Leave everyday language alone in informal texts, but enforce engineering rigor in technical texts.** "approx.", "etc.", slashes, a clumsy phrase, a filler word: acceptable in personal guides and informal lay texts. **Exception:** In technical presentations, academic defenses, engineering documentation, and scientific evaluations, clumsy phrasing and conversational slang degrade credibility. There, use formal, precise, and unambiguous domain terminology.

## Counter-moves, group B: from StoryScope

The numbers are human against AI from StoryScope, English fiction of about 5,000 words. For short non-fiction they are a transfer, not a measurement; how they transfer is in [references/structure.md](references/structure.md).

1. **Do not state the moral.** AI narrators state the theme themselves in 77 % of stories, humans in 52 %. No closing sentence that explains what it all means. No "This shows", no "In the end, it is about". The reader draws the conclusion.
2. **Leave something open.** AI resolves through inner insight in 47 % of cases ("and then she understood"), humans in 27 %. A thread stays loose, a question unanswered, an objection standing. The ending may stop in mid-thought or on a sober fact. Only what is open in the material stays open: no statement of the draft is weakened for this. And not every ending as "Whether X, I don't know yet", that is the next template.
3. **In long texts, do not tell front to back.** Humans jump in time, use flashbacks and hold back a revelation that makes the earlier part read differently. Applies to stories and long essays. In short texts exactly this was recognized as model (group A, point C).
4. **Allow a side strand.** 79 % of AI stories have none, 57 % of human ones. A digression, a parenthetical remark, an anecdote that only half belongs to the topic.
5. **Loosen the causal chain.** With AI everything follows compellingly from the previous thing, and the hero solves it alone (69 % against 46 %). Chance, luck, other people and outside circumstances may decide.
6. **Name feelings.** AI shows feeling through the body 81 % of the time (tight chest, cold sweat), humans 38 %. Humans write "I was afraid" three times as often. Fewer sensory impressions, smells only when they matter (82 % against 57 %), weather and room not as a mirror of the soul.
7. **Name real names.** Humans name concrete books, authors, brands and places almost twice as often (47 % against 24 %). Instead of "a well-known economist" the name, instead of "a big city" Leeds.
8. **Address the reader.** Humans do it in 28 % of texts, AI in 7 %. An aside to "you", a question that is not answered at once.
9. **Show ambivalence.** Humans leave the main character's decision morally mixed more often (59 % against 38 %). In non-fiction: own mistake, mixed feelings, an opinion with doubt.
10. **Less debate of principle.** With AI, dialogue serves philosophy 59 % of the time, with humans 34 %. More ordinary speech, more places, more scene.
11. **Weigh unevenly.** AI gives every point the same room and the same form. One point gets three paragraphs, another half a sentence, one drops out.
12. **Distribute tension unevenly.** Claude escalates events flatter than any other model. Something has to tip, a sentence has to surprise. A hard one-liner at the end of a paragraph is the wrong tool for this (group A, point A).

When Claude is the writer (so, usually), also note the Claude row of the fingerprint table in [references/structure.md](references/structure.md).

## Stance in non-fiction

In non-fiction AI reads impersonal and dense: fewer hedges, intensifiers and evaluations, fewer questions and personal asides, more nominalizations (Reinhart et al., PNAS 2025; Jiang and Hyland). Counter-moves:

- an evaluation you can attribute ("I find it too expensive") and a real doubt ("I am not sure this holds")
- a question to the reader or to yourself that is not answered at once
- verbs instead of empty nouns: "we migrated" instead of "we carried out the execution of the migration"
- a concrete test run or failure case instead of an abstract generalization
- precise technical terms: never soften domain terminology into casual colloquialisms in engineering contexts

## Reading check

After the script, read aloud or half aloud. Answer each question with yes or no.

1. Is there any sentence that explains the meaning of the text? Delete it.
2. Does the text end with a summary, a lesson, an outlook or a punchline? Replace with the last concrete sentence or leave open.
3. Does something stay open that a person would leave open at this point?
4. Is there at least one jump (time, place, topic) and one side thought? For very short texts (email, under 100 words) one of the two is enough.
5. Is there at least one real name, a number or a detail only this author can know, or a placeholder that explicitly asks for it?
6. Are paragraphs and sections of uneven length and uneven build?
7. Does every section have the same form (heading, three points, conclusion)? Then rebuild one.
8. Would the author recognize the text as theirs?
9. Are facts, names, numbers and quotes unchanged against the draft, and is nothing invented?
10. Does a passage sound like advertising, marketing puffery, or a corporate life lesson? Strip the fluff. For general personal writing, rewrite into what the author would tell a friend. For technical, academic, and engineering texts, rewrite into what an engineer or scientist writes in a peer-reviewed paper or technical evaluation: precise, formal, objective, data-backed, without conversational slang or colloquial shortcuts.
11. Does the text end with a question to the readers that could stand under any other post ("What do you think?")? Delete. A question or request that fits only this text may stay if it comes from the material.
12. Is there an image, a joke or an exaggeration that a careful editor would strike? If not and the tone allows it: dare one (group A, point B).
13. Do sentence length and rhythm follow the author's voice (without a voice: the content), instead of a rule? Are there no rows of short fragments as punchlines, and no comma chains where the author writes short?
14. Does the ending return to the beginning? Then end differently.
15. Do numbers, names and lists agree everywhere in the text (the same list in two sections, the same number in text and table), and has every technical term kept its fixed form? Machine text holds the tone steady and lets the facts drift.
16. Has the text added anything that is not in the material (image, joke, parenthesis, explanation, punchline)? Delete, unless the user explicitly asked for embellishment.
17. Where the author would put a link, a video or an image: is there a placeholder for the real one instead of a paraphrase?

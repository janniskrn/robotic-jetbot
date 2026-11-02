# Voice profile: how a specific person writes

The skill is general. A voice makes it personal: real texts by an author, numbers measured from them, and a short description of how they write. Voices live outside the skill and are swappable, so every user can create their own without changing the skill.

## Why

What moved anything at all in the blind tests was the voice of a real person, not a rule. With a voice sample of the author, the AI rating of a blind reader on the development texts fell from 38 to 21 (blind test 2, S3); on the holdout, version S4 with a voice sample was still at the level of Claude without the skill. There was only one sample of 250 to 450 words per author. Epoch AI (July 2026, English) measured the same on commercial detectors: without a style prompt, Pangram, GPTZero and Originality missed almost no model text (at most 0.7 %), after five real passages of an author as a template 10 to 18 %. The voice is therefore the lever with evidence, and more samples are better than one.

## Storage

```
$WLH_VOICES/                  default: ~/.config/writing-like-human/voices
  active                      one line: name of the voice that applies when none is given (optional)
  <name>/
    samples/                  5 to 20 own texts, .txt or .md, at least 200 words each
    measurement.md            produced by the script, do not edit by hand
    profile.md                written by the agent, read back by the author
```

Samples are private texts of the author. They do not belong in a repository others can read, and not in the skill folder.

**What makes a good sample:** texts the author wrote without AI help, if possible in the text type at hand (blog, email, LinkedIn, report), raw rather than edited. Dictated notes are especially good because the speaking voice is in them. Not: texts already revised with a model, press releases, joint texts.

## Creating one

1. Put the samples into `samples/`.
2. Measure: `python3 -I .claude/skills/writing-like-human/scripts/voice_profile.py $WLH_VOICES/<name>`
3. The agent reads all samples and `measurement.md` and writes `profile.md` following the template below. Every statement with a short quote from the samples.
4. The author reads `profile.md` and strikes what is wrong. Their correction beats the measurement.

## Template for profile.md

```markdown
# Voice: <name>

As of <date>, <n> samples, <words> words. Text types: ...

## In three sentences
How this person sounds, so that a friend would recognize them.

## Sentence and rhythm
Numbers from measurement.md and what they mean (short and hard, or long chains with asides, or both depending on the text type).

## Vocabulary
Favorite words, filler words, technical words, dialect, loanwords, formal or informal address. Words they never use.

## Quirks with density
For each quirk: what, one quote, how often per 1,000 words. For example:
- Own words (compounds, playful distortions): "runjumpthrow", about 2 per 1,000 words
- Writing habits: "e.g" without a period, "it's" contracted everywhere, sentences starting lowercase in chat
- Typography: emoticons at the end of a paragraph, capital letters for emphasis, straight quotation marks
- Recurring errors a reader would recognize as theirs (only those that occur at least twice)

## Opening and ending
How they start and stop, with quotes. What they never do (conclusion, question to the readers, punchline).

## Humor and stance
Whether and how they are funny, how they evaluate, how they doubt.

## Do not carry over
What is in the samples but does not belong in new texts: content, names of third parties, one-off typos.
```

## Using it

If a voice is active (file `active`, or the user names it: "in my voice", "voice: anna"), the agent reads `profile.md` and two or three samples of the matching text type in step 1. Then:

- **The voice beats every rule of the skill.** If the author writes short and hard, no chain sentences; if they end with a conclusion, the text may too.
- **Quirks at the measured density, not more often.** One own word per 1,000 words means, in a text of 300 words: one or none. Too much is a new template.
- **Own habits instead of invented errors.** Only spellings and errors the author demonstrably repeats are taken over. The agent does not build in random typos: in blind test 2 the judge recognized human texts 10 of 10 even after all errors were corrected, so errors are not what it hangs on, and they make the text worse.
- **No invented leftovers.** Where the author would put a link, a video or an image, there is a placeholder for the real one (`[Link: ...]`), no paraphrase and no artificial remnant. A judge recognized S4 texts on the holdout precisely by paraphrases at places where the original had a link.
- **Content only from the material.** The voice supplies the how, never the what.

Without a voice the skill stays general. Then at most one own word per text and only where the tone carries it; no errors, no leftovers.

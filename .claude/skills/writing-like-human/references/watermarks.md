# Watermarks in AI text

As of 2026-10-28. Research and own measurement of the original are not included in this copy. Vendor statements are marked as such, voices from the community as opinion.

## Two kinds that must not be confused

**1. Characters in the text.** Invisible or swapped Unicode characters: zero-width (U+200B to U+200D, U+2060, U+FEFF), bidi controls (U+202A to U+202E, U+2066 to U+2069), tag characters (U+E0000 to U+E007F), variation selectors (U+FE00 to U+FE0F, U+E0100 to U+E01EF; whole messages can be hidden behind a letter or emoji with these), foreign spaces (U+00A0, U+202F, U+2002 to U+200A), look-alikes from Cyrillic or Greek. They can be found and removed reliably; `scripts/invisible_chars.py` does that (check passed).

No large provider declares such characters as its watermark. Anthropic states explicitly that nothing is added and there are no hidden characters; OpenAI says the same for textGrain. What went through the press in 2025 as a "ChatGPT watermark" were narrow non-breaking spaces (U+202F) in answers of o3 and o4-mini, found by the start-up Rumi ([trendingtopics](https://www.trendingtopics.eu/startup-entdeckt-versteckte-markierungen-in-texten-von-openai-o3-und-o4-mini/), [t3n](https://t3n.de/news/openai-zeichen-chatgpt-texte-1683993/)). Rumi itself named learned typography as a possible explanation; I found a statement from OpenAI on this only second hand. Later, users reported U+202F in GPT-5 answers ([OpenAI forum](https://community.openai.com/t/gpt-5-non-reasoning-outputs-u-202f-narrow-no-break-space-instead-of-normal-spaces-breaks-text-rendering-on-macos-apps/1362321)). Such characters are therefore a trace, not a watermark: random, not encrypted, gone with search and replace, and Word or a careful typesetter sets the same character in "e.g." or "5 %".

**2. Statistical watermarks in the word choice.** Between equally good next words the model chooses not with ordinary chance but with a secret key and the preceding words. Whoever has the key calculates over enough text how likely the pattern is by chance. Foundations: Kirchenbauer et al., "A Watermark for Large Language Models", ICML 2023 ([arXiv 2301.10226](https://arxiv.org/abs/2301.10226), a green list of tokens is favored), and Dathathri et al., "Scalable watermarking for identifying large language model outputs", Nature 634, 818 to 823, October 2024 ([SynthID-Text](https://www.nature.com/articles/s41586-024-08025-4)). Nothing of this is visible in the text; no script without the key can find it.

## Who deploys what

| Provider | Since | What | Where | Who can check |
|---|---|---|---|---|
| Anthropic (Claude) | models from 2 August 2026, older ones are retrofitted | variant of SynthID-Text, plus C2PA in generated files | worldwide, all surfaces (API, claude.ai, Claude Code, Cowork, cloud partners), no opt-out | private preview of a Detection API for eligible bodies in the EU, explicitly including educational institutions |
| OpenAI (ChatGPT, Codex) | announced 5 October 2026, rollout over weeks | textGrain, with researchers from Penn and Yale | EU only, all plans; API selectable worldwide, off by default | initially selected researchers and specialist bodies |
| Google (Gemini) | 2024 | SynthID-Text | Gemini | open-source version in Hugging Face Transformers for your own models |

Sources: [Anthropic, announcement 14 August 2026](https://www.anthropic.com/news/claude-text-watermark), [Anthropic Support, model table](https://support.claude.com/en/articles/16266773-how-claude-marks-ai-generated-content), [TechCrunch on textGrain](https://techcrunch.com/2026/10/05/openai-will-start-watermarking-chatgpts-text-in-the-eu/), [Nemecek et al., arXiv 2609.09604](https://arxiv.org/abs/2609.09604). The trigger is Article 50 of the EU AI Act and the Code of Practice on Transparency of AI-Generated Content (July 2026, about 190 signatories). According to one source the Code exempts very short texts under 200 tokens.

According to the Anthropic table, Opus 5.5, Sonnet 5.5 and Haiku 5.5 carry the watermark. **Every text this skill writes or rewrites through Claude is therefore marked,** and rewriting through Claude sets the pattern anew.

## What it survives (vendor statements and studies)

- Anthropic: light rephrasing probably does not remove it completely, a full rewrite does; translations by Claude carry it; proofreading human texts usually leaves too little; for facts and code it is hardly set. A hit means "Claude processed the text", not "Claude wrote it". No minimum length is given, only: short texts are not enough.
- OpenAI: replacing 10 % of the words with synonyms lowered detection from about 92 to 66 %. Short passages, mathematics and translations are hard. A missing watermark "proves no human authorship".
- SynthID-Text, open version: light rephrasing and translation lower detection considerably; diluted with a lot of foreign text it nears chance ([arXiv 2508.20228](https://arxiv.org/abs/2508.20228)).
- Nemecek et al. (September 2026): neither "easy to remove" nor "robust" can currently be checked for the deployed systems, because no outsider has a detector. That is the real problem.

## Community tools

Looked at on 2026-10-28, code read, none of it run or installed.

| Tool | License, stars | What it really does | Local |
|---|---|---|---|
| [guillaumemeyer/watermarks-remover](https://github.com/guillaumemeyer/watermarks-remover) | MIT, 25,126 | Layer A: remove Unicode carriers from a fixed list (checkable). Layer B: rewrite by another model, "best effort". Files: C2PA, EXIF, XMP, Office properties. Contains an agent skill and an HTTP service; optional parts clone foreign research repos and download large models | yes, rewriting optionally via Ollama |
| [mikiane/claude-watermark-cleaner](https://github.com/mikiane/claude-watermark-cleaner) | no license, 151 | Remove Unicode, then rewrite by a non-Claude model; protects code, URLs and numbers. Explicitly meant as a critique of the watermark | partly |
| [wiltodelta/remove-ai-watermarks](https://github.com/wiltodelta/remove-ai-watermarks) | Apache-2.0, 6,157 | Images, video, audio, metadata; no text | yes |
| [mertizci/noai-watermark](https://github.com/mertizci/noai-watermark) | MIT, 213 | Images; no text | yes |
| Web services (claudewatermark.com, gptcleanup.com and others), StealthGPT, Human Writes | commercial | Unicode cleaning or rewriting; their "undetectable" scores come from ordinary AI detectors, not from the watermark | no, text goes to strangers |

According to [BleepingComputer (13 August 2026)](https://www.bleepingcomputer.com/news/security/ai-watermark-removers-flood-the-web-almost-none-can-prove-they-work/), none of these tools can prove that it removes a vendor watermark; a tester found in a widespread cleaner that the most common technique for hidden payloads went through unchanged. Meyer himself writes in the README that without a public detector no tool can honestly certify that the official check fails, and rewriting with a weaker model pulls quality down to its level.

## Detectors outside the vendors

Nobody outside the vendors has built or rebuilt a detector that says for a single text "carries Claude's or ChatGPT's watermark" (as of 2026-10-28). Three things come close:

- **Keyless test whether a model is marked at all:** Gloaguen, Jovanović, Staab, Vechev, "Black-Box Detection of Language Model Watermarks" (ICLR 2025, arXiv 2405.20777, code eth-sri/watermark-detection). Up to 9,000 short queries ("I ate {number} ..." with four fruits), then a permutation test for context-dependent bias. It says something about the model, nothing about a single text. Karen Spinner ([Substack, 23 August 2026](https://wonderingaboutai.substack.com/p/a-mostly-plain-language-primer-on)) found Gemini 3.5 Flash positive with it, Claude Sonnet 5, Opus 4.8 and GPT-5.2 without a finding; the Claude models tested were still from before the cutoff date, though, and the original test missed SynthID because of its rule not to mark repeated word sequences. John Wang ([blog, 12 and 20 August 2026](https://johnjwang.com/post/2026/08/12/how-claude-watermarking-probably-works/)) checked 7.2 million characters of Claude Code output for Unicode (nothing) and ran bias tests of his own, also without a clear signal.
- **Stealing the watermark:** Jovanović, Staab, Vechev, "Watermark Stealing in Large Language Models" (ICML 2024, arXiv 2402.19361): from many answers the rule behind a green-list watermark can be learned approximately, for under 50 dollars, after which spoofing and removing succeed over 80 % of the time. For SynthID-Text there is spoofing through distillation (DITTO, arXiv 2510.10987) and a theoretical weakness of the mean score (arXiv 2603.03410); no public rebuild of the Claude key exists.
- **Own keys with an open implementation:** SynthID-Text in Hugging Face Transformers and the MarkLLM toolkit create and detect watermarks with a self-chosen key on open models. Researchers and `watermarks-remover` (bench_synthid_text.py) use them to measure how much a rewrite removes. That is a proxy: the same method, but not Claude's settings and not its key.

Google's SynthID Detector (synthid.com) has been open to everyone since 7 October 2026, but checks only image, video and audio, no text ([Google](https://blog.google/innovation-and-ai/models-and-research/google-deepmind/synth-id-ai-content/), [PetaPixel](https://petapixel.com/2026/10/08/googles-synthid-ai-detector-is-now-freely-available-to-everyone/)). The statement in the watermarks-remover README that Google shut the detector down in August 2026 does not fit this.

## Second research round: is there a solution? (2026-10-28)

No, none that can be checked. The search was for a public detector and for a documented removal on the real Claude or ChatGPT watermark; GitHub sorted by recency.

- **Vendors:** Anthropic's Detection API has been in private preview since 1 September 2026 for bodies with an examination reason under the EU AI Act, with no date for broader access ([Anthropic](https://www.anthropic.com/news/claude-text-watermark), [tpsreport](https://tpsreport.news/news/anthropic-claude-watermark-verification-api)). OpenAI published a technical report on textGrain; the detector stays with selected researchers.
- **Rebuilds of the methods:** textGrain was rebuilt after the report (omarht27/textgrain-eval, shravan1996/generative-ai-text-watermarks, on small open models with own keys). That shows how the method reacts, not whether a ChatGPT text is marked.
- **Rewriting on the proxy:** A single rewrite pass with Qwen3.7 Plus brought ten of ten English reports under the threshold of the open SynthID-Text detector and kept all statements according to the review panel ([painintheagent](https://painintheagent.com/blog/text-watermark-removal-retest/), quoted in the README of balakhonoff/claude-watermark-remover). A single test, English, open key, not Claude's settings.
- **Behavior test on endpoints:** AI or Not (TolyK/ai-text-watermark-finder, MIT) claims to have checked 1.19 billion tokens across the cutoff date in August. Calibrated on four local Qwen3 endpoints, two of them with real SynthID marking, only one effect measure (Cramér's V) separated: marked 0.69 to 0.73, unmarked 0.04 to 0.05. Measured: claude-sonnet-5 0.067, claude-haiku-4-5 0.016, so close to "unmarked"; the usual p-value, in contrast, declared unmarked endpoints marked too. Their own AI detector recognized Claude prose identically before and after the cutoff (99.6 to 100 %). According to the README; time of measurement and settings not checked. The tool itself says it cannot prove a Claude watermark on a single document.
- **Tools with verification:** cyzanfar/text-watermark-remover (MIT) reports "mitigation_verified" only against published methods with a matching detector and otherwise explicitly "unverified". New removers like balakhonoff/claude-watermark-remover (MCP server, sends text via OpenRouter to foreign models) and novatechflow/ai-watermark-scrambler (local model) rewrite, but cannot document the effect on Claude.

**Decision of the owner (2026-10-28):** do not pursue it ourselves, wait for the community. Revisit as soon as one of these happens:
1. Anthropic or OpenAI open their detector or give researchers broader access, and someone publishes measurements on the real watermark.
2. An independent study measures rewriting against the vendor detector (not against the open proxy).
3. A rebuilt detector for Claude text (for example through watermark stealing) is checked on known Claude texts from before and after the cutoff date.
Search terms for the next round: "Claude watermark detection API access", "textGrain detector public", "watermark removal vendor detector study", GitHub by recency: "claude watermark", "textgrain", "synthid text detect".

**Opinions** (not checked): watermarks are only a tick box for the EU duty (Ghorbaninia, Meyer); a duty to mark mainly creates extra model calls for rewriting and thus more energy use (README mikiane); a public detector would devalue the watermark itself because one could practice against it (researchers in The New Stack).

Why the skill adopts none of these: layer A is covered by `invisible_chars.py` with the standard library and a passed test of its own; foreign code with a service, hooks and downloaded models would bring supply-chain risk without added value for text. Before any later adoption, check with `skillspector`.

## What the skill does and does not do

- It scans every text for characters (step 7 in SKILL.md), shows the findings and cleans only after approval, with a list of every change.
- It never claims that a text is free of watermarks or human. A clean scan only says: no conspicuous characters.
- Statistical watermarks: it explains that Claude text is marked, that light editing changes little, and that only a text the author reformulates themselves reliably does not carry the pattern. Real sentences of the author's own (step 2, material) are therefore the strongest lever here too. The skill does not build in automatic rewriting by a second model: the effect cannot be measured, the quality measurably drops.
- Where AI use must be disclosed (term paper, exam, publisher, authority), cleaning changes nothing about that duty. The skill does not help to get around a required disclosure.

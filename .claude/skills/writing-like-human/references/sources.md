# Sources

Checked on 2026-10-27. Numbers are taken from the papers, not recomputed.

## StoryScope (main source)

Jenna Russell, Rishanth Rajendhran, Mohit Iyyer (University of Maryland), John Wieting (Google DeepMind): *StoryScope: Investigating idiosyncrasies in AI fiction*. Preprint, arXiv [2604.03136](https://arxiv.org/abs/2604.03136), April 2026, not yet peer reviewed. Code and data: [github.com/jenna-russell/storyscope](https://github.com/jenna-russell/storyscope).

**Setup.** 10,272 human short stories from Books3; for each, Claude Sonnet 4.6, GPT 5.4, Gemini 3 Flash, DeepSeek V3.2 and Kimi K2.5 wrote a version from the same prompt. 61,608 stories, 4,753 words on average. A language model (Gemini 3 Flash) rated each story on 304 narrative features in ten dimensions (character, relationships, event, plot, structure, setting, time, revelation, perspective, style). Agreement with humans κ = 0.84.

**Result.** Narrative features only, without style: 93.2 % macro F1 for human against AI, 68.4 % for the question which of the six sources wrote it. With style 96.0 % and 77.3 %. 30 core features alone: 84.8 %. Text-based classifiers on the raw text (ModernBERT, TF-IDF) reach 99.7 to 99.9 %, the zero-shot detector Binoculars 55.9 %.

**Surface revision barely helps.** 278 Gemini stories were cleaned of clichés, filler sentences and bombast with LAMP. The narrative features still recognized them at 93.9 % instead of 95.5 %.

**Rarity.** Human stories lie rarer in feature space (percentile 0.71 against 0.49). For 57.8 % of the prompts the human version is the most unusual of the six. The five models form a common cloud, the humans a separate, broader one.

**Core features (table 15, human against AI, mean over five models).** Scales 1 to 5, otherwise share of stories.

| Feature | Human | AI |
|---|---|---|
| Theme and moral explicit (1-5) | 3.28 | 3.94 |
| Weight of moral questions (1-5) | 3.26 | 3.68 |
| Thematic closure (1-5) | 4.41 | 4.74 |
| Narrator comments on the theme | 52 % | 77 % |
| Dialogue as a debate of principle | 34 % | 59 % |
| Allusions only hinted | 50 % | 72 % |
| Feeling through the body | 38 % | 81 % |
| Setting mirrors inner life (1-5) | 3.58 | 4.07 |
| Nature and environment emphasized (1-5) | 2.83 | 3.21 |
| Smells | 57 % | 82 % |
| Density of sensory impressions (1-5) | 3.66 | 3.93 |
| Depth of interiority (1-5) | 3.67 | 3.93 |
| Continuous causal chain (1-5) | 3.92 | 4.20 |
| Resolution through the main character's decision | 46 % | 69 % |
| Character introduced by outside description | 30 % | 52 % |
| No side plot | 57 % | 79 % |
| Resolution through inner insight | 27 % | 47 % |
| Investment in characters before the danger (1-5) | 2.76 | 2.99 |
| Concrete, named references to other works | 47 % | 24 % |
| Mix of open and hinted references | 37 % | 16 % |
| Breaking the fourth wall (mean) | 0.67 | 0.39 |
| Direct address of the reader (mean) | 0.28 | 0.07 |
| Revelation recasts the earlier part (1-5) | 3.28 | 2.95 |
| Time jumps (1-5) | 2.40 | 2.12 |
| Flashbacks and flash-forwards (1-5) | 2.58 | 2.31 |
| Side plot mirrors the theme | 42 % | 21 % |
| Main character morally mixed | 59 % | 38 % |
| Feelings named | 29 % | 8 % |

**Limits.** English fiction, long texts, one model as the rater, preprint. For non-fiction, and for German, the transfer is a reasoned assumption, not a measurement. The direction (build gives more away than words) is supported by the other sources.

## Further work

- **LAMP.** Tuhin Chakrabarty, Philippe Laban, Chien-Sheng Wu: *Can AI writing be salvaged?* CHI 2025, [arXiv 2409.14509](https://arxiv.org/abs/2409.14509). 18 professional authors revised 1,057 paragraphs from GPT-4o, Claude 3.5 Sonnet and Llama 3.1. Seven error classes: cliché, unnecessary explanation, bombast, bad sentence structure, lack of concreteness, awkward word choice, tense shift. Most frequent: word choice 28 %, sentence structure 20 %, unnecessary explanation 18 %, cliché 17 %. The three models differed little.
- **Reinhart et al.** *Do LLMs write like humans? Variation in grammatical and rhetorical styles*, PNAS 2025, [doi 10.1073/pnas.2422455122](https://doi.org/10.1073/pnas.2422455122). Biber features; instruction-tuned models deviate more than base models, denser and more information-heavy, less involved. Overview of further findings (fewer hedges, evaluations, questions, personal asides; more nominalization): [refsmmat.com/notebooks/llm-style](https://www.refsmmat.com/notebooks/llm-style.html).
- **Russell, Karpinska, Iyyer.** *People who frequently use ChatGPT for writing tasks are accurate and robust detectors of AI-generated text*, ACL 2025, [arXiv 2501.15654](https://arxiv.org/abs/2501.15654). Five heavy users were right by majority on 299 of 300 non-fiction texts, even after paraphrase and "humanizer". They watch for AI vocabulary, but also for formality, originality and clarity.
- **Detectors.** Karr, Khvatskii, Hua, Chawla: *Why AI Detection Fails for Academic Integrity*, [arXiv 2608.11256](https://arxiv.org/abs/2608.11256) (2026). Commercial detectors (not named in the abstract) flag 9 to 15 % of unchanged abstracts from 2023 to 2025, markedly more outside the STEM fields. After a humanizer (Undetectable AI) fewer than 4 % of the AI texts are still recognized. Xu, Zhong, Raghunathan, Fang, Kolter report, per a secondary source ([aiweekly](https://aiweekly.co/node/10334), original not read), that GPTZero and Pangram mostly classify texts from base models as human. Vendor figures contradict each other.
- **Fine-tuning.** According to the StoryScope introduction, fine-tuning on human style lowers the detection rate in creative writing from 97 % to 3 % (Chakrabarty et al. 2026, original not read).
- **German-language sources.** Writing center of the University of Konstanz, *Typische Schwächen KI-generierter Texte* (2024, CC BY 4.0): arguments listed at the same rank ("first, second"), introduction and ending unrelated, the same thought in several places, switching between present and past tense, a paragraph sounds like an ending and then it goes on. [t3n](https://t3n.de/news/ki-texte-erkennen-floskeln-buzzwords-gedankenstriche-chatgpt-1745388/): stock phrases, dashes, sentences of equal length, hardly any coinages and colloquial language.
- **Wikipedia.** [Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing), basis of `slop-humanizer`.

## Origin of the idea

A short video (Ben Gusberg) recommended loading StoryScope into a model and letting it build a "human writer" skill. This skill is the worked-out version, with the numbers from the paper instead of from the video.

## Detectors compared (as of 2026-10-28)

- **Jabarian and Imas, "Artificial Writing and Automated Detection"** (Chicago Booth, BFI WP 2025-116, NBER w34223): 1,992 passages in six everyday genres, four frontier models. Pangram with false-alarm and miss rate near zero, also on short texts and humanizers, the only tool under a false-alarm limit of 0.5 %; OriginalityAI and GPTZero behind it; the open RoBERTa detector weak. Only summary and short version read.
- **Epoch AI, Data Insight of 15 July 2026** (English, 495 human texts from before November 2022, Claude Opus 4.8, GPT-5.5, Gemini 3.1 Pro): false alarms Pangram 0 %, GPTZero 0 %, Originality 3.8 %. Missed model texts without a style prompt at most 0.7 %, with five real passages of an author as a style template 10.1 % (Pangram), 10.8 % (GPTZero), 17.8 % (Originality); for scientific texts up to 25 to 29 %. Read.
- **Own measurement, blind test 2 (German, 200 to 400 words):** Claude as a blind reader separates reliably (10 of 10 in pairs, single judgment AUROC 0.9 to 1.0); Binoculars and Fast-DetectGPT with Qwen2.5-1.5B 0.66 and 0.67, XLM-R for German 0.68, Qwen3.8-27B as judge 4 of 10.

## Watermarks in text (as of 2026-10-28)

In detail, with tools and vendor status, in [watermarks.md](watermarks.md). The supporting evidence:

- **Kirchenbauer et al., "A Watermark for Large Language Models"** (ICML 2023, arXiv 2301.10226): green list of tokens, statistical test with a p-value. Abstract read.
- **Dathathri et al., "Scalable watermarking for identifying large language model outputs"** (Nature 634, 818 to 823, 2024): SynthID-Text, only the sampling changes, detection without the model. Abstract read.
- **Anthropic, "Claude text watermark"** (14 August 2026, amended 1 September) and support article 16266773: variant of SynthID-Text, models from 2 August 2026, no hidden characters, Detection API in private preview. Read.
- **OpenAI textGrain** (5 October 2026): only from TechCrunch, OpenAI's help page blocked retrieval. 10 % synonyms lower detection from about 92 to 66 %.
- **Nemecek, Chaudhary, Ayday, "Watermarks Without Verification"** (arXiv 2609.09604, September 2026): the effect and robustness of the deployed watermarks cannot be checked from outside. Abstract read.
- **Own measurement, character check 1:** `invisible_chars.py` finds 405 of 405 inserted characters, zero false alarms; six fresh Claude texts without a single conspicuous character.

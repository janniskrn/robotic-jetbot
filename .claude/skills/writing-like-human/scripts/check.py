#!/usr/bin/env python3
"""Finds known AI patterns (stock phrases, sentence patterns, labels, closing summary). Not a detector.

Usage: python3 -I check.py text.md   (or text on stdin)
Output: findings marked  ! clustered  ~ single  § house rule  . info
Blind test 2 (2026-10-28): the earlier rhythm rules of thumb (sentence lengths, chain sentences, particles,
"human signals") did not separate human and Claude on fresh texts (AUROC 0.57) and were removed.
What remains only finds what it names.
"""
import re
import sys

ABBREV = ["e.g.", "i.e.", "etc.", "vs.", "Mr.", "Ms.", "Mrs.", "Dr.", "Prof.", "No.", "Fig.", "approx.", "incl.",
          "St.", "Jr.", "Sr.", "Inc.", "Co.", "cf.", "al."]

CONTRAST = [
    r"\bnot (?:just|only|merely|simply)\b[^.!?]{1,120}\bbut (?:also )?\b",
    r"\b(?:isn't|is not|wasn't|was not|aren't|are not)\b[^.!?]{1,60}[.,;] (?:it's|it is|it was|they're|they are)\b",
    r"\bit(?:'s| is) not (?:about|just)\b[^.!?]{1,80}[.,;] ?(?:it(?:'s| is)|but)\b",
    r"(?:^|[.!?]\s)Not (?:because|for|about|to)\b[^.!?]{1,60}\. (?:Because|But|It|Rather)\b",
]

PHRASES = [
    r"in today's (?:\w+[ -])*?(?:world|age|landscape|era)", r"in a world where", r"imagine (?:a|that|if)\b",
    r"have you ever (?:wondered|asked yourself)", r"let's (?:dive|delve|unpack|explore)", r"dive (?:in|into)\b",
    r"it's no secret", r"we all know", r"here's the thing", r"it's worth noting", r"when it comes to",
    r"at its core", r"the truth is", r"let that sink in", r"at the end of the day",
    r"\bfurthermore\b", r"\bmoreover\b", r"\badditionally\b", r"\bnevertheless\b",
    r"it is (?:important|crucial|essential) to (?:note|remember|understand|recognize)",
    r"plays? an? (?:crucial|key|vital|pivotal|important) role", r"last but not least",
    r"in conclusion", r"to sum up", r"in summary", r"all in all", r"one thing is (?:clear|certain)",
    r"the future (?:is|looks|belongs)", r"here to stay", r"stay tuned", r"only time will tell",
    r"studies (?:show|prove|suggest)", r"experts (?:agree|say)", r"the (?:data|numbers) (?:show|speak|tell)",
    r"game[- ]?changer", r"next level", r"unlock(?:s|ing)? (?:the )?(?:full )?potential", r"integral part",
    r"a testament to", r"the key to", r"offers the opportunity", r"is characterized by",
    r"i hope this (?:helps|finds you)", r"great question", r"let me know if", r"feel free to",
    r"i'm (?:excited|thrilled|delighted) to (?:announce|share)", r"what do you think\?", r"thoughts\?", r"agree\?",
    r"spoiler:", r"plot twist",
]

WORDS = [
    "seamless", "holistic", "tailored", "innovative", "revolutioniz", "groundbreaking", "cutting-edge", "essential",
    "multifaceted", "profound", "synergy", "synergies", "milestone", "cornerstone", "underscore", "highlight",
    "diverse", "comprehensive", "exciting", "valuable", "robust", "delve", "tapestry", "leverag", "pivotal",
    "testament", "showcase", "foster", "meticulous", "landscape", "elevate", "empower", "crucial", "vibrant",
    "journey", "unlock", "navigate", "realm",
]

CLOSING = [r"\b(?:in conclusion|to sum up|in summary|ultimately|overall|the bottom line|the takeaway)\b",
           r"(?:^|[.!?]\s)in the end\b", r"\bthis (?:shows|proves|teaches|reminds)\b", r"\bthe lesson\b",
           r"\bat the end of the day\b"]


def clean(text):
    text = re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.S)
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    text = re.sub(r"`[^`]*`", "", text)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"\[[^\]]{3,}\]", "", text)  # placeholders for the author
    return text


def sentences(paragraph):
    s = paragraph
    for a in ABBREV:
        s = s.replace(a, a.replace(".", "§"))
    parts = re.split(r"(?<=[.!?…])\s+(?=[\"'(A-Z0-9])", s)
    return [t.replace("§", ".").strip() for t in parts if re.search(r"\w", t)]


def words(t):
    return re.findall(r"[\w'-]+", t)


def short(t, n=90):
    t = " ".join(t.split())
    return t if len(t) <= n else t[: n - 1] + "…"


def main():
    raw = open(sys.argv[1], encoding="utf-8").read() if len(sys.argv) > 1 else sys.stdin.read()
    text = clean(raw)
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]
    headings = [b for b in blocks if b.startswith("#")]
    list_items = sum(1 for z in text.splitlines() if re.match(r"\s*(?:[-*•]|\d+\.)\s", z))
    # Short blocks without end punctuation are subheadings, table cells or labels, not paragraphs.
    # Without this filter a report (analysis, 2026-10-27) counted every heading as a punchline.
    titles = [b for b in blocks if not b.startswith("#") and len(words(b)) <= 12
              and not re.search(r"[.!?…\"”)]\s*$", b)]
    paragraphs = [b for b in blocks if not b.startswith("#") and b not in titles
                  and not re.match(r"\s*(?:[-*•·]|\d+\.)\s", b)]
    all_sentences = [s for a in paragraphs for s in sentences(a)]
    w = words(text)
    nw = max(len(w), 1)
    per1000 = lambda n: n * 1000 / nw
    out = []

    def finding(mark, title, details=()):
        out.append(f"{mark} {title}")
        out.extend(f"    {d}" for d in details)

    punchlines = [a for i, a in enumerate(paragraphs) if i and len(sentences(a)) == 1 and len(words(a)) <= 8
                  and len(words(paragraphs[i - 1])) > 15]
    if len(punchlines) >= 2:
        finding("!", f"{len(punchlines)} one-liners as punchline after a longer paragraph",
                [short(p) for p in punchlines[:4]])

    # punctuation and form
    dashes = re.findall(r"—|(?<!\d)–|–(?!\d)|(?<=\S)[ \t]--?[ \t](?=\S)", text)
    if dashes:
        finding("§", f"{len(dashes)} dashes (house rule: none; not an AI marker, 3 of 8 human texts had some)")
    reveals = [s for s in all_sentences if re.match(r"^[^:,.!?]{2,40}:\s+\S", s) and len(words(s.split(":")[0])) <= 4]
    if reveals:
        finding("!" if len(reveals) >= 2 else "~", f"{len(reveals)} colon reveals", [short(s) for s in reveals[:4]])
    question_answer = [f"{a} {b}" for a, b in zip(all_sentences, all_sentences[1:])
                       if a.endswith("?") and len(words(a)) <= 5 and len(words(b)) <= 8]
    if question_answer:
        finding("~", f"{len(question_answer)} short question with an instant answer",
                [short(x) for x in question_answer[:3]])
    emojis = re.findall(r"[\U0001F300-\U0001FAFF☀-➿←-⇿]", text)
    if emojis:
        finding("~", f"{len(emojis)} emojis or arrows")
    bold = re.findall(r"\*\*[^*]+\*\*", text)
    if len(bold) >= 3:
        finding("~", f"{len(bold)} bold passages")
    if headings and len(paragraphs) / len(headings) < 2:
        finding("~", f"{len(headings)} headings on {len(paragraphs)} paragraphs")
    if list_items and list_items > len(all_sentences) / 2:
        finding("~", f"{list_items} list items against {len(all_sentences)} sentences of running text")
    # bullet with a label: "- **Short title:** an explanatory sentence", almost every bullet in AI reports
    labels = [z for z in text.splitlines()
              if re.match(r"\s*(?:[-*•·]|\d+\.)?\s*\**[A-Z][^:.!?]{2,50}?\**\s*:\**\s+\S", z)
              and len(words(z.split(":")[0])) <= 7 and len(words(z.split(":", 1)[1])) >= 5]  # not "Section 1: Title"
    if len(labels) >= 5:
        finding("!" if len(labels) >= 10 else "~", f'{len(labels)} bullets of the pattern "Label: explanation"',
                [short(e, 60) for e in labels[:3]])
    versus = re.findall(r"^[^\n.]{3,60}\bvs\.?\s[^\n.]{3,60}$", text, re.M)
    if len(versus) >= 2:
        finding("~", f'{len(versus)} headings or labels "X vs. Y"', [short(g, 60) for g in versus[:3]])

    # patterns
    contrast = [m.group(0) for p in CONTRAST for m in re.finditer(p, text, re.I)]
    if contrast:
        finding("!" if len(contrast) >= 2 else "~", f"{len(contrast)} contrast formulas (not X, but Y)",
                [short(k) for k in contrast[:5]])
    phrases = [m.group(0) for p in PHRASES for m in re.finditer(p, text, re.I)]
    if phrases:
        finding("!" if len(phrases) >= 3 else "~", f"{len(phrases)} stock phrases",
                sorted(set(f.lower() for f in phrases))[:12])
    inflated = [m.group(0) for x in WORDS for m in re.finditer(r"\b" + x + r"\w*", text, re.I)]
    if inflated:
        finding("!" if per1000(len(inflated)) > 6 else "~", f"{len(inflated)} inflated words",
                [", ".join(sorted(set(x.lower() for x in inflated)))])
    triples = re.findall(r"\b[\w-]+, [\w-]+,? (?:and|or) [\w-]+\b", text)
    if nw >= 200 and per1000(len(triples)) > 5:
        finding("~", f"{len(triples)} triples ({per1000(len(triples)):.1f} per 1,000 words)",
                [short(d) for d in triples[:4]])

    # ending
    if paragraphs:
        ending = "\n".join(paragraphs[-2:])
        if any(re.search(p, ending, re.I | re.M) for p in CLOSING):
            finding("!", "closing paragraph sums up or announces a lesson", [short(ending)])
        if len(paragraphs) >= 2 and len(words(paragraphs[-1])) <= 8 and len(words(paragraphs[-2])) > 15:
            finding("!", "text ends with a one-liner as punchline", [short(paragraphs[-1])])
        if re.search(r"\?\s*\W*$", ending) and re.search(r"\b(?:you|your|y'all|everyone|folks)\b", ending, re.I):
            finding("~", "ending with a question to the readers (suspicious as a mandatory formula)")

    questions = [x for x in all_sentences if x.endswith("?")]
    finding(".", f"Questions: {len(questions)} - words {len(w)} - sentences {len(all_sentences)} - "
                 f"paragraphs {len(paragraphs)} - titles and cells {len(titles)}")

    print("\n".join(out))
    print("\nMarks: ! clustered  ~ single  § house rule  . info. Not a detector: no finding does not mean human,"
          " a finding does not mean AI. Never write for the script; use the reading check from SKILL.md.")


if __name__ == "__main__":
    main()

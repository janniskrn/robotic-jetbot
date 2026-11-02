#!/usr/bin/env python3
"""Measures from real texts of an author how they write. Basis for the profile.md of a voice.

Usage: python3 -I voice_profile.py <voice-folder>
Reads <folder>/samples/*.txt and *.md, writes <folder>/measurement.md. If the samples sit in subfolders
(e.g. samples/core, samples/term-paper), each group is measured on its own and shown side by side:
what is in all groups is the voice; what is only in revised texts is often the trace of the tool. The rest
of profile.md (tone, humor, quirks with examples) is written by the agent following references/voice-profile.md.
Rates per 1,000 words, so the agent can place quirks at the same density, not more often.
"""
import collections
import pathlib
import re
import statistics
import sys

STOP = set("""the a an and or but i you he she it we they this that these those of to in on at for with as by from is
are was were be been am do does did have has had will would can could not no so if then than too very just also
my your his her its our their me him us them what who which when where how why there here about into over""".split())
ABBREV = ["e.g.", "i.e.", "etc.", "vs.", "Mr.", "Ms.", "Mrs.", "Dr.", "Prof.", "No.", "approx.", "incl."]


def sentences(text):
    s = text
    for a in ABBREV:
        s = s.replace(a, a.replace(".", "§"))
    return [t.replace("§", ".").strip() for t in re.split(r"(?<=[.!?…])\s+", s) if re.search(r"\w", t)]


def words(t):
    return re.findall(r"[\w'’-]+", t)


def per1000(n, nw):
    return f"{n * 1000 / nw:.1f}"


def read_folder(d):
    return sorted(list(d.glob("*.txt")) + list(d.glob("*.md")))


def main():
    folder = pathlib.Path(sys.argv[1])
    root = folder / "samples"
    groups = [(d.name, read_folder(d)) for d in sorted(root.iterdir()) if d.is_dir() and read_folder(d)] \
        if root.exists() else []
    if not groups:
        groups = [("all", read_folder(root))] if root.exists() else []
    if not any(p for _, p in groups):
        sys.exit(f"no samples in {root}")
    lines = [f"# Measurement: {folder.name}", ""]
    for name, samples in groups:
        lines += measure(name, samples, len(groups) > 1)
    (folder / "measurement.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{folder / 'measurement.md'} written ({', '.join(f'{n}: {len(p)} samples' for n, p in groups)})")


def measure(name, samples, several):
    texts = [p.read_text(encoding="utf-8") for p in samples]
    everything = "\n\n".join(texts)
    w = words(everything)
    nw = len(w)
    s = [x for t in texts for x in sentences(t)]
    sl = [len(words(x)) for x in s]
    paragraphs = [a for t in texts for a in re.split(r"\n\s*\n", t) if a.strip()]
    pl = [len(words(a)) for a in paragraphs]

    def count(pattern, flags=0):
        return len(re.findall(pattern, everything, flags))

    def rate(pattern, flags=0):
        return per1000(count(pattern, flags), nw)

    # patterns are computed here: backslashes inside f-string expressions fail on Python before 3.12
    r_paren = rate(r"[(]")
    r_ellipsis = rate(r"[.][.][.]|…")
    r_dash = rate(r"—|(?<![0-9])–|(?<=\S) - (?=\S)")
    r_emoticon = rate(r"[:;]-?[)(DPp]|[\U0001F300-\U0001FAFF]")
    r_caps = rate(r"\b[A-Z]{4,}\b")
    n_contraction = count(r"[A-Za-z][’'](?:s|t|re|ve|ll|d|m)\b")
    n_eg_dots = count(r"e[.]g[.]")
    n_eg_bare = count(r"\be[.]?g\b(?![.])")
    n_and_but = count(r"(?:^|[.!?]\s)(?:And|But)\b", re.M)
    h = "###" if several else "##"
    z = ([f"## Group {name}", ""] if several else []) + [
        f"{len(samples)} samples, {nw} words. Below about 3,000 words the rates are rough.", "",
        f"{h} Sentence and paragraph", "",
        f"- Sentence length: mean {statistics.mean(sl):.1f}, median {statistics.median(sl):.0f}, "
        f"90 % of sentences up to {sorted(sl)[int(len(sl) * 0.9) - 1]} words",
        f"- Share of sentences up to 5 words: {sum(x <= 5 for x in sl) / len(sl):.0%}, "
        f"from 30 words: {sum(x >= 30 for x in sl) / len(sl):.0%}",
        f"- Commas per sentence: {everything.count(',') / len(s):.2f}",
        f"- Paragraph length: mean {statistics.mean(pl):.0f} words, one-line paragraphs {sum(x <= 8 for x in pl) / len(pl):.0%}",
        f"- Sentence starts in lowercase: {sum(1 for x in s if x[:1].islower()) / len(s):.0%}",
        "", f"{h} Marks per 1,000 words", "",
        f"- Questions {per1000(sum(x.endswith('?') for x in s), nw)}, exclamations {per1000(sum(x.endswith('!') for x in s), nw)}, "
        f"parentheses {r_paren}, ellipses {r_ellipsis}",
        f"- Dashes {r_dash}, colons {per1000(everything.count(':'), nw)}, "
        f"semicolons {per1000(everything.count(';'), nw)}",
        f"- Emoticons {r_emoticon}, WORDS IN CAPITALS {r_caps}",
        f"- Quotation marks: straight {everything.count(chr(34)) // 2}, curly {everything.count(chr(8220))}",
        "", f"{h} Writing habits (counts, not judgments)", "",
        f"- Contractions (it's, don't, I'm) {n_contraction}, e.g. with periods {n_eg_dots}, without {n_eg_bare}",
        f"- Starting sentences with And or But {n_and_but}",
        "", f"{h} Long and compound words (candidates for own words, check per sample)", "",
        "- " + ", ".join(sorted({x for x in w if len(x) >= 16 or x.count('-') >= 2})[:40]),
        "", f"{h} Recurring words and phrases (across several samples)", ""]
    per_sample = [set(x.lower() for x in words(t)) for t in texts]
    multi = collections.Counter(x for st in per_sample for x in st if x not in STOP and len(x) > 3)
    z.append("- Words in at least half of the samples: " +
             ", ".join(x for x, n in multi.most_common(60) if n >= max(2, len(texts) / 2))[:600])
    grams = collections.Counter()
    for t in texts:
        ww = [x.lower() for x in words(t)]
        grams.update({" ".join(ww[i:i + 3]) for i in range(len(ww) - 2)})
    z.append("- Three-word sequences in several samples: " +
             "; ".join(g for g, n in grams.most_common(400) if n >= 2 and not set(g.split()) <= STOP)[:600])
    z += ["", f"{h} Openings and endings", ""]
    for p, t in zip(samples, texts):
        ss = sentences(t)
        if ss:
            z.append(f"- {p.name}: opening \"{' '.join(ss[0].split())[:120]}\" - ending \"{' '.join(ss[-1].split())[:120]}\"")
    return z + [""]


if __name__ == "__main__":
    main()

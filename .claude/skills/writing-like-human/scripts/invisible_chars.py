#!/usr/bin/env python3
"""Finds invisible and unusual Unicode characters in a text and cleans only on request.

Usage:
  python3 -I invisible_chars.py text.md                  report findings, change nothing
  python3 -I invisible_chars.py text.md --clean          write a cleaned version (text.cleaned.md or -o target)
                                                         and list every change (line:column, old -> new, reason)
  --spaces        also turn typographically justified non-breaking spaces (class "keep") into normal ones
  --typography    also align typography as far as mechanically safe
Exit 0: nothing to remove or replace. Exit 1: findings. Exit 2: usage error.

Classes:
  remove      invisible and without a job: zero-width, bidi controls, tag characters, variation selectors after letters,
              soft hyphen, control characters, private and unassigned code points
  replace     looks like an ordinary character and is another: foreign spaces between words,
              look-alikes from Cyrillic, Greek, full-width, non-breaking hyphens
  keep        typographically justified: non-breaking space in "e.g.", before units, emoji sequences
  typography  matter of style, no trace: em dash (house rule, rebuild the sentence)

Statistical watermarks (SynthID-Text, textGrain) sit in the word choice; this script does not see them.
"""
import collections
import pathlib
import sys
import unicodedata

ABBREV = set("""e i g a o d s S v Mr Mrs Ms Dr Prof No Nos p pp Fig Figs vs etc approx incl max min Co Inc Jr Sr St Vol
Ch cf al Ave Blvd Capt Gen Gov Sen Rep""".split())
UNITS = set("""% ‰ ° € $ £ km kg m cm mm g l ml h min s ms MB GB TB KB EUR USD CHF CHF percent euros dollars
pages words points pt px""".split())
SPACE_PROTECTED = {0x00A0, 0x202F, 0x2009, 0x2007, 0x200A}
INVISIBLE_LETTER = {0x034F, 0x115F, 0x1160, 0x17B4, 0x17B5, 0x3164, 0xFFA0}
LOOKALIKES = dict(zip(
    "АВЕКМНОРСТХаеорсхуіјѕԁԛԝІЈЅҮΑΒΕΖΗΙΚΜΝΟΡΤΥΧοιν",
    "ABEKMHOPCTXaeopcxyijsdqwIJSYABEZHIKMNOPTYXoiv"))


def is_emoji(c):
    cp = ord(c)
    return (cp >= 0x1F000 and cp < 0x1FB00) or 0x2190 <= cp <= 0x21FF or 0x2300 <= cp <= 0x27BF \
        or 0x2B00 <= cp <= 0x2BFF or cp in (0xA9, 0xAE, 0x203C, 0x2049, 0x2122, 0x2139, 0x3030, 0x303D, 0x3297, 0x3299)


def is_vs(cp):
    return 0xFE00 <= cp <= 0xFE0F or 0xE0100 <= cp <= 0xE01EF


def is_latin(c):
    return unicodedata.name(c, "").startswith("LATIN")


def word_around(t, i):
    a = i
    while a > 0 and (t[a - 1].isalpha() or unicodedata.category(t[a - 1]) in ("Mn", "Cf")):
        a -= 1
    b = i + 1
    while b < len(t) and (t[b].isalpha() or unicodedata.category(t[b]) in ("Mn", "Cf")):
        b += 1
    return t[a:b]


def space_reason(t, i):
    """Reason why a non-breaking space makes typographic sense here, else None."""
    before, after = t[:i], t[i + 1:]
    tok_before = before.split()[-1] if before.split() else ""
    tok_after = after.split()[0] if after.split() else ""
    if tok_before.endswith(".") and (tok_before[:-1].split(".")[-1] in ABBREV or len(tok_before.rstrip(".")) == 1):
        return "inside an abbreviation or after an initial"
    if tok_before.endswith(".") and tok_before[:-1].isdigit():
        return "after an ordinal number"
    if tok_before[-1:] in "§€$£" or tok_before in ("No.", "p.", "pp.", "Fig.", "Art."):
        return "between sign and number"
    if tok_before[-1:].isdigit() and (tok_after[:1].isdigit() or tok_after.rstrip(".,;:)") in UNITS
                                      or tok_after[:1] in "%‰°€$£"):
        return "between number and unit"
    return None


def scan(t):
    """Yields per finding (index, class, replacement, reason)."""
    for i, c in enumerate(t):
        cp = ord(c)
        if c in "\n\t\r" or (32 <= cp < 127):
            continue
        cat = unicodedata.category(c)
        prev = t[i - 1] if i else ""
        nxt = t[i + 1] if i + 1 < len(t) else ""
        if cat == "Cc":
            yield i, "remove", "", "control character"
        elif 0xE0000 <= cp <= 0xE007F:
            j = i
            while j > 0 and 0xE0000 <= ord(t[j - 1]) <= 0xE007F:
                j -= 1
            if j > 0 and ord(t[j - 1]) == 0x1F3F4 and i - j < 8:
                yield i, "keep", c, "part of a flag sequence"
            else:
                yield i, "remove", "", "tag character, can carry hidden data"
        elif is_vs(cp):
            if cp in (0xFE0E, 0xFE0F) and prev and (is_emoji(prev) or prev in "#*0123456789") and not is_vs(ord(prev)):
                yield i, "keep", c, "emoji presentation"
            else:
                yield i, "remove", "", "variation selector without an emoji, known carrier of hidden data"
        elif cp == 0x200D:
            left = t[i - 2] if i >= 2 and (ord(prev) == 0xFE0F or 0x1F3FB <= ord(prev) <= 0x1F3FF) else prev
            if left and is_emoji(left) and nxt and is_emoji(nxt):
                yield i, "keep", c, "joins an emoji sequence"
            else:
                yield i, "remove", "", "zero-width joiner outside an emoji"
        elif cp == 0x00AD:
            yield i, "remove", "", "soft hyphen (hyphenation, often from PDF)"
        elif cp == 0xFEFF and i == 0:
            yield i, "remove", "", "byte order mark at the start of the file"
        elif cat == "Cf" or cp in INVISIBLE_LETTER:
            yield i, "remove", "", "invisible format character"
        elif cat == "Co":
            yield i, "remove", "", "private code point without a defined meaning"
        elif cat == "Cn":
            yield i, "remove", "", "unassigned code point"
        elif cat in ("Zl", "Zp"):
            yield i, "replace", "\n", "line or paragraph separator instead of a line break"
        elif cat == "Zs":
            reason = space_reason(t, i) if cp in SPACE_PROTECTED else None
            if reason:
                yield i, "keep", " ", f"non-breaking space {reason}"
            else:
                yield i, "replace", " ", "foreign space"
        elif cp in (0x2010, 0x2011):
            yield i, "replace", "-", "hyphen variant, hardly typeable on keyboards"
        elif c in LOOKALIKES:
            w = word_around(t, i)
            if any(is_latin(x) for x in w):
                yield i, "replace", LOOKALIKES[c], "look-alike inside a Latin word"
        elif 0xFF01 <= cp <= 0xFF5E or 0x1D400 <= cp <= 0x1D7FF:
            yield i, "replace", unicodedata.normalize("NFKC", c), "look-alike (full-width or mathematical)"
        elif cp == 0x2014 or (cp == 0x2013 and prev == " " and nxt == " " and not (t[i - 2:i - 1].isdigit()
                                                                                    and t[i + 2:i + 3].isdigit())):
            yield i, "typography", c, "dash (house rule: rebuild the sentence, do not replace mechanically)"


def visible(s):
    return "".join(c if c in "\n" or (unicodedata.category(c)[0] not in "CZ" or c == " ") else f"<U+{ord(c):04X}>"
                   for c in s).replace("\n", "~")


def position(t, i):
    line = t.count("\n", 0, i) + 1
    return line, i - (t.rfind("\n", 0, i) + 1) + 1


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    if "-o" in args:
        k = args.index("-o")
        target = pathlib.Path(args[k + 1])
        args = args[:k] + args[k + 2:]
    else:
        target = None
    if len(args) != 1 or flags - {"--clean", "--spaces", "--typography"}:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    source = pathlib.Path(args[0])
    t = source.read_bytes().decode("utf-8")
    findings = list(scan(t))
    counts = collections.Counter((k, ord(t[i])) for i, k, _, _ in findings)
    active = {"remove", "replace"} | ({"keep"} if "--spaces" in flags else set()) \
        | ({"typography"} if "--typography" in flags else set())

    if "--clean" not in flags:
        for i, k, e, g in findings:
            line, col = position(t, i)
            name = unicodedata.name(t[i], "no name")
            arrow = f" -> {visible(e) or '(gone)'}" if k in ("remove", "replace") else ""
            print(f"L{line}:C{col}  U+{ord(t[i]):04X} {name}  [{k}{arrow}] {g}  ...{visible(t[max(0, i - 20):i + 20])}...")
    else:
        new, changes = [], []
        swaps = {i: (e, g) for i, k, e, g in findings if k in active and not (k == "typography" and e == t[i])}
        for i, c in enumerate(t):
            if i in swaps:
                e, g = swaps[i]
                line, col = position(t, i)
                changes.append(f"L{line}:C{col}  U+{ord(c):04X} {unicodedata.name(c, '?')} -> {visible(e) or '(removed)'}  {g}")
                new.append(e)
            else:
                new.append(c)
        target = target or source.with_name(source.stem + ".cleaned" + source.suffix)
        target.write_bytes("".join(new).encode("utf-8"))
        print(f"{len(changes)} changes, written to {target}")
        print("\n".join(changes))

    print("\nSummary: " + (", ".join(f"{k} U+{cp:04X} {unicodedata.name(chr(cp), '?')} x{n}"
                                     for (k, cp), n in sorted(counts.items())) or "no findings"))
    print("Note: this script does not check statistical watermarks in the word choice; that is not possible "
          "without the vendor's key.")
    sys.exit(1 if any(k in ("remove", "replace") for _, k, _, _ in findings) else 0)


if __name__ == "__main__":
    main()

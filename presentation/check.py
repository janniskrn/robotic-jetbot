"""Static checks on the presentation, without a browser.

    python presentation/check.py [week2.html] [--fix]

With --fix the line numbers of quoted lines that have merely moved are rewritten first, and only the
lines whose code actually changed are reported.

Tag balance, em dashes, unfilled placeholders, document twins for every class sized in cqw, bar widths
recomputed from their own values, every quoted code line still at the line number the slide
claims for it, and the palette contrasts against the targets in design/THEME.md.
The one thing it cannot see is a slide whose text runs off the bottom: that check is in README.md and
needs a browser.
"""

import html
import os
import re
import sys
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
arg_page = next((a for a in sys.argv[1:] if not a.startswith('-')), 'week2.html')
if os.path.exists(arg_page):
    PAGE = os.path.abspath(arg_page)
else:
    PAGE = os.path.join(HERE, arg_page)
SOURCE_DIR = os.path.join(os.path.dirname(HERE), 'notebooks', 'mini_av')

# text that has to be readable from the back of a room: 7:1. Small print: 4.5:1.
TARGETS = {'ink': 7.0, 'muted': 7.0, 'faint': 4.5, 'accent-ink': 4.5}
VOID = {'img', 'br', 'hr', 'input', 'meta', 'link', 'source', 'area', 'base', 'col', 'embed', 'param', 'track', 'wbr'}

problems = []


def fail(message):
    problems.append(message)


class TagCheck(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.stack, self.bad = [], []

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append((tag, self.getpos()[0]))

    def handle_endtag(self, tag):
        if self.stack and self.stack[-1][0] == tag:
            self.stack.pop()
        else:
            self.bad.append((tag, self.getpos()[0]))


def luminance(hex_color):
    h = hex_color.lstrip('#')
    parts = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    parts = [(v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4) for v in parts]
    return 0.2126 * parts[0] + 0.7152 * parts[1] + 0.0722 * parts[2]


def contrast(a, b):
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def tokens(block):
    """{name: hex} for the plain hex tokens of one :root block"""
    return dict(re.findall(r'--([\w-]+):\s*(#[0-9A-Fa-f]{6})', block))


def code_line(line):
    """One line of a <pre> block as (line number or None, plain code): spans and comments dropped"""
    number = re.match(r'\s*<span class="ln[^"]*">(\d*)</span>', line)
    rest = line[number.end():] if number else line
    rest = re.sub(r'<span class="[mc]">.*?</span>', '', rest)
    text = html.unescape(re.sub(r'<[^>]+>', '', rest)).split('#')[0].strip()
    return (int(number.group(1)) if number and number.group(1) else None), text


def source_lines(name):
    return [l.split('#')[0].strip() for l in open(os.path.join(SOURCE_DIR, name), encoding='utf-8')]


def find_text(source, text, near):
    """Line numbers whose code is this text, nearest to `near` first (a line may occur twice)"""
    if text.endswith('...'):
        hits = [i + 1 for i, l in enumerate(source) if l.startswith(text[:-3]) and text[:-3]]
    else:
        hits = [i + 1 for i, l in enumerate(source) if l == text]
    return sorted(hits, key=lambda n: abs(n - near))


def renumber(page):
    """Rewrite the line numbers of every quoted line that has simply moved, and say what is left.

    The code changes every week; the numbers must not be maintained by hand. A line whose text has
    changed cannot be guessed, so it is reported and fixed on the slide.
    """
    out, last, changed, moved = [], 0, 0, {}
    for match in re.finditer(r'<pre[^>]*>(.*?)</pre>', page, re.S):
        names = re.findall(r'([\w.]+\.py)', page[max(0, match.start() - 200):match.start()]
                           + ' ' + match.group(1).split('\n')[0])
        if not names or not os.path.exists(os.path.join(SOURCE_DIR, names[-1])):
            continue
        source, lines, previous = source_lines(names[-1]), [], 0
        for line in match.group(1).split('\n'):
            number, text = code_line(line)
            if number is not None and text and text != '...':
                hits = find_text(source, text, number)
                ahead = [n for n in hits if n > previous]  # a listing runs down the file, not back up
                hits = ahead + [n for n in hits if n not in ahead]
                if hits:
                    moved[number], previous = hits[0], hits[0]
                if hits and hits[0] != number:
                    line = re.sub(r'(<span class="ln[^"]*">)\d+(</span>)',
                                  r'\g<1>%d\g<2>' % hits[0], line, count=1)
                    changed += 1
                elif not hits:
                    print('  by hand: %s has no line "%s" (slide says %d)' % (names[-1], text, number))
            lines.append(line)
        out.append(page[last:match.start(1)])
        out.append('\n'.join(lines))
        last = match.end(1)
    out.append(page[last:])
    page = ''.join(out)

    # the notes point at those lines by number, so they have to move with them
    def anchor(match):
        number = moved.get(int(match.group(1)))
        return match.group(0) if number is None else '<span class="nn">%d</span>' % number
    page, badges = re.subn(r'<span class="nn">(\d+)</span>', anchor, page)
    print('renumbered %d lines (%d note anchors checked)' % (changed, badges))
    return page


def check_code_blocks(page):
    """Every quoted line must still exist in the file named in the block's first comment.

    A slide that shows code the file no longer contains is the one error nobody notices in time.
    A line ending in ... only has to match the start of a line.
    """
    for match in re.finditer(r'<pre[^>]*>(.*?)</pre>', page, re.S):
        block = match.group(1)
        lines = block.split('\n')
        # the file is named in the caption above the block or in its first comment line: take the
        # nearest name, which is the last one before the code starts
        names = re.findall(r'([\w.]+\.py)', page[max(0, match.start() - 200):match.start()] + ' ' + lines[0])
        if not names:
            fail('code block without a file name above it: %s' % lines[0][:60])
            continue
        name = names[-1]
        path = os.path.join(SOURCE_DIR, name)
        if not os.path.exists(path):
            fail('code block names %s, which does not exist' % name)
            continue
        source = [l.split('#')[0].strip() for l in open(path, encoding='utf-8')]
        for line in lines:  # the first line already holds code when <pre> opens the block
            number, text = code_line(line)
            if not text or text == '...':
                continue
            if number is not None:  # the slide claims a position, so check that too
                at = source[number - 1] if 0 < number <= len(source) else ''
                ok = at.startswith(text[:-3]) if text.endswith('...') else at == text
                if not ok:
                    fail('%s line %d is "%s", the slide shows "%s"' % (name, number, at, text))
            elif text.endswith('...'):
                head = text[:-3]
                if not any(s.startswith(head) for s in source):
                    fail('%s has no line starting with: %s' % (name, head))
            elif text not in source:
                fail('%s no longer contains: %s' % (name, text))


def check_note_anchors(page):
    """A note's number must be a line the slide shows.

    A note pointing at a line nobody can see is worse than no number: the reader looks for it,
    does not find it, and stops trusting the other numbers.
    """
    for block in re.findall(r'<div class="codeslide">(.*?)</ol>', page, re.S):
        shown = set(re.findall(r'<span class="ln[^"]*">(\d+)</span>', block))
        caption = re.search(r'<div class="cf">([^<]*)</div>', block)
        for note in re.findall(r'<span class="nn">(\d+)</span>', block):
            if note not in shown:
                fail('note %s points at a line the slide does not show (%s)'
                     % (note, caption.group(1)[:46] if caption else '?'))

    # a caption that says "lines A to B" has to be the range the slide really shows
    for block in re.findall(r'<div class="cf">([^<]*)</div>\s*<pre[^>]*>(.*?)</pre>', page, re.S):
        said = re.search(r'lines (\d+) to (\d+)', block[0])
        shown = [int(n) for n in re.findall(r'<span class="ln[^"]*">(\d+)</span>', block[1])]
        if said and shown and (int(said.group(1)), int(said.group(2))) != (min(shown), max(shown)):
            fail('caption says lines %s to %s, the slide shows %d to %d (%s)'
                 % (said.group(1), said.group(2), min(shown), max(shown), block[0][:40]))


def check_appendix(page):
    """The appendix states each file's length: a file that grew would otherwise pass unnoticed,
    because every line it still shows would match. Rebuild with build_appendix.py."""
    for name, claimed in re.findall(r'<h3>([\w.]+\.py) <span class="fn">(\d+) lines</span></h3>', page):
        path = os.path.join(SOURCE_DIR, name)
        actual = len(open(path, encoding='utf-8').read().rstrip('\n').split('\n'))
        if actual != int(claimed):
            fail('appendix has %s at %s lines, the file has %d: run build_appendix.py'
                 % (name, claimed, actual))


def main():
    page = open(PAGE, encoding='utf-8').read()

    if '--fix' in sys.argv:  # the code moved: follow it, then check what is left
        page = renumber(page)
        open(PAGE, 'w', encoding='utf-8', newline='').write(page)

    if '—' in page or '–' in page:
        fail('em or en dash in the text: %d found' % (page.count('—') + page.count('–')))

    left = sorted(set(re.findall(r'__[A-Z0-9_]+__', page)))
    if left:
        fail('placeholder never filled: %s' % ', '.join(left))

    checker = TagCheck()
    checker.feed(page)
    if checker.stack:
        fail('tag never closed: %s' % ', '.join('%s (line %d)' % t for t in checker.stack))
    if checker.bad:
        fail('closing tag with no opener: %s' % ', '.join('%s (line %d)' % t for t in checker.bad))

    slides = len(re.findall(r'<section>', page))
    eyebrows = len(re.findall(r'class="eyebrow"', page))
    if eyebrows > max(1, slides // 3):
        fail('%d eyebrows on %d slides: at most one per three' % (eyebrows, slides))

    # every class sized in cqw needs a body.doc rule in rem, or the document mode is unreadable
    css_parts = re.findall(r'<style[^>]*>(.*?)</style>', page, flags=re.S)
    for link in re.findall(r'<link[^>]+rel=["\']stylesheet["\'][^>]+href=["\']([^"\']+)["\']', page):
        link_path = os.path.normpath(os.path.join(os.path.dirname(PAGE), link))
        if os.path.exists(link_path):
            css_parts.append(open(link_path, encoding='utf-8').read())
    css = re.sub(r'/\*.*?\*/', '', '\n'.join(css_parts) if css_parts else page, flags=re.S)
    deck_classes, doc_classes = set(), set()
    for selector, body in re.findall(r'([^{}]+)\{([^{}]*)\}', css):
        selector = selector.strip()
        names = re.findall(r'\.([a-zA-Z][\w-]*)', selector)
        if selector.startswith('body.doc'):
            doc_classes.update(names)
        elif 'cqw' in body:
            deck_classes.update(names)
    missing = sorted(deck_classes - doc_classes)
    if missing:
        fail('sized in cqw with no body.doc twin: %s' % ', '.join(missing))

    # a bar drawn to a width that is not its own value is a lie about the measurement
    for width, value in re.findall(r'width:([\d.]+)%"></i></span><span class="bv">([\d.]+)\s*s<', page):
        expected = round(float(value) / 60 * 100, 1)
        if abs(expected - float(width)) > 0.05:
            fail('bar for %s s drawn at %s %%, should be %s %% of the 60 s cap' % (value, width, expected))

    check_code_blocks(page)
    check_appendix(page)
    check_note_anchors(page)

    # the swerve figure: the cup has to sit at the centre of the drawn curve
    arc = re.search(r'M(\d+),(\d+) A (\d+),\d+ 0 0 1 (\d+),', page)
    cup = re.search(r'<circle cx="(\d+)" cy="\d+" r="12"', page)
    if arc and cup:
        start, radius, end = int(arc.group(1)), int(arc.group(3)), int(arc.group(4))
        if (start + end) // 2 != int(cup.group(1)) or (end - start) // 2 != radius:
            fail('the avoidance curve is not centred on the cup any more')

    # contrast, against the ground of each palette
    light = tokens(re.search(r':root\{(.*?)\}', css, re.S).group(1))
    dark_block = re.search(r':root\[data-theme="dark"\]\{(.*?)\}', css, re.S)
    dark = tokens(dark_block.group(1)) if dark_block else {}
    for name, palette in (('light', light), ('dark', dark)):
        ground = palette.get('ground')
        if not ground:
            continue
        for token, target in TARGETS.items():
            if token in palette:
                ratio = contrast(palette[token], ground)
                if ratio < target:
                    fail('%s palette: %s is %.2f:1 on the ground, target %.1f' % (name, token, ratio, target))

    print('%s: %d slides, %d eyebrows' % (os.path.basename(PAGE), slides, eyebrows))
    if problems:
        print('\n%d problem(s):' % len(problems))
        for problem in problems:
            print('  - %s' % problem)
        print('\nStill to run in a browser: the overflow check in presentation/README.md')
        return 1
    print('all static checks pass')
    print('Still to run in a browser: the overflow check in presentation/README.md')
    return 0


if __name__ == '__main__':
    sys.exit(main())

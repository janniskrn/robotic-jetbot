"""Static checks on the presentation, without a browser.

    python presentation/check.py [index_v3.html]

Tag balance, em dashes, unfilled placeholders, document twins for every class sized in cqw, bar widths
recomputed from their own values, every quoted code line still present in its source file, and the
palette contrasts against the targets in design/THEME.md.
The one thing it cannot see is a slide whose text runs off the bottom: that check is in README.md and
needs a browser.
"""

import html
import os
import re
import sys
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(HERE, sys.argv[1] if len(sys.argv) > 1 else 'index.html')
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


def code_text(line):
    """One line of a <pre> block as plain code: markers and comments dropped, entities decoded"""
    line = re.sub(r'<span class="[mc]">.*?</span>', '', line)
    return html.unescape(re.sub(r'<[^>]+>', '', line)).split('#')[0].strip()


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
            text = code_text(line)
            if not text or text == '...':
                continue
            if text.endswith('...'):
                head = text[:-3]
                if not any(s.startswith(head) for s in source):
                    fail('%s has no line starting with: %s' % (name, head))
            elif text not in source:
                fail('%s no longer contains: %s' % (name, text))


def main():
    page = open(PAGE, encoding='utf-8').read()

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
    css = re.sub(r'/\*.*?\*/', '', page, flags=re.S)
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

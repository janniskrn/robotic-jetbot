"""Prints presentation/week3.html (the week 3 page) to week3.pdf with the robot's Chromium 87, which has no cqw
units: a print copy turns 1cqw into 2.97 mm (1 % of the 297 mm printed slide) and keeps every page a hair under
167 mm, or this Chromium adds blank pages."""
import io, re, subprocess
P = '/home/jetbot/jetbot/presentation/'
h = io.open(P + 'week3.html', encoding='utf-8').read()
h = re.sub(r'(-?\d*\.?\d+)cqw', lambda m: '%.3fmm' % (float(m.group(1)) * 2.97), h).replace('100dvh', '100vh')
h = re.sub(r'<section data-group="w1">.*?</section>', '', h, flags=re.S)  # only the week 3 page
h = h.replace('</head>', '<style>@media print{body.slides section,body.map section,body.slides .slide,body.map .slide,'
              'body.map .roadmap{height:166.4mm !important}}</style></head>', 1)
tmp = '/tmp/week3_print.html'
io.open(tmp, 'w', encoding='utf-8').write(h)
subprocess.run(['chromium-browser', '--headless', '--disable-gpu', '--no-sandbox', '--no-pdf-header-footer',
                '--virtual-time-budget=20000', '--print-to-pdf=' + P + 'week3.pdf', tmp],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=200)

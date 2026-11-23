"""Prints presentation/week4.html to week4.pdf with the robot's Chromium: 11 pages of 1280 x 720 px. The page is
sized in px (no cqw), so it prints as it shows. Needs the internet once for the fonts.

    python3 presentation/print_week4.py
"""
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
subprocess.run(['chromium-browser', '--headless', '--disable-gpu', '--no-sandbox', '--no-pdf-header-footer',
                '--virtual-time-budget=20000', '--print-to-pdf=' + os.path.join(HERE, 'week4.pdf'),
                'file://' + os.path.join(HERE, 'week4.html')],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=200, check=True)

#!/usr/bin/env python3

#### PERL WOULd BE ~~25% FASTER! BUT THIS ONE HANDLES EMOJI ...



import sys
sys.stdin.reconfigure(encoding='utf-8', errors='replace')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

for line in sys.stdin:
    print(line.rstrip('\n').replace('"', "''"))


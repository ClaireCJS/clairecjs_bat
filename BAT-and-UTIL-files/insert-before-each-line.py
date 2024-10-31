#!/usr/bin/env python3

#### THE PERL VERSION IS 25% FASTER! BUT THIS ONE HANDLES EMOJI!

import sys
sys.stdin .reconfigure(encoding='utf-8', errors='replace')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <prefix>", file=sys.stderr)
        sys.exit(1)
    prefix = sys.argv[1]

    for line in sys.stdin:
        line = line.rstrip('\n')
        print(prefix + line)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3

#### THE PERL VERSION IS 25% FASTER! BUT THIS ONE HANDLES EMOJI! ... [and has the percent substitution] ...

### substitutes {{{{QUOTE}}}}   into "
### substitutes {{{{PERCENT}}}} into %

import sys
sys.stdin.reconfigure(encoding='utf-8', errors='replace')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <postfix>", file=sys.stderr)
        sys.exit(1)
    postfix = sys.argv[1]

    postfix = postfix.replace("{{{{QUOTE}}}}"  , r'"')
    postfix = postfix.replace("{{{{QUOTES}}}}" , r'"')
    postfix = postfix.replace("{{{{PERCENT}}}}", r'%')
    postfix = postfix.replace("{{{{PCT}}}}"    , r'%')
    postfix = postfix.replace("{{{{PIPE}}}}"   , r'|')

    for line in sys.stdin:
        line = line.rstrip('\n')
        # Use a normal string, not a raw string, to ensure correct matching
        print(line + postfix)

if __name__ == "__main__":
    main()

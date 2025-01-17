import random
import sys
from colorama import init
#init(autoreset=False)
#init()

colors = range(31, 38)
for line in sys.stdin:
    r = random.randint(64,255)
    g = random.randint(64,255)
    b = random.randint(64,255)
    sys.stdout.write(f'\033[38;2;{r};{g};{b}m{line.rstrip()}\033[0m\n')

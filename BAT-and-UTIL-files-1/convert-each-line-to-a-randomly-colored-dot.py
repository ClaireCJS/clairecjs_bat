import os
import sys
import random

# Ensure output is not buffered (autoflush)
#tesys.stdout.reconfigure(line_buffering=True)                                # this buffers by line which i don't like
sys.stdout = os.fdopen(sys.stdout.fileno(), 'wb', buffering=0)                # Set stdout to be unbuffered (buffer size 0 means per-character buffering)


# ANSI color codes for foreground colors 30-37 (standard)
ansi_colors = list(range(30, 38))

# Initialize variables with random values
last_randcolor = random.choice(ansi_colors)
curr_randcolor = random.choice(ansi_colors)


# Function to get a random color that is different from the last one
def get_random_color():
    global curr_randcolor
    global last_randcolor
    #curr_randcolor = random.choice(ansi_colors)
    while curr_randcolor == last_randcolor: curr_randcolor = random.choice(ansi_colors)
    last_randcolor = curr_randcolor
    return curr_randcolor

# Read from stdin and output colored dots
for line in sys.stdin:
    randcolor = get_random_color()
    #ys.stdout.write(f"\033[{randcolor}m.\033[0m")
    sys.stdout.write(f"\033[{randcolor}m.".encode('utf-8'))
    #sys.stdout.flush()

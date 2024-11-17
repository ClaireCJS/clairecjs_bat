import sys
import time
import colorsys

# Set default values for code and number
code = "11"  # Default to background
number = -1  # Default to run indefinitely

# Parse command-line arguments
if len(sys.argv) > 1:
    # Check if the first argument is a number
    try:
        number = int(sys.argv[1])  # Attempt to convert to integer
    except ValueError:
        # If not a number, check for background or foreground
        if sys.argv[1].lower() == "background":
            code = "11"
        elif sys.argv[1].lower() == "foreground":
            code = "10"

    # Check if a second argument is provided and is a number
    if len(sys.argv) > 2:
        try:
            number = int(sys.argv[2])  # Convert to integer if second argument is provided
        except ValueError:
            print("Error: Second argument must be an integer if provided.")
            sys.exit(1)

cycle_count = 0
for i in range(0, 2560):
    h = i / 256.0
    (r, g, b) = tuple(round(j * 255) for j in colorsys.hsv_to_rgb(h, 1.0, 1.0))

    # Print ANSI escape sequence and RGB values
    sys.stdout.write(f'\x1b]{code};rgb:{r:x}/{g:x}/{b:x}\x1b\\')
    sys.stdout.write(f'\rrgb:{r:x}/{g:x}/{b:x}')
    sys.stdout.flush()

    cycle_count += 1
    time.sleep(.05)

    # Stop the loop if cycle_count reaches the specified number
    if cycle_count == number:
        break  # Stop the loop

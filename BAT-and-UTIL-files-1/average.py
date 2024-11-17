import sys
import re

# Constants
END_OF_INPUT_LINES = 2  # Number of consecutive blank lines to signal end of input

def parse_and_average(inputs):
    numbers = []
    separators = [' ', '\n', ',']

    inputs = inputs.replace(',', '')  # Remove commas before splitting

    for sep in separators:
        inputs = inputs.replace(sep, ' ')

    for num in inputs.split():
        # Remove any non-number characters from the beginning of the string
        num = re.sub('^[^\d.-]+', '', num)
        num = re.sub(        '%', '', num)
        try:
            numbers.append(float(num))
        except ValueError:
            pass  # Ignore non-numeric values

    sum_numbers = sum(numbers)
    count_numbers = len(numbers)
    average_numbers = sum_numbers / count_numbers if count_numbers != 0 else 0

    print("\n  Count:", count_numbers  )
    print(  "    Sum:", sum_numbers    )
    print("\nAverage:", average_numbers)

# If parameters are entered, use them
if len(sys.argv) > 1:
    parse_and_average(' '.join(sys.argv[1:]))

# If no parameters are entered, prompt the user to paste a list of values
else:
    print("Please paste a space / enter / comma-separated list of values (end with {} blank lines):".format(END_OF_INPUT_LINES))
    user_input_lines = []
    blank_lines = 0

    while blank_lines < END_OF_INPUT_LINES:
        line = input()
        if line.strip() == '':
            blank_lines += 1
        else:
            blank_lines = 0
        user_input_lines.append(line)

    parse_and_average('\n'.join(user_input_lines))

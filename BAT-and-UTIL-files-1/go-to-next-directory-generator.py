import os
import ctypes
import sys

# Windows API call to get the real stored filename
def get_real_path(path):
    buf = ctypes.create_unicode_buffer(1024)
    if ctypes.windll.kernel32.GetLongPathNameW(path, buf, 1024):
        return buf.value
    return path  # Fallback if API fails

# Get starting directory from command-line argument
if len(sys.argv) < 2:
    print("❌ ERROR: No directory provided!", file=sys.stderr)
    sys.exit(1)

starting_dir = sys.argv[1]
previous_mode = (len(sys.argv) > 2 and sys.argv[2] == "PREVIOUS")

print(f'rem echo DEBUG: Starting directory: "{starting_dir}"')

# Get parent directory
parent_dir = os.path.dirname(get_real_path(starting_dir).rstrip("\\")) + "\\"
print(f'rem echo DEBUG: Parent directory: "{parent_dir}"')

# Change into the parent directory
try:
    os.chdir(parent_dir)
except OSError as e:
    print(f"❌ ERROR: Cannot change into parent directory: {e}", file=sys.stderr)
    sys.exit(1)

# Read directory contents and filter only directories
files = [f for f in os.listdir('.') if os.path.isdir(f)]
files = [get_real_path(f) for f in files]  # Ensure real Windows filenames
files.sort(key=lambda x: x.lower())

print(f"rem echo DEBUG: Found folders: {' '.join(files)}")

# Extract just the folder name from the starting directory
target_dir = get_real_path(starting_dir).rstrip("\\")
target_dir = os.path.basename(target_dir)  # Ensure full folder name

print(f'rem echo DEBUG: Fully extracted target directory name: "{target_dir}"')

# Search for the next or previous folder
try:
    index = files.index(target_dir)  # Find the current directory index
except ValueError:
    print("❌ ERROR: Target directory not found in sorted list!", file=sys.stderr)
    sys.exit(1)

direction = -1 if previous_mode else 1
index += direction

# Ensure the next folder exists before switching
while 0 <= index < len(files) and not os.path.isdir(get_real_path(os.path.join(parent_dir, files[index]))):
    print(f'rem echo DEBUG: Skipping non-directory: "{files[index]}"')
    index += direction

# Check if the final index is valid
if index < 0 or index >= len(files):
    print("❌ ERROR: No next/previous directory found!", file=sys.stderr)
    sys.exit(1)

# Final target directory
full_target = get_real_path(os.path.join(parent_dir, files[index])) + "\\"

print(f'rem echo DEBUG: Switching to: "{full_target}"')
print(f'cd "{full_target}"')

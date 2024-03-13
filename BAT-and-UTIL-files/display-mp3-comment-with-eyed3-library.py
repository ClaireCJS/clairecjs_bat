import sys
import eyed3

def print_description(filepath):
    audiofile = eyed3.load(filepath)
    if audiofile is None:
        print(f"No file found at {filepath}")
        return

    if audiofile.tag is None:
        print(f"No ID3 tag found in {filepath}")
        return

    for comment in audiofile.tag.comments:
        print("Literal: " + comment.text)
        print("Substit: " + comment.text.replace("\r","\\r").replace("\n","\\n"))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please provide a file path as a command-line argument.")
        sys.exit(1)
    filepath = sys.argv[1]  # Take the file path from the first command-line argument
    print_description(filepath)

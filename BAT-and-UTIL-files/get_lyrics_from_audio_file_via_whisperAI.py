import os
import sys
import whisper

# Get the filename from the command-line argument
if len(sys.argv) < 2:
    print("Please specify a filename.")
    sys.exit(1)
filename = sys.argv[1]

# Load the model and transcribe the audio file
model = whisper.load_model("base")
result = model.transcribe(filename)
transcript = result["text"]

# Save the transcript to a file with the same name as the base file
base_name, ext = os.path.splitext(filename)
transcript_name = f"{base_name}.txt"
if os.path.isfile(transcript_name):
    i = 1
    while os.path.isfile(f"{transcript_name}.{i:03d}"): i += 1
    transcript_name = f"{transcript_name}.{i:03d}"
with open(transcript_name, "w", encoding="utf-8") as f:
    f.write(transcript)

# Print the transcript to the console
print(transcript)

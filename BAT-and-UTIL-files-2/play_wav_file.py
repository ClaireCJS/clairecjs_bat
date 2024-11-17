import sys
import os
import simpleaudio as sa

def validate_file(file_path, extension=None):
    if not os.path.exists (file_path):                            raise FileNotFoundError(f"The specified file does not exist: {file_path}")
    if not os.path.isfile (file_path):                            raise IsADirectoryError(f"The specified path is a directory, not a file: {file_path}")
    if     os.path.getsize(file_path) == 0:                       raise        ValueError(f"The specified file is empty: {file_path}")
    if extension  and  not file_path.lower().endswith(extension): raise        ValueError(f"The specified file does not have the '{extension}' extension: {file_path}")

def play_wav_filename(wav_filename):
    wave_obj = sa.WaveObject.from_wave_file(wav_filename)
    play_obj = wave_obj.play()
    play_obj.wait_done()  # Wait until sound has finished playing

def main():
    if len(sys.argv) < 2:
        print("Usage: python play-wav-file.py <wav_filename>")
        sys.exit(666)

    wav_filename = sys.argv[1]
    play_wav_filename(wav_filename)

if __name__ == "__main__":
    main()


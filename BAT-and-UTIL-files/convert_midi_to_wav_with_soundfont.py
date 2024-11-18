"""
play a midi file
"""
import os
import sys
from contextlib import redirect_stdout
from pydub import AudioSegment
from pydub.silence import detect_nonsilent
from colorama import Fore, Back, Style, init                                                                                                                                #pylint: disable=W0611
init()
original_stdout = sys.stdout
null_file = open(os.devnull,'w',encoding='utf-8')
sys.stdout = null_file
from midi2audio import FluidSynth
sys.stdout = original_stdout
null_file.close()
#this is defined in get_soundfont_file() below now: DEFAULT_SOUNDFONT_FILE


def validate_file(file_path, extension=None, extension2=None):
    #DEBUG: print(f"validating file {file_path}")
    if not os.path.exists (file_path):                            raise FileNotFoundError(f"The specified file does not exist: {file_path}")
    if not os.path.isfile (file_path):                            raise IsADirectoryError(f"The specified path is a directory, not a file: {file_path}")
    if     os.path.getsize(file_path) == 0:                       raise        ValueError(f"The specified file is empty: {file_path}")
    if extension and not file_path.lower().endswith(extension) \
                 and not file_path.lower().endswith(extension2):  raise        ValueError(f"The specified file does not have the '{extension}' extension: {file_path}")

def convert_midi_to_wav_using_soundfont(midi_file=r'c:\midirandia.mid', audio_file=r'c:\midirandia.wav'):
    soundfont_file = get_soundfont_file()
    # Validate that the MIDI file exists
    validate_file(midi_file, '.mid', '.midi')
    validate_file(soundfont_file, '.sf2')                               # Validate that the SoundFont file exists
    # Redirect stdout to devnull while FluidSynth is running?
    print(f"{Fore.BLACK}")
    original_stdout = sys.stdout
    null_file       = open(os.devnull,'w',encoding='utf-8')
    sys.stdout      = null_file
    fluid_synth     = FluidSynth(sound_font=soundfont_file)                 # You need to convert MIDI to audio using the specified SoundFont
    fluid_synth.midi_to_audio(midi_file, audio_file)
    sys.stdout      = original_stdout
    null_file.close()
    print(f"{Fore.WHITE}")
    trim_silence(audio_file)
    return audio_file


def trim_silence(audio_file):
    audio = AudioSegment.from_file(audio_file)                                          # Load the audio file
    non_silence = detect_nonsilent(audio, min_silence_len=100, silence_thresh=-50)      # Detect nonsilent parts. You may need to adjust -50 dB to fit your needs.
    if len(non_silence) > 0:                                                            # If there are nonsilent parts
        start_trim = non_silence[ 0][0]
        end_trim   = non_silence[-1][1]
        trimmed = audio[start_trim:end_trim]
        trimmed.export(audio_file, format="wav")                                        # Overwrite the original file with trimmed audio

def get_soundfont_file():
    DEFAULT_SOUNDFONT_FILE   = r'c:\util2\soundfonts\current_soundfont.sf2'
    ALTERNATE_SOUNDFONT_FILE = 'soundfont.sf2'

    if not os.path.isfile(DEFAULT_SOUNDFONT_FILE):
        print("Default soundfont file not found, looking for 'soundfont.sf2' in the current directory.")
        if os.path.isfile(ALTERNATE_SOUNDFONT_FILE):
            soundfont = ALTERNATE_SOUNDFONT_FILE
        else:
            soundfont = input("Please provide the location of your soundfont file: ")
            if not os.path.isfile(soundfont):
                print("Unable to find specified soundfont file. Please ensure to pass it as a parameter.")
                sys.exit(666)
    else:
        soundfont = DEFAULT_SOUNDFONT_FILE
    #DEBUG: print(f"*soundfont: {soundfont}")
    return soundfont


def main():
    if len(sys.argv) != 3: print(f"\n{Fore.YELLOW} Usage: python script.py <midi_filename> <wav_filename>"); sys.exit(1)
    midi_filename = sys.argv[1]
    wav_filename  = sys.argv[2]

    if not os.path.isfile(midi_filename): print(f"{Fore.RED}Error: MIDI file '{midi_filename}' does not exist."); sys.exit(1)
    if     os.path.isfile( wav_filename): print(f"{Fore.RED}Error:  WAV file '{wav_filename }' already exists."); sys.exit(1)

    convert_midi_to_wav_using_soundfont(midi_filename, wav_filename)


if __name__ == "__main__":
    main()

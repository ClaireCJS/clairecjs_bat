"""
    Generate and play random midi, but in one self-contained script for automation
"""
#import os
#import sys
import generate_midi_randomly
import convert_midi_to_wav_with_soundfont
import play_wav_file

def main():
    midi = "c:\\midirandia.midi"
    wav1 = "c:\\midirandia.wav"
    generate_midi_randomly.create_random_midi(15, midi)
    wav2 = convert_midi_to_wav_with_soundfont.convert_midi_to_wav_using_soundfont(midi, wav1)
    play_wav_file.play_wav_filename(wav2)

if __name__ == "__main__":
    main()

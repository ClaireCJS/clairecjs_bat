"""
    Generate and play random midi, but in one self-contained script for automation
"""
#import os
import sys
import generate_midi_randomly
import convert_midi_to_wav_with_soundfont
import play_wav_file

defaut_duration = 15
midi            = "c:\\bat\\midirandia.midi"   #\___contents don't matter, but needs(?) to exist(?)
wav1            = "c:\\bat\\midirandia.wav"    #/

def main():
    duration_to_use = defaut_duration
    if len(sys.argv) > 1:
        try:
            duration_to_use = int(sys.argv[1])
        except ValueError:
            print(f"Invalid number of notes '{sys.argv[1]}'. Using default: {default_duration}")


    generate_midi_randomly.create_random_midi(duration_to_use, midi)
    wav2 = convert_midi_to_wav_with_soundfont.convert_midi_to_wav_using_soundfont(midi, wav1)
    play_wav_file.play_wav_filename(wav2)

if __name__ == "__main__":
    main()

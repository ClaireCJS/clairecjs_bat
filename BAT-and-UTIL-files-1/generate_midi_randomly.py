"""
    generate a random midi
"""
import sys
import random
from mido import Message, MidiFile, MidiTrack
import mido

DEBUG               = 1
DEFAULT_SONG_LENGTH = 15


def get_known_musical_scales():
    return {
        'major': [60, 62, 64, 65, 67, 69, 71, 72],
        'natural_minor': [60, 62, 63, 65, 67, 68, 70, 72],
        'harmonic_minor': [60, 62, 63, 65, 67, 68, 71, 72],
        'melodic_minor': [60, 62, 63, 65, 67, 69, 71, 72],
        'dorian': [60, 62, 63, 65, 67, 69, 70, 72],
        'mixolydian': [60, 62, 64, 65, 67, 69, 70, 72],
        'lydian': [60, 62, 64, 66, 67, 69, 71, 72],
        'phrygian': [60, 61, 63, 65, 67, 68, 70, 72],
        'locrian': [60, 61, 63, 64, 66, 68, 70, 72],
        'pentatonic_major': [60, 62, 64, 67, 69, 72],
        'pentatonic_minor': [60, 63, 65, 67, 70, 72],
        'blues': [60, 63, 65, 66, 67, 70, 72],
        'chromatic': [60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72]
    }



def get_scale_of_notes_to_use():
    scales = get_known_musical_scales()
    scale_name = random.choice(list(scales.keys()))
    scale = scales[scale_name]
    root_note = random.randint(60, 72)
    scale = [(note - 60) + root_note for note in scale]
    even_more_message = ""
    if random.choice([True, True, True, False]):
        range_increased   = True
        lower_scale       = [note - 12 for note in scale]
        higher_scale      = [note + 12 for note in scale]
        more_lower_scale  = [note - 24 for note in scale]
        more_higher_scale = [note + 24 for note in scale]
        scale             = lower_scale + scale + higher_scale
        if random.choice([True, False, False, False]):
            scale = more_lower_scale + scale + more_higher_scale
            even_more_message = "rrr"
        else:
            even_more_message = ""
    else:
        range_increased = False
    return scale, root_note, scale_name, range_increased, even_more_message



def create_random_midi(duration_in_seconds, filename, tempo=None):
    if tempo is None:
        tempo = random.randint(60,140)  #random tempo between 60bpm and 140bpm
        tempo = tempo * 4167            #a value of "500000" is equivalent to 120bpm
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)
    track.append(mido.MetaMessage('set_tempo', tempo=tempo))
    current_time = 0
    #DEBUG: print(f"tempo={tempo}")
    beats_per_minute = mido.tempo2bpm(tempo)
    bpm = beats_per_minute
    seconds_per_beat = 60.0 / beats_per_minute

    scale, root_note, scale_name, range_increased, even_more_message = get_scale_of_notes_to_use()

    num_channels = random.choice([2, 3, 4, 4, 5, 5, 5, 6, 6, 6, 6, 7, 7, 7, 7, 7, 8, 8, 8, 8, 8, 8, 9, 9, 9, 9, 9, 9, 9, 9, 10, 10, 10, 10, 10, 10, 10, 11, 11, 11, 11, 11, 11, 12, 12, 12, 12, 12, 13, 13, 13, 13, 14, 14, 14, 15, 15, 16])
    note_duration_options      = [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.15, 0.15, 0.15, 0.15, 0.15, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.5, 0.5, 0.5, 0.5, 1.0, 1.0, 1.5, 1.5, 2.0, 2.5]  # durations in seconds
    silence_after_note_options = [0.05, 0.05, 0.10, 0.10, 0.15, 0.20, 0.20, 0.25, 0.25, 0.40, 0.50, 0.5, 0.75]  # durations in seconds

    if DEBUG:
        print(f"* duration: {duration_in_seconds}s")
        print(f"* channels: {num_channels}")
        print(f"*      bpm: {int(bpm)}")
        print(f"*    scale: {scale_name}")
        print(f"*    wider: {range_increased}{even_more_message}")
        print(f"*     root: {root_note}")
        print(f"*    notes: {scale}")

    for channel in range(16):
        track = MidiTrack()
        if channel != 1:  instrument = random.randint(0, 127)  # There are 128 possible instruments, 10 is reserved
        track.append(Message('program_change', program=instrument, time=0, channel=channel))
        mid.tracks.append(track)
    for channel in range(16):
        channel_index = channel
        while current_time < duration_in_seconds:
            # Choosing number of simultaneous notes (up to 4 for a chord)
            num_notes = random.choice([1, 2, 2, 3, 3, 3, 3, 4, 4])
            notes = random.sample(scale, num_notes)  # Choosing distinct notes from scale
            velocity = random.randint(40, 120)

            note_duration, silence_after_note = random.choice(note_duration_options), random.choice(silence_after_note_options)

            # Assign the same channel to all notes of the chord
            ####channel = random.randint(1, num_channels-1)
            #if num_notes > 1 else 0  # 0 is for individual notes, other channels for chords

            # Start multiple notes at the same time (like a chord)
            for note in notes:
                message  = Message('note_on', note=note, velocity=velocity, time=0, channel=channel)
                mid.tracks[channel_index].append(message)

            # Advance time for the note duration and stop the notes
            for note in notes:
                message  = Message('note_off', note=note, velocity=velocity, time=int(seconds_per_beat * mido.second2tick(note_duration, mid.ticks_per_beat, tempo)), channel=channel)
                mid.tracks[channel_index].append(message)
            current_time += note_duration

            # Insert a silence after the notes
            mid.tracks[channel_index].append(Message('note_off', note=0, velocity=0,time=int(seconds_per_beat * mido.second2tick(silence_after_note, mid.ticks_per_beat, tempo))))
            current_time += silence_after_note

    mid = add_random_drums(mid,duration_in_seconds,tempo)
    mid.save(filename)


def add_random_drums_1(midi_file, duration_in_seconds, tempo=500000):
    track = MidiTrack()
    midi_file.tracks.append(track)
    beats_per_minute = mido.tempo2bpm(tempo)
    seconds_per_beat = 60.0 / beats_per_minute
    drum_notes = [36, 38, 42, 46]  # bass drum, snare drum, closed hi-hat, open hi-hat
    drum_pattern_duration_options = [0.25, 0.5, 1.0]  # durations in beats
    current_time = 0
    while current_time < duration_in_seconds:
        drum_note = random.choice(drum_notes)
        velocity = random.randint(40, 120)
        pattern_duration = random.choice(drum_pattern_duration_options)
        message_on = Message('note_on', note=drum_note, velocity=velocity, time=0, channel=10)
        track.append(message_on)
        message_off = Message('note_off', note=drum_note, velocity=velocity, channel=10,
                              time=int(seconds_per_beat * mido.second2tick(pattern_duration, midi_file.ticks_per_beat, tempo)))
        track.append(message_off)
        current_time += pattern_duration


def add_random_drums(midi_file, duration_in_seconds, tempo=500000):
    if len(midi_file.tracks) > 9:                                    # Track numbers start at 0, so Track 10 is at index 9
        track = midi_file.tracks[9]
        track.clear()                                                # Clear existing track -- TODO should we really do this?
    else:
        track = MidiTrack()                                          # Create a new track if it doesn't exist
        midi_file.tracks.append(track)

    beats_per_minute = mido.tempo2bpm(tempo)
    seconds_per_beat = 60.0 / beats_per_minute

    drum_notes = [36, 36, 36, 38, 42, 42, 42, 42, 46, 46, 46, 46, ]  # bass drum, snare drum, closed hi-hat, open hi-hat
    drum_pattern_duration_options = [0.25, 0.5, 1.0]                 # durations in beats

    current_time = 0
    while current_time < duration_in_seconds:
        velocity         = random.randint(40, 120)
        drum_note        = random.choice(drum_notes)
        pattern_duration = random.choice(drum_pattern_duration_options)
        time             = int(seconds_per_beat * mido.second2tick(pattern_duration, midi_file.ticks_per_beat, tempo))
        message_on       = Message('note_on' , note=drum_note, velocity=velocity, channel=10, time=0   ); track.append(message_on )
        message_off      = Message('note_off', note=drum_note, velocity=velocity, channel=10, time=time); track.append(message_off)
        current_time    += pattern_duration
    return midi_file




def main():
    global DEFAULT_SONG_LENGTH
    if len(sys.argv) < 2: raise ValueError("Usage: python script.py <output_filename> [<song_length_in_seconds>]")
    filename = sys.argv[1]
    length = ""
    if len(sys.argv) > 2:
        length = int(sys.argv[2])

    if not length: length = DEFAULT_SONG_LENGTH

    create_random_midi(length, filename)

if __name__ == "__main__":
    main()

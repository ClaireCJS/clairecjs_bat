@echo off

set MIDI_DURATION=15



if "%1" ne "" (set MIDI_DURATION=%1)

@call generate-and-play-random-midi.bat %MIDI_DURATION%




@Echo OFF


generate_and_play_random_midi.py %*


REM can also do it piece-by-piece, if you want:

REM                REM Generate random midi - pass command line arg of length
REM                    set                          MIDI=c:\delme.mid
REM                    if exist "%MIDI%" (*del /q "%MIDI%")
REM                    generate_midi_randomly.py   %MIDI% %*
REM                    call validate-env-var        MIDI
REM
REM                REM Convert midi to wav using a soundfont file
REM                    %COLOR_RUN%
REM                    set WAV=c:\delme.wav
REM                    if exist "%WAV%" (*del /q "%WAV%")
REM                    convert_midi_to_wav_with_soundfont.py %MIDI% %WAV% >nul
REM
REM                REM Play wav file
REM                    play_wav_file.py %WAV%
REM

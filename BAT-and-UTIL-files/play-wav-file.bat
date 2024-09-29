@Echo OFF

rem Validate environment:
        if 1 ne %validated_play_wav_file (
                rem we want ffplay, part of ffmpeg:
                    set  validate_in_path_message=FFMPEG needs to be installed
                    call validate-in-path ffplay 
                    unset /q validate_in_path_message

                rem we want grep, and we want our play-button emoji and ansi controls:
                    call validate-in-path grep
                    call validate-environment-variables PLAY CHECK ANSI_SAVE_POSITION ANSI_MOVE_UP_1 ANSI_RESTORE_POSITION ANSI_COLOR_BRIGHT_GREEN ANSI_COLOR_GREEN BLINK_ON BLINK_OFF ITALICS_ON ITALICS_OFF ANSI_EOL  EMOJI_SPEAKER_HIGH_VOLUME ANSI_RESET ANSI_ERASE_LINE ANSI_COLOR_BRIGHT_RED
                    call validate-function SET_CURSOR_COLOR_BY_HEX ANSI_MOVE_TO_COL 
                rem Done validating:
                    set  validated_play_wav_file=1
        )

rem Validate parameter:
        set                                WAV_FILE=%1
        call validate-environment-variable WAV_FILE
        call validate-file-extension      %WAV_FILE% "wav"


rem Play the wav with ffmpeg's ffplay, but only outputting the line that says its duration, so we know what to expect:
rem Let's also change the cursor to magenta while this is happening 😎
        echos %ANSI_SAVE_POSITION%%ANSI_COLOR_BRIGHT_GREEN%%BLINK_ON%%PLAY%  %EMOJI_SPEAKER_HIGH_VOLUME%%BLINK_OFF%%@SET_CURSOR_COLOR_BY_HEX[FF00FF]%ANSI_COLOR_BRIGHT_RED%
        (ffplay -nodisp -hide_banner  -autoexit "%@UNQUOTE[%WAV_FILE]"  |&:u8 grep -i duration) 


rem Restore position & cursor color, overwrite duration information, as it's no longer relevant...
        echos %@ANSI_MOVE_TO_COL[1]%ANSI_ERASE_LINE%%ANSI_RESTORE_POSITION%%ANSI_MOVE_UP_1%%@ANSI_MOVE_TO_COL[1]%ANSI_EOL%
        echos %ANSI_COLOR_GREEN%%CHECK% Played '%italics_on%%@FILENAME[%wav_file%]%italics_off%'...
        call set-cursor
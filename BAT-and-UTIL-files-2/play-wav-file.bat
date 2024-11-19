@Echo OFF
@on break cancel

rem Validate environment:
        if 1 ne %validated_play_wav_file (
                rem we want ffplay, part of ffmpeg:
                    set      validate_in_path_message=FFMPEG needs to be installed
                    call     validate-in-path ffplay 
                    unset /q validate_in_path_message

                rem we want grep, and we want our play-button emoji and ansi controls:
                    call validate-in-path               grep
                    call validate-function              SET_CURSOR_COLOR_BY_HEX ANSI_MOVE_TO_COL 
                    call validate-environment-variables PLAY CHECK ANSI_SAVE_POSITION ANSI_MOVE_UP_1 ANSI_RESTORE_POSITION ANSI_COLOR_BRIGHT_GREEN ANSI_COLOR_GREEN BLINK_ON BLINK_OFF ITALICS_ON ITALICS_OFF ANSI_EOL  EMOJI_SPEAKER_HIGH_VOLUME ANSI_RESET ANSI_ERASE_LINE ANSI_COLOR_BRIGHT_RED

                rem Prevent repeat environment validation:
                    set  validated_play_wav_file=1
        )

rem Validate that the parameter exists, and is a wav file:
        set                                 WAV_FILE=%1
        call validate-environment-variable  WAV_FILE
        call validate-file-extension       %WAV_FILE% "wav"

rem Cosmetics: save position, change color of text and cursor, display play+speaker emoji:
        echos %ANSI_SAVE_POSITION%%ANSI_COLOR_BRIGHT_GREEN%%BLINK_ON%%PLAY%  %EMOJI_SPEAKER_HIGH_VOLUME%%BLINK_OFF%%@SET_CURSOR_COLOR_BY_HEX[FF00FF]%ANSI_COLOR_BRIGHT_RED%



rem Play the wav with ffmpeg's ffplay.exe, but only outputting the line that says its duration, so we know what to expect:
        (ffplay -nodisp -hide_banner -autoexit "%@UNQUOTE[%WAV_FILE]"  |&:u8  grep -i duration) 



rem Cosmetics: Restore position & cursor color, overwrite duration information with success report, fix cursor
        rem echos %@ANSI_MOVE_TO_COL[1]%ANSI_ERASE_LINE%%ANSI_RESTORE_POSITION%%ANSI_MOVE_UP_1%%@ANSI_MOVE_TO_COL[1]%ANSI_EOL%
        echos %@ANSI_MOVE_TO_COL[1]%ANSI_ERASE_LINE%%ANSI_MOVE_UP_1%%@ANSI_MOVE_TO_COL[1]%ANSI_EOL%
        echos %ANSI_COLOR_GREEN%%CHECK% Played '%italics_on%%@FILENAME[%wav_file%]%italics_off%'...%ANSI_RESET%
        echo %CURSOR_RESET%

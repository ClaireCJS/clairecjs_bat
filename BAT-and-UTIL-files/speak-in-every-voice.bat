@Echo OFF

set NUM_VOICES=%@EXECSTR[wsay -l|wc -l]

echo.
echo %ANSI_MOVE_UP_1%%ANSI_SAVE_POSITION%

do voice_num = 1 to %NUM_VOICES%

    echos %ANSI_RESTORE_POSITION%
    call print-message important_less "%ANSI_GREEN%%EMOJI_LOUDSPEAKER% Voice %BOLD_ON%#%@ANSI_BG[0,96,0]%voice_num%%@ANSI_BG[0,0,0]%BLINK_OFF%%BOLD_OFF%%BOLD_ON%/%NUM_VOICES% %EMOJI_LOUDSPEAKER%"
    wsay "%*" -v %voice_num%

enddo

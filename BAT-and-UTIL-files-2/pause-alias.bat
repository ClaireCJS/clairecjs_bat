@loadbtm on
@Echo off
@on break cancel



rem Bypassing pauses is important for automation...
        if %NOPAUSE eq 1 (goto :END)


rem Parameter passing:
        unset /q EXTRA_PAUSE_MODE
        unset /q EXTRA_PAUSE_NUMBER_OF_PAUSES

        :Param_Fetch
        set PARAMS=%$
        SET PARAM_1=%@UNQUOTE[%1]
        SET PARAM_2=%@UNQUOTE[%2]
        SET PARAM_3=%@UNQUOTE[%3]
        SET PARAM_4=%@UNQUOTE[%4]
        SET PARAM_5=%@UNQUOTE[%5]
        SET PARAM_6=%@UNQUOTE[%6]

        rem Help parameter:
                iff "%PARAM_1" == "/?" .or. "%PARAM_1" == "-?" .or. "%PARAM_1" == "/h" .or. "%PARAM_1" == "-h" .or. "%PARAM_1" == "--help" .or. "%PARAM_1" == "?" .or. "%PARAM_1" == "help" .or. "%PARAM_1" == "--h" .or. "%PARAM_1" == "-?" .or. "%PARAM_1" == "--?" then
                    :Usage
                    %COLOR_ADVICE%
                                    echo.
                                    echo USAGE: %0   ———————————————————— normal pause
                                    echo USAGE: %0 /# 5 ————————————————— a countdown of 5 pauses
                    %COLOR_NORMAL%
                    goto :END
                endiff

        rem Extra-pause mode:
                :@echo iff          "%PARAM_1%"  == "/#" then {param_2=%param_2%}
                if %EXTRA_PAUSE_MODE eq 1 goto :ExtraPauseModeDone
                iff          "%PARAM_1%"  == "/#" then
                          if "%PARAM_2%"  ==   "" goto :Usage
                          set    EXTRA_PAUSE_MODE=1
                          set    EXTRA_PAUSE_NUMBER_OF_PAUSES=%PARAM_2%
                          shift 2
                          goto :Param_Fetch
                elseif 
                          set    EXTRA_PAUSE_MODE=0
                        unset /q EXTRA_PAUSE_NUMBER_OF_PAUSES
                endiff
                :ExtraPauseModeDone


rem Set window title if instructed:
        iff "%PAUSE_WINDOW_TITLE%" != "" then
                set OLD_TITLE=%@EXECSTR[title]
                title %PAUSE_WINDOW_TITLE%
                set PAUSE_WINDOW_TITLE=
        endiff


rem Save position:
        set pause_row=%_ROW
        set pause_col=%_column


rem Preface the pause with an emoji for visual processing ease and make it the color we want:
        echos %ANSI_COLOR_PAUSE%%EMOJI_PAUSE_BUTTON% %ANSI_RESET%%@char[27][ q%@char[27]]12;#FFFF00%@char[7]

rem Clear the keyboard buffer [/C option] to prevent accidental pause-bypasses:
        inkey /c

rem Do the actual pause:
        *pause /C %@unquote[%PARAMS%]

rem A pause that doesn't start at the beginning of the line (due to our emoji) doesn't clear itself correctly (TCC bug or maybe VT100 working as intended), so we must do it ourselves:
rem But we use it to our advantage to leave it if we have additional pauses, because it looks better that way
rem Let’s additionally go back to where the pause was initiated and erase the rest of that line:
        echos %ANSI_RESET%%ANSI_EOL%%@ANSI_MOVE_TO_ROW[%@EVAL[%pause_row% + 1]]%@ANSI_MOVE_TO_COL[%pause_col%]%ANSI_ERASE_TO_END_OF_LINE%



rem An extra countdown for those times when we really want to get in a fight with our future selves:
        iff defined EXTRA_PAUSE_NUMBER_OF_PAUSES .and. "%EXTRA_PAUSE_MODE%" == "1" .and. %ANSI_COLORS_HAVE_BEEN_SET eq 1 then
                if "%PARAMS%" == "" set PARAMS=Press any key when ready!  ``
                echo %@ANSI_MOVE_TO_COL[1]%pause% %PARAMS%
                rem first_number=%@EVAL[%EXTRA_PAUSE_NUMBER_OF_PAUSES%-1]
                set first_number=%@EVAL[%EXTRA_PAUSE_NUMBER_OF_PAUSES%]
                do pauseNum = %@EVAL[%EXTRA_PAUSE_NUMBER_OF_PAUSES%-1] to 1 by -1
                        set numdis=%@EVAL[%pauseNum-1]
                        set spacer_len=%@EVAL[%@LEN[%@EVAL[%first_number]]-%@LEN[%numdis]]
                        iff %spacer_len gt -1 then
                                set spacer=%@REPEAT[ ,%spacer_len%]``
                        else
                                set spacer=``
                        endiff
                        echos      %pause% %ANSI_RESET%%blink_on%%ansi_red%%ansi_save_position%
                        echos %spacer%[%ansi_bright_red%%numdis%%ansi_red%]%blink_off% %@ANSI_RANDFG_SOFT[]%@ANSI_RANDBG_SOFT[]%blink_on%`` 
                        echos Press any key when ready... 
                        (*pause /c) >nul 
                        echos %blink_off%%@ansi_move_left[3] %CHECK%%@ansi_move_up[1]%@ansi_move_left[%@EVAL[33-%@LEN[%@EVAL[%@LEN[%spacer]]]]]
                        echos %ansi_restore_positon%%@ansi_move_down[1]%ansi_reset%%ansi_color_green%%blink_off%
                        echos %spacer%%@ANSI_MOVE_LEFT[%@EVAL[%@LEN[%first_number]-2]]%@IF[%@LEN[%first_number%] le 2, ,]``
                        echos %faint_on%[%numdis%] %@ANSI_RANDFG_SOFT[]%@ANSI_RANDBG_SOFT[]%blink_off%%faint_off%
                        echos Press any key when ready
                        echo %ansi_reset%%@ansi_move_right[28]
                enddo
        endiff



:END

:Cleanup
        rem Window title back to previous:
                if "%PAUSE_WINDOW_TITLE%" != "" (set PAUSE_WINDOW_TITLE= %+ title %OLD_TITLE%)

        rem Don't leave trash:
                unset /q adsfEXTRA_PAUSE_MODE
                unset /q adsfEXTRA_PAUSE_NUMBER_OF_PAUSES

        rem 20241028: 🐐 Having some problems Ctrl-Break'ing out of scripts, as an experiment wondering if perhaps adding a slight delay here would help?
                delay /m250


        echos %CURSOR_RESET%


@echo off
on break cancel


:USAGE: askyn "question" "yes|no" {run ’askyn’ without parameters to see usage)
:SIDE-EFFECTS: sets ANSWER to Y or N, and sets DO_IT to 1 (if yes) or 0 (if no)
:DEPENDENCIES: {see validate-in-path section}

rem Validate environment once:
        iff 1 ne %VALIDATED_ASKYN% then
                call validate-in-path echos print-if-debug important.bat fatal_error.bat warning.bat repeat if set color_alarm_hex color_success_hex
                call validate-functions CURSOR_COLOR_BY_WORD CURSOR_COLOR_BY_HEX 

                set VALIDATED_ASKYN=1
        endiff


rem Set default flags:                                                                    
        set NO_ENTER_KEY=0
        set BIG_QUESTION=0
        set NOTITLE=0
        set RUNNING_TESTS=0
        set WAIT_OPS=
        SET WAIT_TIMER_ACTIVE=0


rem Get positional required parameters:
        iff defined AskYN_question then
                set ASK_QUESTION=%AskYN_question% 
                unset /q AskYN_question
        else
                set ASK_QUESTION=%[1]
                shift
        endiff

        iff "%1" eq "test" then
                set RUNNING_TESTS=1
        else        
                set RUNNING_TESTS=0
        endiff        

        set DEFAULT_ANSWER=%1 %+ shift
        set WAIT_TIME=%1      %+ shift

        if "%WAIT_TIME%" ne "" .and. "%WAIT_TIME%" ne "NULL" .and. "%WAIT_TIME%" ne "0" (set WAIT_OPS=/T /W%wait_time% %+ set WAIT_TIMER_ACTIVE=1)
        

rem Get non-positional parameters:
        set ADDITIONAL_KEYS=

        :grab_next_param
                if "%1" eq "" (goto :done_grabbing_params)
                if "%1" eq "noenter" .or. "%1" eq "no_enter" (shift %+ set NO_ENTER_KEY=1 %+ goto :grab_next_param)
                if "%1" eq "big"     .or. "%1" eq "big"      (shift %+ set BIG_QUESTION=1 %+ goto :grab_next_param)
                if "%1" eq "notitle" .or. "%1" eq "no_title" (shift %+ set NOTITLE=1      %+ goto :grab_next_param)
        :done_grabbing_params

rem Get positional-at-end parameter for expanded answer meanings (“what does ‘A’ equal?”-type questions):
        iff "%1%" ne "" then
                set ADDITIONAL_KEYS=%1
                shift
                iff "%1" ne "" then
                        rem echo we gotta figure this out: “%1$”
                        set meanings=%1$
                        for %%tmpLetterForMeaning in (%1$) do ( gosub processLetterMeaning "%tmpLetterForMeaning%")
                endiff
        endiff                

rem cancel %+ 🐐

                        goto :DoneWithMeaning
                                :processLetterMeaning                         
                                        rem echo tmpLetterForMeaning  = %tmpLetterForMeaning%
                                        if "1" ne "%@RegEx[:,%tmpLetterForMeaning%]" (
                                                call fatal_error "%left_quote%%tmpLetterForMeaning%%right_quote% makes no sense. This parameter should have been in the forumat of %left_quote%{%italics_on%letter%italics_off%}:{%italics_on%meaning%italics_off%}%right_quote%, where %left_quote%letter%right_quote% is a letter found in our additional allowable keys %faint_on%(currently set to %left_quote%additional_keys%%right_quote%)%faint_off%"
                                        )
                                        set tmp_meaning_letter=%@LEFT[1,%tmpLetterForMeaning%]
                                        set tmp_meaning_expand=%@RIGHT[%@EVAL[%@LEN[%tmpLetterForMeaning]-2],%tmpLetterForMeaning%]
                                        echo %left_apostrophe%%tmp_meaning_letter%%right_apostrophe% means %left_apostrophe%%tmp_meaning_expand%%right_apostrophe%
                                return
                        :DoneWithMeaning                        



iff "%ASK_QUESTION%" eq "" .or. "%ASK_QUESTION%" eq "help" .or. "%ASK_QUESTION%" eq "--help" .or. "%ASK_QUESTION%" eq "/?" .or. "%ASK_QUESTION%" eq "-?" .or. "%ASK_QUESTION%" eq "-h" then
                %color_advice%
                echo.
                echo USAGE: You did this: %ansi_color_warning_soft%%0 %*%ansi_color_advice%
                %color_advice%
                echo.
                echo USAGE: call askyn "Question to ask without question mark" [yes or no] [time to wait...0 if not waiting] ["big" if you want double height, "notitle" if you don’t want the title changed]
                echo USAGE: 
                echo USAGE: 1ˢᵗ param: the question you want to ask WITHOUT question mark at the end
                echo USAGE: 2ⁿᵈ param: default answer of “yes” or “no” or “None” to not have a default [or possiby of another available response letter, but this is untested]
                echo USAGE: 3ʳᵈ param: is wait_time before expiration, at which point the default answer is selected. Use “0” to wait forever.
                echo USAGE: 4ᵗʰ-6ᵗʰ params: 
                echo USAGE:            1) can be   “big”   to make it a double-height question
                echo USAGE:            2) can be “no_title” if you don’t want the window title changed while asking
                echo USAGE:            2) can be “no_enter” if you don’t want the ENTER key to select the default optoin
                echo USAGE: 
                echo USAGE: Next(5ᵗʰ/6ᵗʰ/7ᵗʰ)  param: a list of additional keystrokes allowed 
                echo USAGE                      For example:   This allows Y or N          : “AskYn "Ovewrite file" no 0” 
                echo USAGE                      For example:   This allows Y or N or A or R: “AskYn "Ovewrite file" no 0 AR” 
                echo USAGE:              
                echo USAGE: Next parameters: an optional list of what each of the additional letters means in our special format:
                echo USAGE: 
                echo USAGE                      For example:   This allows Y or N or A or R: “AskYn "Ovewrite file" no 0 AR A:Abort,R:Retry” 
                echo USAGE: 
                echo USAGE: EXAMPLES:
                echo USAGE: 
                echo USAGE:     call AskYN "Do you want to" yes 
                echo USAGE:     call AskYN "Do you want to" yes 30
                echo USAGE:     call AskYN "Do you want to" no  30 big
                echo USAGE: 
                echo USAGE: RESULTS:
                echo USAGE: 
                echo USAGE:    1) sets OUR_ANSWER to either "Y" or "N"
                echo USAGE:    2) sets DO_IT      to either "1" or "2"
                echo USAGE: 
                echo USAGE: TO RUN TEST SUITE:
                echo USAGE: 
                echo USAGE:     call AskYn test
                echo USAGE: 
                %color_normal%
    goto :END
endiff




REM Test suite special case, including testing for the facts that higher timer values are wider timers which affect answer character placement:
        if 1 ne %RUNNING_TESTS goto :Not_A_Test
                cls
                call important "About to do %0 test suite"
                echo ———————————————————————————————————————————————————————————————————
                call AskYN         "  Big question defaulting to  no d:0"  no      0 big
                call AskYN         "  Big question defaulting to yes d:0" yes      0 big
                call AskYN         "Timed question defaulting to  no d:1"  no      9 big
                call AskYN         "Timed question defaulting to yes d:1" yes      9 big
                call AskYN         "TIMED question defaulting to  no d:2"  no     99 big
                call AskYN         "TIMED question defaulting to yes d:2" yes     99 big
                call AskYN         "TIMED question defaulting to  no d:3"  no    999 big
                call AskYN         "TIMED question defaulting to yes d:3" yes    999 big
                call AskYN         "TIMED question defaulting to  no d:4"  no   9999 big
                call AskYN         "TIMED question defaulting to yes d:4" yes   9999 big
                call AskYN         "TIMED question defaulting to  no d:5"  no  99999 big
                call AskYN         "TIMED question defaulting to yes d:5" yes  99999 big
                call AskYN         "TIMED question defaulting to  no d:6"  no 999999 big
                call AskYN         "TIMED question defaulting to yes d:6" yes 999999 big
                call AskYN "Generic       question defaulting to yes"     yes
                call AskYN "Generic       question defaulting to  no"      no
                call AskYN "Generic timed question defaulting to yes"     yes      9
                call AskYN "Generic timed question defaulting to  no"      no      9
                call AskYN "Generic TIMED question defaulting to yes"     yes   9999
                call AskYN "Generic TIMED question defaulting to  no"      no   9999
                goto :END
        :Not_A_Test



REM Variable setup:
        set ANSWER=
        set DO_IT=
        set OUR_ANSWER=


rem Set title for waiting-for-answer state:
        iff 1 ne %NOTITLE% then
                rem echo setting title 1 - NOTITLE = “%NOTITLE%”
                title %EMOJI_RED_QUESTION_MARK%%@UNQUOTE[%ASK_QUESTION%]%EMOJI_RED_QUESTION_MARK%
        endiff

        
REM Parameter validation:
        rem Let’s not dip into all this for something used so often: call validate-environment-variable question skip_validation_existence
        if not defined ask_question (call fatal_error "$0 called without a question being passed as the 1st parameter (also, “yes”/“no” must be 2ⁿᵈ parameter)")
        iff "%default_answer" ne "" .and. "%default_answer%" ne "yes" .and. "%default_answer%" ne "no" .and. "%default_answer%" ne "y" .and. "%default_answer%" ne "n" then
           call fatal_error "2nd parameter to %0 can only be “yes”, “no”, “y”, or “n” but was “%DEFAULT_ANSWER%”"
           rem TODO expand this to allow other letters if they were passed as available letters
        endiff
        iff "%DEFAULT_ANSWER%" eq "" then
            set default_answer=no
            call warning "Answer is defaulting to %default_answer% because 2nd parameter was not passed"
        endiff


REM Parameter massaging:
        if "%default_answer%" eq "y" (set default_answer=yes)
        if "%default_answer%" eq "n" (set default_answer=no)


REM Build the question prompt:
                          unset /q WIN7DECORATOR
        if "%OS%" eq "7" (  set    WIN7DECORATOR=*** ``)
        set BRACKET_COLOR=224,0,0
        set PRETTY_QUESTION=%@UNQUOTE[%ASK_QUESTION]
        rem echo "pretty question is “%pretty_question%”"
        rem pause
                                                           rem 2024/12/12 added this space here -----------v not sure how i feel about it
                                                           rem set PRETTY_QUESTION=%EMOJI_RED_QUESTION_MARK%%ANSI_COLOR_BRIGHT_RED%%ansi_color_prompt%%ASKYN_DECORATOR%%WIN7DECORATOR%%PRETTY_QUESTION%%ITALICS_ON%%BLINK_ON%?%BLINK_OFF%%ITALICS_OFF%%ANSI_RESET% %@ANSI_FG_RGB[%BRACKET_COLOR][
                                                           rem set PRETTY_QUESTION=%EMOJI_RED_QUESTION_MARK% %ANSI_COLOR_BRIGHT_RED%%ansi_color_prompt%%ASKYN_DECORATOR%%WIN7DECORATOR%%PRETTY_QUESTION%%ITALICS_ON%%BLINK_ON%?%BLINK_OFF%%ITALICS_OFF%%ANSI_RESET% %@ANSI_FG_RGB[%BRACKET_COLOR][
                                                           rem 2024/12/12 NOPE DON’T LIKE IT, go back to original:
                                                               set PRETTY_QUESTION=%EMOJI_RED_QUESTION_MARK%%ANSI_COLOR_BRIGHT_RED%%ansi_color_prompt%%ASKYN_DECORATOR%%WIN7DECORATOR%%PRETTY_QUESTION%%ITALICS_ON%%BLINK_ON%?%BLINK_OFF%%ITALICS_OFF%%ANSI_RESET% %@ANSI_FG_RGB[%BRACKET_COLOR][
        if "%default_answer" eq "yes" .and. %NO_ENTER_KEY ne 1 set PRETTY_QUESTION=%pretty_question%%bold%%underline%%ANSI_COLOR_PROMPT%Y%underline_off%%bold_off%                             %+ rem   capital Y
        if "%default_answer" eq "no"  .or.  %NO_ENTER_KEY eq 1 set PRETTY_QUESTION=%pretty_question%%faint%y%faint_off%                                                                        %+ rem lowercase Y
                                                               set PRETTY_QUESTION=%pretty_question%%italics_off%%bold_off%%underline_off%%double_underline_off%%@ANSI_FG_RGB[%BRACKET_COLOR]/ %+ rem           slash
        if "%default_answer" eq "yes" .or.  %NO_ENTER_KEY eq 1 set PRETTY_QUESTION=%pretty_question%%faint%n%faint_off%                                                                        %+ rem lowercase N
        if "%default_answer" eq "no"  .and. %NO_ENTER_KEY ne 1 set PRETTY_QUESTION=%pretty_question%%bold%%underline%%ANSI_COLOR_PROMPT%N%underline_off%%bold_off%                             %+ rem   capital N
                                                               set PRETTY_QUESTION=%pretty_question%%@ANSI_FG_RGB[%BRACKET_COLOR]]%EMOJI_RED_QUESTION_MARK%                                    %+ rem right bracket + ❓
                                                               set PRETTY_QUESTION_ANSWERED=%@REPLACE[%BLINK_ON%,,%PRETTY_QUESTION] %+ rem an unblinking version, so the question mark that blinks before we answer is still displayed——but stops blinking after we answer the question 

rem Check if we are not doing titling, and skip titling section if that is the case:
        if 1 eq %NOTITLE% (goto :title_done)

rem Re-set a new window title:
        set stripped=%@STRIPANSI[%@STRIPANSI[%PRETTY_QUESTION]]
        iff 1 ne %NOTITLE then
                rem echo setting title 2 - NOTITLE = “%NOTITLE%”
                title %stripped%
        endiff

rem Re-set a new window title: BUG FIX:
        rem weird bug  where "\B" got past the stripansi function, giving us titles like "❓do it?(B [(BY/n]❓" with two "(B" 
        rem in them that don’t belong, but also using %@REREPLACE on the variable didn’t work despite working on the %_WinTitle
        rem So we incrementally set and read the wintitle to fix it that way. It’s ugly, but it’s not a time-pressed situation:
        set stripped2=%@REREPLACE[\(B *\[\(B, \[,%_wintitle]
        rem echo setting title 3 - NOTITLE = “%NOTITLE%”
        title %stripped2%
        set stripped3=%@REREPLACE[\?\(B\s+\[y\/\(BN,? [y/N,%_wintitle]
        title %stripped3%
        :title_done


REM Which keys will we allow?
                               set ALLOWABLE_KEYS=yn%additional_keys%[Enter]
        if %NO_ENTER_KEY eq 1 (set ALLOWABLE_KEYS=yn%additional_keys%)




REM Print the question out with a spacer below to deal with pesky ANSI behavior:
        rem if %BIG_QUESTION eq 1 (SET xx=4)
        rem if %BIG_QUESTION ne 1 (SET xx=3)
        set XX=3
        set XX=2
        set XX=1
        if %big_question eq 1 (set XX=%@EVAL[%xx +1 ] )
        rem set XX=10
        repeat %XX% echo.
        echos   %@ANSI_MOVE_LEFT[2]``
        if %xx gt 0 (echos %@ANSI_MOVE_UP[%@EVAL[%xx-1]])
        rem sechos %@ANSI_MOVE_UP[1] %+ rem this seems to be too much for normal-size but TODO not sure about large size
        iff %BIG_QUESTION eq 1 then
                echos %@ANSI_MOVE_DOWN[1]
                rem echos %BIG_TOP%%PRETTY_QUESTION%%ANSI_CLEAR_TO_END%%newline%%BIG_BOT%%PRETTY_QUESTION% %ANSI_SAVE_POSITION%%ANSI_CLEAR_TO_END%``
                    echos %BIG_TOP%%PRETTY_QUESTION%%ANSI_CLEAR_TO_END%
                   rem   delay /m 1
                    echos %newline%%BIG_BOT%%PRETTY_QUESTION% %ANSI_SAVE_POSITION%%ANSI_CLEAR_TO_END%``
                if %WAIT_TIMER_ACTIVE eq 1 (echos %@ANSI_MOVE_UP[1])
        endiff
            
REM Load INKEY with the question, unless we’ve already printed it out:
        echos %@CURSOR_COLOR_BY_WORD[PURPLE]
                                    set INKEY_QUESTION=%PRETTY_QUESTION%
        if %WAIT_TIMER_ACTIVE eq 0 .and. %BIG_QUESTION eq 1 (set INKEY_QUESTION=)


REM Actually answer the question here —— make the windows “question” noise first, then get the user input:
        echos %ANSI_CURSOR_SHOW%
        *beep question    
        unset /q SLASH_X
        if  %BIG_QUESTION eq 1 .and. %WAIT_TIMER_ACTIVE eq 1 (set SLASH_X=/x)
        echos %ANSI_POSITION_SAVE%
        if %BIG_QUESTION eq 1 (set INKEY_QUESTION=%INKEY_QUESTION%%ANSI_POSITION_RESTORE%)
        if %BIG_QUESTION ne 1 (set INKEY_QUESTION=%INKEY_QUESTION%%ANSI_POSITION_SAVE%)
        rem as an experiment, let’s do this 100x instead of 1x:
        @rem repeat 100 input /c /w0 %%This_Line_Clears_The_Character_Buffer
        rem @call clear-buffered-keystrokes is just:
        inkey /c
        inkey %SLASH_X% %WAIT_OPS% /c /k"%ALLOWABLE_KEYS%" %INKEY_QUESTION% %%OUR_ANSWER
        echos %BLINK_OFF%%ANSI_CURSOR_SHOW%

REM set default answer if we hit ENTER, or timed out (which should only happen if WAIT_OPS exists):
        if "%WAIT_OPS%" ne "" .and. ("%OUR_ANSWER%" eq "" .or. "%OUR_ANSWER%" eq "@28") (
            set OUR_ANSWER=%default_answer%
            call print-if-debug "timed out, OUR_ANSWER set to “%OUR_ANSWER%”"
        )        

REM Make sure we have an answer, and initialize our return values
        if not defined OUR_ANSWER ( call error "OUR_ANSWER is not defined in %0" )
        set DO_IT=0
        set ANSWER=%OUR_ANSWER%

REM Process the enter key into our default answer:
        if %OUR_ANSWER% eq "@28" .or. "%@ASCII[%OUR_ANSWER]"=="64 50 56" (
            if  "%default_answer%" eq "no"  ( set DO_IT=0 %+ set ANSWER=N )
            if  "%default_answer%" eq "yes" ( set DO_IT=1 %+ set ANSWER=Y )                  
            echos  ``
            call print-if-debug "enter key processing, answer is now “%ANSWER%”"
        ) 


REM Title
        iff 1 ne %NOTITLE% then
                rem echo setting title 4 - NOTITLE = “%NOTITLE%”
                title %@STRIPANSI[%PRETTY_QUESTION] %A
        endiff


REM Set our 2 major return values that are referred to from calling scripts:
        if "%OUR_ANSWER%" eq "Y" .or. "%OUR_ANSWER%" eq "yes" (set DO_IT=1 %+ set ANSWER=Y)
        if "%OUR_ANSWER%" eq "N" .or. "%OUR_ANSWER%" eq "no"  (set DO_IT=0 %+ set ANSWER=N) 


REM Generate "pretty" answers & update the title:
        iff "%ANSWER" eq "Y" .or. "%ANSWER" eq "yes" then
                set PRETTY_ANSWER= %ANSI_BRIGHT_GREEN%%ITALICS_ON%%DOUBLE_UNDERLINE_ON%Yes%DOUBLE_UNDERLINE_OFF%%BLINK_ON%!%BLINK_OFF%%ITALICS_OFF%
                echos %@CURSOR_COLOR_BY_HEX[%color_success_hex%]
        elseiff "%ANSWER" eq "N" .or. "%ANSWER" eq "no" then 
                set PRETTY_ANSWER= %ANSI_BRIGHT_RED%%ITALICS_ON%%DOUBLE_UNDERLINE_ON%No%DOUBLE_UNDERLINE_OFF%%BLINK_ON%!%BLINK_OFF%%ITALICS_OFF%
                echos %@CURSOR_COLOR_BY_HEX[%color_alarm_hex%]
        else                
                set PRETTY_ANSWER= %ANSI_BRIGHT_GREEN%%ITALICS_ON%%DOUBLE_UNDERLINE_ON%%@UPPER[%ANSWER%]%DOUBLE_UNDERLINE_OFF%%BLINK_ON%!%BLINK_OFF%%ITALICS_OFF%
                echos %@CURSOR_COLOR_BY_WORD[magenta]
        endiff                
        call print-if-debug "our_answer is “%OUR_ANSWER”, default_answer is “%DEFAULT_ANSWER%”, answer is “%ANSWER%”, PRETTY_ANSWER is “%PRETTY_ANSWER%”"
        if 1 eq %NOTITLE% (goto :title_done_3)        
                rem echo setting title 4 - NOTITLE = “%NOTITLE%”
                title %@REPLACE[%EMOJI_RED_QUESTION_MARK,,%@STRIPANSI[%@UNQUOTE[%ASK_QUESTION]? %EMDASH% %PRETTY_ANSWER%]]
        :title_done_3


REM Re-print "pretty" question so that the auto-question mark is no longer blinking because it has now been answered, and
REM print our "pretty" answers in the right spots (challenging with double-height), erasing any timer leftovers:
        if %BIG_QUESTION ne 1 (
            if %WAIT_TIMER_ACTIVE eq 0 (echo %ANSI_POSITION_RESTORE%%PRETTY_ANSWER_ANSWERED%%@ANSI_MOVE_TO_COL[1]%PRETTY_QUESTION_ANSWERED%%PRETTY_ANSWER%)  
            if %WAIT_TIMER_ACTIVE eq 1 (echo %ANSI_POSITION_RESTORE%%ZZZZZZZZZZZZZZZZZZZZZZ%%@ANSI_MOVE_TO_COL[1]%PRETTY_QUESTION_ANSWERED%%PRETTY_ANSWER%      %ANSI_CLEAR_TO_END%``)
        )
        if %BIG_QUESTION eq 1 (           set MOVE_LEFT_BY=1
            if  %WAIT_TIMER_ACTIVE eq 1  (set MOVE_LEFT_BY=4
                if %WAIT_TIME gt 10      (set MOVE_LEFT_BY=%@eval[%MOVE_LEFT_BY + 1])
                if %WAIT_TIME gt 100     (set MOVE_LEFT_BY=%@eval[%MOVE_LEFT_BY + 1])
                if %WAIT_TIME gt 1000    (set MOVE_LEFT_BY=%@eval[%MOVE_LEFT_BY + 1])
                if %WAIT_TIME gt 10000   (set MOVE_LEFT_BY=%@eval[%MOVE_LEFT_BY + 1])
                if %WAIT_TIME gt 100000  (set MOVE_LEFT_BY=%@eval[%MOVE_LEFT_BY + 1])
                if %WAIT_TIME gt 1000000 (set MOVE_LEFT_BY=%@eval[%MOVE_LEFT_BY + 1])
                if %LEFT_MORE gt 0       (set MOVE_LEFT_BY=%@eval[%MOVE_LEFT_BY + %LEFT_MORE])
                rem LEFT_MORE is a secret kludge in case the cursor doesn’t quite move to the left enough
                echos %@ANSI_MOVE_LEFT[%MOVE_LEFT_BY]
            )
            rem DEBUG: echos %ANSI_POSITION_RESTORE%[RESTORE HERE] %+ *pause>nul

            unset /q SPACER
            if %WAIT_TIMER_ACTIVE ne 1 (set SPACER=%@ANSI_MOVE_UP[1]) 

            echos %ANSI_POSITION_RESTORE%%SPACER%%ZZZZZZZZZZZZZZZZZ%%BIG_TOP%%BLINK_ON%%PRETTY_ANSWER%%BLINK_OFF%%ANSI_CURSOR_SHOW%%ANSI_ERASE_TO_END_OF_LINE%
            echos %ANSI_POSITION_RESTORE%%SPACER%%@ANSI_MOVE_DOWN[1]%BIG_BOT%%BLINK_ON%%PRETTY_ANSWER%%BLINK_OFF%%ANSI_CURSOR_SHOW%%ANSI_ERASE_TO_END_OF_LINE%

            repeat 1 echo.
        )


goto :END

                :Oops
                    call fatal_error "That was not a valid way to call “%0” ... You need a 2ⁿᵈ parameter of “yes” or “no” to set a default_answer for when ENTER is pressed"
                 goto :END


:END


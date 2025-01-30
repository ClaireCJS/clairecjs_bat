@Echo Off
on break cancel


:USAGE: askyn "question" "yes|no" {run ’askyn’ without parameters to see usage)
:SIDE-EFFECTS: sets ANSWER to Y or N, and sets DO_IT to 1 (if yes) or 0 (if no)
:DEPENDENCIES: {see validate-in-path section}

:USAGE: NOTE: Braced    arguments are required,
:USAGE: NOTE: Bracketed arguments are optional:
:USAGE:
:USAGE: call askyn {question} {“yes” or “no” or “None”} [wait_time] [modes of operation] [extra allowable keys] [extra key meanings]
:USAGE:
:USAGE: RETURN VALUES: 1) sets %OUR_ANSWER to either “Y” or “N” ..... or one of our additional allowed keystrokes
:USAGE: RETURN VALUES: 2) sets %DO_IT      to either “1” or “0” (don’t use if using additional allowed keystrokes)
:USAGE:
:USAGE: 1ˢᵗ param: the question you want to ask WITHOUT question mark at the end
:USAGE: 2ⁿᵈ param: the default answer of “yes” or “no” ...or “None” for no default
:USAGE: 3ʳᵈ param: the wait time in seconds before using the default answer. Use “0” to wait forever.
:USAGE:
:USAGE: 4ᵗʰ-6ᵗʰ params: Modes of operation:
:USAGE:            1) can be   “big”    to make it a double-height question
:USAGE:            2) can be “no_title” if you don’t want the window title changed while asking
:USAGE:            3) can be “no_enter” if you don’t want the ENTER key to select the default option
:USAGE:
:USAGE: Next (5ᵗʰ/6ᵗʰ/7ᵗʰ++) params: a list of additional keystrokes allowed:
:USAGE:                      For example: To allow Y or N:           AskYn "Ovewrite file" no 0
:USAGE:                      For example: To allow Y or N or A or R: AskYn "Ovewrite file" no 0 AR
:USAGE:
:USAGE: Next parameters: An optional list of additional letter meanings for any additional keystrokes allowed:
:USAGE:                  EXAMPLE: To give letter meanings for A and R: AskYn "Overwrite file" no 0 AR A:Abort,R:Retry
:USAGE:                           Note that underscores in the meanings are converted to spaces
:USAGE:
:USAGE: GENERAL EXAMPLE #1: call AskYN "Do you want to" yes
:USAGE: GENERAL EXAMPLE #2: call AskYN "Do you want to" yes 30
:USAGE: GENERAL EXAMPLE #3: call AskYN "Do you want to" no  30 big MN N:Not_Sure,M:Maybe_I_Do
:USAGE:
:USAGE: TO RUN TEST SUITE: call AskYn test
:USAGE:

rem Validate environment once:
        iff 1 ne %VALIDATED_ASKYN% then
                call validate-plugin                stripansi
                call validate-in-path               echos echoerr echoserr print-if-debug important.bat fatal_error.bat warning.bat repeat if set color_alarm_hex color_success_hex
                call validate-functions             ANSI_CURSOR_CHANGE_COLOR_WORD CURSOR_COLOR_BY_HEX 
                call validate-environment-variables CURSOR_RESET ANSI_COLORS_HAVE_BEEN_SET
                set VALIDATED_ASKYN=1
        endiff


rem Set default flags:                                                                    
        set NOTITLE=0
        set BIG_QUESTION=0
        set NO_ENTER_KEY=0
        set RUNNING_TESTS=0
        SET WAIT_TIMER_ACTIVE=0
        set WAIT_OPS=
        unset /q last_key_meaning_* 


rem Get positional required parameters:
        iff defined AskYN_question then
                set ASK_QUESTION=%@UNQUOTE[%AskYN_question% ]
                unset /q AskYN_question
        else
                set ASK_QUESTION=%@UNQUOTE[%[1]]
                shift
        endiff

        iff "%1" == "test" then
                set RUNNING_TESTS=1
        else        
                set RUNNING_TESTS=0
        endiff        

        set DEFAULT_ANSWER=%1 %+ shift
        set WAIT_TIME=%1      %+ shift

        if "%WAIT_TIME%" != "" .and. "%WAIT_TIME%" != "NULL" .and. "%WAIT_TIME%" != "0" (set WAIT_OPS=/T /W%wait_time% %+ set WAIT_TIMER_ACTIVE=1)
        

rem Get non-positional parameters:
        set ADDITIONAL_KEYS=

        :grab_next_param
                if "%1" == "" (goto :done_grabbing_params)
                if "%1" == "noenter" .or. "%1" == "no_enter" (shift %+ set NO_ENTER_KEY=1 %+ goto :grab_next_param)
                if "%1" == "big"     .or. "%1" == "big"      (shift %+ set BIG_QUESTION=1 %+ goto :grab_next_param)
                if "%1" == "notitle" .or. "%1" == "no_title" (shift %+ set NOTITLE=1      %+ goto :grab_next_param)
        :done_grabbing_params

rem Get positional-at-end parameter for expanded answer key meanings (“what does ‘A’ equal?”-type questions):
        iff "%1%" != "" then
                set ADDITIONAL_KEYS=%1
                shift
                iff "%1" != "" then
                        rem echoerr we gotta figure this out: “%1$”
                        set key_meanings=%1$
                        for %%tmpLetterForKeyMeaning in (%1$) do ( gosub processLetterKeyMeaning "%tmpLetterForKeyMeaning%")
                endiff
        endiff                

rem cancel %+ 🐐

                        goto :DoneWithKeyMeaning
                                :processLetterKeyMeaning                         
                                        rem echoerr tmpLetterForKeyMeaning  = %tmpLetterForKeyMeaning%
                                        if "1" != "%@RegEx[:,%tmpLetterForKeyMeaning%]" (
                                                call fatal_error "%left_quote%%tmpLetterForKeyMeaning%%right_quote% makes no sense. This parameter should have been in the format of %left_quote%{%italics_on%letter%italics_off%}:{%italics_on%Key_Meaning%italics_off%}%right_quote%, where %left_quote%letter%right_quote% is a letter found in our additional allowable keys %faint_on%(currently set to %left_quote%additional_keys%%right_quote%)%faint_off%"
                                        )
                                        set tmp_key_meaning_letter=%@LEFT[1,%tmpLetterForKeyMeaning%]
                                        set tmp_key_meaning_expand=%@RIGHT[%@EVAL[%@LEN[%tmpLetterForKeyMeaning]-2],%tmpLetterForKeyMeaning%]
                                        rem echoerr DEBUG: %left_apostrophe%%tmp_key_meaning_letter%%right_apostrophe% means %left_apostrophe%%tmp_key_meaning_expand%%right_apostrophe%
                                        set key_meaning_%tmp_key_meaning_letter%=%tmp_key_meaning_expand%
                                return
                        :DoneWithKeyMeaning                        



iff "%ASK_QUESTION%" == "" .or. "%ASK_QUESTION%" == "help" .or. "%ASK_QUESTION%" == "--help" .or. "%ASK_QUESTION%" == "/?" .or. "%ASK_QUESTION%" == "-?" .or. "%ASK_QUESTION%" == "-h" then
                if not defined ansi_color_orange call set-ansi force
                %color_advice%
                echoerr.
                echoerr USAGE: NOTE: %ANSI_COLOR_MAGENTA%%italics_on%Braced%italics_off%    arguments are %italics_on%%ansi_color_red%required%italics_off%%ansi_color_advice%%ansi_color_advice%,
                echoerr USAGE: NOTE: %ANSI_COLOR_MAGENTA%%italics_on%Bracketed%italics_off% arguments are %italics_on%%ansi_color_red%optional%italics_off%%ansi_color_advice%%ansi_color_advice%:
                echoerr USAGE:                
                rem echoerr USAGE: You did this: %ansi_color_warning_soft%%0 %*%ansi_color_advice%
                echoerrs USAGE: %ansi_color_bright_yellow%call askyn ``
                echoerrs %ansi_color_orange%{%ansi_color_yellow%%italics_on%%ansi_color_magenta%question%italics_off%%ansi_color_orange%} %ansi_color_orange%{“%ansi_color_bright_yellow%yes%ansi_color_orange%” %italics_on%%ansi_color_yellow%or%italics_off% %ansi_color_orange%“%ansi_color_bright_yellow%no%ansi_color_orange%”%ansi_color_magneta%%italics_on% %ansi_color_yellow%or%italics_off% %ansi_color_orange%“%ansi_color_bright_yellow%None%ansi_color_orange%”%ansi_color_yellow%%ansi_color_orange%}                
                echoerrs  %ansi_color_orange%[%ansi_color_yellow%%italics_on%%ansi_color_magenta%wait_time%ansi_color_orange%%italics_off%] 
                rem echoerrs  %ansi_color_orange%[%ansi_color_orange%“%ansi_color_bright_yellow%big%ansi_color_orange% 
                rem echoerrs  %ansi_color_yellow%%italics_on%or%italics_off% %ansi_color_orange%“%ansi_color_bright_bright_yellow%notitle%ansi_color_orange%%ansi_color_yellow%%italics_off%%ansi_color_orange%”]
                echoerrs  %ansi_color_orange%[%ansi_color_magenta%%italics_on%modes of operation%italics_off%%ansi_color_orange%] 
                echoerrs  %ansi_color_orange%[%italics_on%%ansi_color_magenta%extra allowable keys%italics_off%%italics_off%%ansi_color_orange%]%ansi_color_advice%
                echoerrs  %ansi_color_orange%[%italics_on%%ansi_color_magenta%extra key meanings%italics_off%%italics_off%%ansi_color_orange%]%ansi_color_advice%
                echoerr.
                echoerr USAGE: 
                echoerr USAGE: %ansi_color_orange%RETURN VALUES: %ansi_color_advice%1) sets %ansi_color_yellow%%italics_on%`%`OUR_ANSWER%italics_off%%ansi_color_advice% to either %ansi_color_orange%“%ansi_color_bright_yellow%Y%ansi_color_orange%”%ansi_color_advice% or %ansi_color_orange%“%ansi_color_bright_yellow%N%ansi_color_orange%”%ansi_color_advice% ..... or one of our additional allowed keystrokes
                echoerr USAGE: %ansi_color_orange%RETURN VALUES: %ansi_color_advice%2) sets %ansi_color_yellow%%italics_on%`%`DO_IT     %italics_off%%ansi_color_advice% to either %ansi_color_orange%“%ansi_color_bright_yellow%1%ansi_color_orange%”%ansi_color_advice% or %ansi_color_orange%“%ansi_color_bright_yellow%0%ansi_color_orange%”%ansi_color_advice% (don’t use if using additional allowed keystrokes)
                echoerr %ANSI_COLOR_ADVICE%USAGE: 
                echoerr USAGE: %ansi_color_orange%1ˢᵗ param: %ansi_color_magenta%the %ansi_color_yellow%question%ansi_color_magenta% you want to ask %ansi_color_advice%%italics_on%%blink_on%%double_underline_on%WITHOUT%underline_off%%blink_off%%italics_off% question mark at the end%ansi_color_advice%
                echoerr USAGE: %ansi_color_orange%2ⁿᵈ param: %ansi_color_magenta%the %ansi_color_yellow%default answer%ansi_color_magenta% of %ansi_color_orange%“%ansi_color_bright_yellow%yes%ansi_color_orange%” %ansi_color_magenta%or %ansi_color_orange%“%ansi_color_bright_yellow%no%ansi_color_orange%” %ansi_color_magenta%...or %ansi_color_orange%%ansi_color_orange%“%ansi_color_bright_yellow%None%ansi_color_orange%” %ansi_color_magenta%for no default%ansi_color_advice%
                echoerr USAGE: %ansi_color_orange%3ʳᵈ param: %ansi_color_magenta%the %ansi_color_yellow%wait time in seconds%ansi_color_magenta% before using the %ansi_color_yellow%default answer%ansi_color_advice%. Use %ansi_color_orange%“%ansi_color_bright_yellow%0%ansi_color_orange%” %ansi_color_advice%to wait forever.
                echoerr USAGE: 
                echoerr USAGE: %ansi_color_orange%4ᵗʰ-6ᵗʰ params: %ansi_color_magenta%Modes of operation:%ansi_color_advice%
                echoerr USAGE:            %ansi_color_advice%1) can be   %ansi_color_orange%“%ansi_color_bright_yellow%big%ansi_color_orange%”    %ansi_color_advice%to make it a %ansi_color_yellow%double-height %ansi_color_advice%question%ansi_color_advice%
                echoerr USAGE:            %ansi_color_advice%2) can be %ansi_color_orange%“%ansi_color_bright_yellow%no_title%ansi_color_orange%” %ansi_color_advice%if you don’t want the %ansi_color_yellow%window title%underline_off%%ansi_color_advice% changed while asking%ansi_color_advice%
                echoerr USAGE:            %ansi_color_advice%3) can be %ansi_color_orange%“%ansi_color_bright_yellow%no_enter%ansi_color_orange%” %ansi_color_advice%if you don’t want the %ansi_color_yellow%%double_underline_on%%italics_on%ENTER%italics_off%%underline_off%%ansi_color_advice% key to select the default option%ansi_color_advice%
                echoerr USAGE: 
                echoerr USAGE: %ansi_color_orange%Next (5ᵗʰ/6ᵗʰ/7ᵗʰ++) params: %ansi_color_magenta%a list of %ansi_color_yellow%additional keystrokes allowed%ansi_color_magenta%:%ansi_color_advice%
                echoerr USAGE:                      For example: To allow %ansi_color_bright_yellow%Y%ansi_color_advice% or %ansi_color_bright_yellow%N%ansi_color_advice%:           %ansi_color_bright_yellow%AskYn "Ovewrite file" no 0%ansi_color_advice% 
                echoerr USAGE:                      For example: To allow %ansi_color_bright_yellow%Y%ansi_color_advice% or %ansi_color_bright_yellow%N%ansi_color_advice% or %ansi_color_bright_yellow%A%ansi_color_advice% or %ansi_color_bright_yellow%R%ansi_color_advice%: %ansi_color_bright_yellow%AskYn "Ovewrite file" no 0 %double_underline_on%AR%underline_off%%ansi_color_advice% 
                echoerr USAGE:              
                echoerr USAGE: %ansi_color_orange%Next parameters: %ansi_color_magenta%An optional list of %ansi_color_yellow%additional letter meanings%ansi_color_magenta% for any additional keystrokes allowed%ansi_color_magenta%:%ansi_color_advice%
                echoerr USAGE:                  EXAMPLE: To give %ansi_color_yellow%letter meanings%ansi_color_advice% for %ansi_color_bright_yellow%A%ansi_color_advice% and %ansi_color_bright_yellow%R%ansi_color_advice%: %ansi_color_bright_yellow%AskYn "Overwite file" no 0 AR %double_underline_on%A:Abort,R:Retry%underline_off%%ansi_color_advice%
                echoerr USAGE:                           Note that %ialics_on%underscores%ialics_off% in the meanings are converted to %ialics_on%spaces %ialics_off%
                echoerr USAGE:
                echoerr USAGE: %ansi_color_orange%GENERAL EXAMPLE #1: %ansi_color_bright_yellow%call AskYN "Do you want to" yes %ansi_color_advice%
                echoerr USAGE: %ansi_color_orange%GENERAL EXAMPLE #2: %ansi_color_bright_yellow%call AskYN "Do you want to" yes 30%ansi_color_advice%
                echoerr USAGE: %ansi_color_orange%GENERAL EXAMPLE #3: %ansi_color_bright_yellow%call AskYN "Do you want to" no  30 big MN N:Not_Sure,M:Maybe_I_Do%ansi_color_advice%
                echoerr USAGE: 
                echoerr USAGE: %ansi_color_orange%TO RUN TEST SUITE: %ansi_color_bright_yellow%call AskYn test%ansi_color_advice%
                echoerr USAGE: 
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
                call AskYN "Generic TIMED question defaulting to  no with extra allowable keys"      no   9999  ABCD A:Apple,B:Banana,C:Carrot,D:Durian
                
                goto :END
        :Not_A_Test



REM Variable setup:
        set ANSWER=
        set DO_IT=
        set OUR_ANSWER=


rem Set title for waiting-for-answer state:
        iff 1 ne %NOTITLE% then
                rem echoerr setting title 1 - NOTITLE = “%NOTITLE%”
                title %EMOJI_RED_QUESTION_MARK%%@UNQUOTE[%ASK_QUESTION%]%EMOJI_RED_QUESTION_MARK%
        endiff

        
REM Parameter validation:
        rem Let’s not dip into all this for something used so often: call validate-environment-variable question skip_validation_existence
        if not defined ask_question (call fatal_error "$0 called without a question being passed as the 1st parameter (also, “yes”/“no” must be 2ⁿᵈ parameter)")
        iff "%default_answer" != "" .and. "%default_answer%" != "yes" .and. "%default_answer%" != "no" .and. "%default_answer%" != "Y" .and. "%default_answer%" != "N" then
           call fatal_error "2nd parameter to %0 can only be “yes”, “no”, “y”, or “n” but was “%DEFAULT_ANSWER%”"
           rem TODO expand this to allow other letters if they were passed as available letters
        endiff
        iff "%DEFAULT_ANSWER%" == "" then
            set default_answer=no
            call warning "Answer is defaulting to %default_answer% because 2nd parameter was not passed"
        endiff


REM Parameter massaging:
        if "%default_answer%" == "Y" (set default_answer=yes)
        if "%default_answer%" == "N" (set default_answer=no)


REM Build the question prompt:
                          unset /q WIN7DECORATOR
        if "%OS%" == "7" (  set    WIN7DECORATOR=*** ``)
        set BRACKET_COLOR=224,0,0
        set PRETTY_QUESTION=%@UNQUOTE[%ASK_QUESTION]
        rem echoerr "pretty question is “%pretty_question%”"
        rem pause
                                                           rem 2024/12/12 added this space here -----------v not sure how i feel about it
                                                           rem set PRETTY_QUESTION=%EMOJI_RED_QUESTION_MARK%%ANSI_COLOR_BRIGHT_RED%%ansi_color_prompt%%ASKYN_DECORATOR%%WIN7DECORATOR%%PRETTY_QUESTION%%ITALICS_ON%%BLINK_ON%?%BLINK_OFF%%ITALICS_OFF%%ANSI_RESET% %@ANSI_FG_RGB[%BRACKET_COLOR][
                                                           rem set PRETTY_QUESTION=%EMOJI_RED_QUESTION_MARK% %ANSI_COLOR_BRIGHT_RED%%ansi_color_prompt%%ASKYN_DECORATOR%%WIN7DECORATOR%%PRETTY_QUESTION%%ITALICS_ON%%BLINK_ON%?%BLINK_OFF%%ITALICS_OFF%%ANSI_RESET% %@ANSI_FG_RGB[%BRACKET_COLOR][
                                                           rem 2024/12/12 NOPE DON’T LIKE IT, go back to original: ...
                                                           rem set PRETTY_QUESTION=%EMOJI_RED_QUESTION_MARK%%ANSI_COLOR_BRIGHT_RED%%ansi_color_prompt%%ASKYN_DECORATOR%%WIN7DECORATOR%%PRETTY_QUESTION%%ITALICS_ON%%BLINK_ON%? %italics_off%%emoji_red_question_mark%%BLINK_OFF%%ITALICS_OFF%%ANSI_RESET% %@ANSI_FG_RGB[%BRACKET_COLOR][
                                                           rem 2024/12/24 but why?!?! I don’t like this either .. putting the space back in again haha ... Keep it!!
                                                               set PRETTY_QUESTION=%EMOJI_RED_QUESTION_MARK% %ANSI_COLOR_BRIGHT_RED%%ansi_color_prompt%%ASKYN_DECORATOR%%WIN7DECORATOR%%PRETTY_QUESTION%%ITALICS_ON%%BLINK_ON%%italics_off%%@CHAR[65311]%BLINK_OFF%%ITALICS_OFF%%ANSI_RESET% %@ANSI_FG_RGB[%BRACKET_COLOR][
        if "%default_answer" == "yes" .and. %NO_ENTER_KEY ne 1 set PRETTY_QUESTION=%pretty_question%%bold%%underline%%ANSI_COLOR_PROMPT%Y%underline_off%%bold_off%                             %+ rem   capital Y
        if "%default_answer" == "no"  .or.  %NO_ENTER_KEY eq 1 set PRETTY_QUESTION=%pretty_question%%faint%y%faint_off%                                                                        %+ rem lowercase Y
                                                               set PRETTY_QUESTION=%pretty_question%%italics_off%%bold_off%%underline_off%%double_underline_off%%@ANSI_FG_RGB[%BRACKET_COLOR]/ %+ rem           slash
        if "%default_answer" == "yes" .or.  %NO_ENTER_KEY eq 1 set PRETTY_QUESTION=%pretty_question%%faint%n%faint_off%                                                                        %+ rem lowercase N
        if "%default_answer" == "no"  .and. %NO_ENTER_KEY ne 1 set PRETTY_QUESTION=%pretty_question%%bold%%underline%%ANSI_COLOR_PROMPT%N%underline_off%%bold_off%                             %+ rem   capital N
                                                rem extra allowable keys go here, with a slash first:
                                                        set  spread=%@ReReplace[(.),\1 ,%additional_keys%]
                                                        for %%tmpKey in (%spread%) do (
                                                               rem PRETTY_QUESTION=%PRETTY_QUESTION%%@ANSI_FG_RGB[%BRACKET_COLOR]/%faint_on%%@LOWER[%tmpKey%]%faint_off%
                                                               set PRETTY_QUESTION=%PRETTY_QUESTION%%@ANSI_FG_RGB[%BRACKET_COLOR]/%faint_on%%@UPPER[%tmpKey%]%faint_off%
                                                               set      key_meaning_%tmpKey=%[key_meaning_%tmpkey%] 
                                                               set last_key_meaning_%tmpKey=%[key_meaning_%tmpkey%] 
                                                        )
                                                               set PRETTY_QUESTION=%pretty_question%%@ANSI_FG_RGB[%BRACKET_COLOR]]%EMOJI_RED_QUESTION_MARK%                                    %+ rem right bracket + ❓
                                                               set PRETTY_QUESTION_ANSWERED=%@REPLACE[%BLINK_ON%,,%PRETTY_QUESTION] %+ rem an unblinking version, so the question mark that blinks before we answer is still displayed——but stops blinking after we answer the question 

rem Check if we are not doing titling, and skip titling section if that is the case:
        if 1 eq %NOTITLE% (goto :title_done)

rem Re-set a new window title:
        rem stripped=%@STRIPANSI[%@STRIPANSI[%PRETTY_QUESTION]] %+ rem why were we doing this twice? 
        set stripped=%@STRIPANSI[%PRETTY_QUESTION]
        iff 1 ne %NOTITLE then
                rem echoerr setting title 2 - NOTITLE = “%NOTITLE%”
                title %stripped%
        endiff

rem Re-set a new window title: BUG FIX:
        rem weird bug  where "\B" got past the stripansi function, giving us titles like "❓do it?(B [(BY/n]❓" with two "(B" 
        rem in them that don’t belong, but also using %@REREPLACE on the variable didn’t work despite working on the %_WinTitle
        rem So we incrementally set and read the wintitle to fix it that way. It’s ugly, but it’s not a time-pressed situation:
        set stripped2=%@REREPLACE[\(B *\[\(B, \[,%_wintitle]
        rem echoerr setting title 3 - NOTITLE = “%NOTITLE%”
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
        repeat %XX% echoerr.
        echoserr   %@ANSI_MOVE_LEFT[2]``
        rem ? if %xx gt 0 (echoserr %@ANSI_MOVE_UP[%@EVAL[%xx-1]])
        if %xx gt 0 (echoserr %@ANSI_MOVE_UP[%@EVAL[%xx]])
        rem echoserr %@ANSI_MOVE_UP[1] %+ rem this seems to be too much for normal-size but TODO not sure about large size
        iff %BIG_QUESTION eq 1 then
                echoserr %@ANSI_MOVE_DOWN[1]
                rem echoserr %BIG_TOP%%PRETTY_QUESTION%%ANSI_CLEAR_TO_END%%newline%%BIG_BOT%%PRETTY_QUESTION% %ANSI_SAVE_POSITION%%ANSI_CLEAR_TO_END%``
                    echoserr %BIG_TOP%%PRETTY_QUESTION%%ANSI_CLEAR_TO_END%
                   rem   delay /m 1
                    echoserr %newline%%BIG_BOT%%PRETTY_QUESTION% %ANSI_SAVE_POSITION%%ANSI_CLEAR_TO_END%``
                if %WAIT_TIMER_ACTIVE eq 1 (echoserr %@ANSI_MOVE_UP[1])
        endiff
            
REM Load INKEY with the question, unless we’ve already printed it out:
        echoserr %@ANSI_CURSOR_CHANGE_COLOR_WORD[PURPLE]
        on break cancel
                                                             set INKEY_QUESTION=%PRETTY_QUESTION%
        if %WAIT_TIMER_ACTIVE eq 0 .and. %BIG_QUESTION eq 1 (set INKEY_QUESTION=)


REM Actually answer the question here —— make the windows “question” noise first, then get the user input:
        echoserr %ANSI_CURSOR_SHOW%
        if 1 ne %SLEEPING *beep question    
        unset /q SLASH_X
        if  %BIG_QUESTION eq 1 .and. %WAIT_TIMER_ACTIVE eq 1 (set SLASH_X=/x)
        echoserr %ANSI_POSITION_SAVE%
        if %BIG_QUESTION eq 1 (set INKEY_QUESTION=%INKEY_QUESTION%%ANSI_POSITION_RESTORE%)
        if %BIG_QUESTION ne 1 (set INKEY_QUESTION=%INKEY_QUESTION%%ANSI_POSITION_SAVE%)
        rem as an experiment, let’s do this 100x instead of 1x:
        @rem repeat 100 input /c /w0 %%This_Line_Clears_The_Character_Buffer
        rem @call clear-buffered-keystrokes is just:
        inkey /c
        rem The " >&:u8 con " is so it shows up to the console even if the entire thing is wrapped in something redirecting STDOUT to nul ... This is a case where we want to “pop out” of STDERR *into* STDOUT / have both combined into STDOUT, so that we see it and can answer the prompt:
        rem Alas, this causes our unicode characters to be munged because so much of TCC’s internal workings don’t support modern characters
        rem (inkey %SLASH_X% %WAIT_OPS% /c /k"%ALLOWABLE_KEYS%" %INKEY_QUESTION% %%OUR_ANSWER) >:u8&:u8 con
        inkey %SLASH_X% %WAIT_OPS% /c /k"%ALLOWABLE_KEYS%" %INKEY_QUESTION% %%OUR_ANSWER
        echos %BLINK_OFF%%ANSI_CURSOR_SHOW%

REM set default answer if we hit ENTER, or timed out (which should only happen if WAIT_OPS exists):
        if "%WAIT_OPS%" != "" .and. ("%OUR_ANSWER%" == "" .or. "%OUR_ANSWER%" == "@28") (
            set OUR_ANSWER=%default_answer%
            call print-if-debug "timed out, OUR_ANSWER set to “%OUR_ANSWER%”"
        )        

REM Make sure we have an answer, and initialize our return values
        if not defined OUR_ANSWER ( call error "OUR_ANSWER is not defined in %0" )
        set DO_IT=0
        set ANSWER=%OUR_ANSWER%

REM Process the enter key into our default answer:
        if %OUR_ANSWER% == "@28" .or. "%@ASCII[%OUR_ANSWER]"=="64 50 56" (
            if  "%default_answer%" == "no"  ( set DO_IT=0 %+ set ANSWER=N )
            if  "%default_answer%" == "yes" ( set DO_IT=1 %+ set ANSWER=Y )                  
            echoserr  ``
            call print-if-debug "enter key processing, answer is now “%ANSWER%”"
        ) 


REM Title
        iff 1 ne %NOTITLE% then
                rem echoerr setting title 4 - NOTITLE = “%NOTITLE%”
                title %@STRIPANSI[%PRETTY_QUESTION] %A
        endiff


REM Set our 2 major return values that are referred to from calling scripts:
        if "%OUR_ANSWER%" == "Y" .or. "%OUR_ANSWER%" == "yes" (set DO_IT=1 %+ set ANSWER=Y)
        if "%OUR_ANSWER%" == "N" .or. "%OUR_ANSWER%" == "no"  (set DO_IT=0 %+ set ANSWER=N) 


REM Generate "pretty" answers & update the title:
        iff "%ANSWER" == "Y" .or. "%ANSWER" == "yes" then
                set PRETTY_ANSWER= %ANSI_BRIGHT_GREEN%%ITALICS_ON%%DOUBLE_UNDERLINE_ON%Yes%DOUBLE_UNDERLINE_OFF%%BLINK_ON%!%BLINK_OFF%%ITALICS_OFF%
                echoserr %@CURSOR_COLOR_BY_HEX[%color_success_hex%]
        elseiff "%ANSWER" == "N" .or. "%ANSWER" == "no" then 
                set PRETTY_ANSWER= %ANSI_BRIGHT_RED%%ITALICS_ON%%DOUBLE_UNDERLINE_ON%No%DOUBLE_UNDERLINE_OFF%%BLINK_ON%!%BLINK_OFF%%ITALICS_OFF%
                echoserr %@CURSOR_COLOR_BY_HEX[%color_alarm_hex%]
        else                
                iff "" != "%[key_meaning_%answer%]" then
                        rem (Make sure to change underscores to spaces)
                        set VALUE_TO_USE=%@ReReplace[\_, ,%[key_meaning_%ANSWER%]]
                else
                        set VALUE_TO_USE=%@UPPER[%ANSWER%]
                endiff
                set PRETTY_ANSWER= %ANSI_BRIGHT_GREEN%%ITALICS_ON%%DOUBLE_UNDERLINE_ON%%VALUE_TO_USE%%DOUBLE_UNDERLINE_OFF%%BLINK_ON%!%BLINK_OFF%%ITALICS_OFF%
                echoserr %CURSOR_RESET%
        endiff                
        call print-if-debug "our_answer is “%OUR_ANSWER”, default_answer is “%DEFAULT_ANSWER%”, answer is “%ANSWER%”, PRETTY_ANSWER is “%PRETTY_ANSWER%”"
        if 1 eq %NOTITLE% (goto :title_done_3)        
                rem echoerr setting title 4 - NOTITLE = “%NOTITLE%”
                title %@REPLACE[%EMOJI_RED_QUESTION_MARK,,%@STRIPANSI[%@UNQUOTE[%ASK_QUESTION]? %EMDASH% %PRETTY_ANSWER%]]
        :title_done_3


REM Re-print "pretty" question so that the auto-question mark is no longer blinking because it has now been answered, and
REM print our "pretty" answers in the right spots (challenging with double-height), erasing any timer leftovers:
        if %BIG_QUESTION ne 1 (
            if %WAIT_TIMER_ACTIVE eq 0 (echoerr %ANSI_POSITION_RESTORE%%PRETTY_ANSWER_ANSWERED%%@ANSI_MOVE_TO_COL[1]%PRETTY_QUESTION_ANSWERED%%PRETTY_ANSWER%)  
            if %WAIT_TIMER_ACTIVE eq 1 (echoerr %ANSI_POSITION_RESTORE%%ZZZZZZZZZZZZZZZZZZZZZZ%%@ANSI_MOVE_TO_COL[1]%PRETTY_QUESTION_ANSWERED%%PRETTY_ANSWER%      %ANSI_CLEAR_TO_END%``)
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
                echoserr %@ANSI_MOVE_LEFT[%MOVE_LEFT_BY]
            )
            rem DEBUG: echoserr %ANSI_POSITION_RESTORE%[RESTORE HERE] %+ *pause>nul

            unset /q SPACER
            if %WAIT_TIMER_ACTIVE ne 1 (set SPACER=%@ANSI_MOVE_UP[1]) 

            echoserr %ANSI_POSITION_RESTORE%%SPACER%%ZZZZZZZZZZZZZZZZZ%%BIG_TOP%%BLINK_ON%%PRETTY_ANSWER%%BLINK_OFF%%ANSI_CURSOR_SHOW%%ANSI_ERASE_TO_END_OF_LINE%
            echoserr %ANSI_POSITION_RESTORE%%SPACER%%@ANSI_MOVE_DOWN[1]%BIG_BOT%%BLINK_ON%%PRETTY_ANSWER%%BLINK_OFF%%ANSI_CURSOR_SHOW%%ANSI_ERASE_TO_END_OF_LINE%

            repeat 1 echoerr.
        )


goto :END

                :Oops
                    call fatal_error "That was not a valid way to call “%0” ... You need a 2ⁿᵈ parameter of “yes” or “no” to set a default_answer for when ENTER is pressed"
                 goto :END


:END

unset key_meaning_* tmp_key_meaning_*


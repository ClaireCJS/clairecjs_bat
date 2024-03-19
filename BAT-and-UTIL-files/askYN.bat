@echo off

:USAGE: askyn "question" "yes|no" - 1st param is question, 2nd is yes/no defult, 3rd is wait_time before expiration (NULL for no wait time), 4th is "no_enter" do disallow enter key, 5th is "big" to make this a big-text prompt
:SIDE-EFFECTS: sets ANSWER to Y or N, and sets DO_IT to 1 (if yes) or 0 (if no)
:DEPENDENCIES: set-colors.bat validate-environment-variable.bat validate-environment-variables.bat print-if-debug.bat fatal_error.bat bigecho.bat bigechos.bat echobig.bat echosbig.bat

if "%1" eq "help" .or. "%1" eq "--help" .or. "%1" eq "/?" .or. "%1" eq "-?" .or. "%1" eq "-h" (
    %color_advice%
    echo USAGE: askyn "question" "yes|no" - 1st param is question, 2nd is yes/no defult, 3rd is wait_time before expiration
    goto :END
)


REM Parameter catching:
        set question=%1
        set ANSWER=
        set DEFAULT_ANSWER=%2
        set DO_IT=
        set OUR_ANSWER=

        set  WAIT_OPS=
        set  WAIT_TIME=%3
        SET  WAIT_TIMER_ACTIVE=0
        if "%WAIT_TIME%" ne "" .and. "%WAIT_TIME%" ne "NULL" .and. "%WAIT_TIME%" ne "0" (set WAIT_OPS=/T /W%wait_time% %+ set WAIT_TIMER_ACTIVE=1)

        set PARAM_4=%4
                                                                    set NO_ENTER_KEY=0
        if "%PARAM_4%" eq "noenter" .or. "%PARAM_4%" eq "no_enter" (set NO_ENTER_KEY=1)
        if "%PARAM_5%" eq "noenter" .or. "%PARAM_5%" eq "no_enter" (set NO_ENTER_KEY=1)
        REM DEBUG: echo PARAM_4 = %PARAM_4 ... NO_ENTER_KEY is %NO_ENTER_KEY

        set PARAM_5=%5                             
                                                           set BIG_QUESTION=0
        if "%PARAM_4%" eq "big" .or. "%PARAM_5%" eq "big" (set BIG_QUESTION=1)

        
REM Parameter validation:
        call validate-environment-variable question skip_validation_existence
        if "%default_answer" ne "" .and. "%default_answer%" ne "yes" .and. "%default_answer%" ne "no" .and. "%default_answer%" ne "y" .and. "%default_answer%" ne "n" (
           call fatal_error "2nd parameter to %0 can only be 'yes', 'no', 'y', or 'n' but was '%2'"
        )
        if "%2" eq "" (
            set default_answer=no
            call warning "Answer is defaulting to %default_answer% because 2nd parameter was not passed"
        )

REM Parameter processing/massaging:
        if "%default_answer%" eq "y" (set default_answer=yes)
        if "%default_answer%" eq "n" (set default_answer=no)


REM Build the question prompt:
                          set WIN7DECORATOR=
        if "%OS%" eq "7" (set WIN7DECORATOR=*** ``)
        set BRACKET_COLOR=224,0,0
        rem                                                                 vvvvvvvvvvvvvvvvvvvvvv--- inserted this 2024/03/18 for double-height questions but havfe concerns that this is inserting presentation logic in a bad place for maintainence
                                      set QUESTION=%EMOJI_RED_QUESTION_MARK%%ANSI_COLOR_BRIGHT_RED%%ASKYN_DECORATOR%%WIN7DECORATOR%%@UNQUOTE[%question]?%ANSI_RESET% %@ANSI_FG_RGB[%BRACKET_COLOR][
        if "%default_answer" eq "yes" set QUESTION=%question%%bold%%underline%%ANSI_COLOR_PROMPT%Y%underline_off%%bold_off%
        if "%default_answer" eq "no"  set QUESTION=%question%%faint%y%faint_off%
                                      set QUESTION=%question%%italics_off%%bold_off%%underline_off%%double_underline_off%%@ANSI_FG_RGB[%BRACKET_COLOR]/
        if "%default_answer" eq "yes" set QUESTION=%question%%faint%n%faint_off%
        if "%default_answer" eq "no"  set QUESTION=%question%%bold%%underline%%ANSI_COLOR_PROMPT%N%underline_off%%bold_off%
                                      set QUESTION=%question%%@ANSI_FG_RGB[%BRACKET_COLOR]]%EMOJI_RED_QUESTION_MARK%

REM Which keys will we allow?
                               set ALLOWABLE_KEYS=yn[Enter]
        if %NO_ENTER_KEY eq 1 (set ALLOWABLE_KEYS=yn)

REM Decide how to display the question prompt:
                                    set ECHO_COMMAND=echos
        if defined ASKYN_DECORATOR (set ECHO_COMMAND=echos %ASKYN_DECORATOR%)
        if %BIG_QUESTION eq 1      (set ECHO_COMMAND=%@REPLACE[echos,call bigechos ,%ECHO_COMMAND])
        if defined ASKYN_DECORATOR (set ASKYN_DECORATOR=)


REM Actually print the question (and use the system sound for 'question')
        rem    timer spacer [0] is '%TIMER_SPACER%'%newline%question [0] is '%QUESTION'
        rem                         set TIMER_SPACER=.     ``
        rem IF %WAIT_TIME gt 9     (set TIMER_SPACER=%TIMER_SPACER% ``)
        rem IF %WAIT_TIME gt 99    (set TIMER_SPACER=%TIMER_SPACER% ``)
        rem IF %WAIT_TIME gt 999   (set TIMER_SPACER=%TIMER_SPACER% ``)
        rem IF %WAIT_TIME gt 9999  (set TIMER_SPACER=%TIMER_SPACER% ``)
        rem IF %WAIT_TIME gt 99999 (set TIMER_SPACER=%TIMER_SPACER% ``)
        rem not a good approach for double-height questions: IF %WAIT_TIMER_ACTIVE eq 1 (echos %TIMER_SPACER%``)                %+ rem Spacer because of TCCv31 bug where timer resets to column 1
        rem timer spacer [A] is '%TIMER_SPACER%'%newline%question [A] is '%QUESTION'
        rem IF %WAIT_TIMER_ACTIVE eq 1 (set QUESTION=%TIMER_SPACER%%QUESTION%) %+ rem Spacer because of TCCv31 bug where timer resets to column 1
        rem timer spacer [B] is '%TIMER_SPACER%'%newline%question [B] is '%QUESTION'

        rem echos %ANSI_COLOR_PROMPT% 
        rem %ECHO_COMMAND% %QUESTION%%ANSI_POSITION_SAVE%``  %+ rem yes, there should be no space between %ECHO_COMMAND% and %QUESTION%
        if %BIG_QUESTION eq 1 (call echosbig %QUESTION%)
        rem make the windows 'question' noise:

REM Actually answer the question here:
        set INKEY_QUESTION=%QUESTION%%ANSI_POSITION_SAVE%
        if %BIG_QUESTION eq 1 .and. %WAIT_TIMER_ACTIVE eq 0 (set INKEY_QUESTION=)
        rem   %ANSI_COLOR_INPUT%%BLINK_ON%%BIG_TEXT_OFF%
        echos %ANSI_COLOR_INPUT%%BIG_TEXT_OFF%
        call print-if-debug "inkey /x %WAIT_OPS% /c /k'%ALLOWABLE_KEYS%' %%OUR_ANSWER"
        rem This exposed different bugs: if %BIG_QUESTION eq 1 (set INKEY_QUESTION=%INKEY_QUESTION%%NEWLINE%)
        rem %BIG_QUESTION eq 1 (set INKEY_QUESTION=%@CHAR[8254]%ANSI_POSITION_SAVE%) %+ rem Kludge for double-height questions we want something that appears to be a space, and in this situation we are only drawing the lower half of the chracter, and this overline character is blank in the lower half
        rem if  %BIG_QUESTION eq 1 (set INKEY_QUESTION=%ANSI_POSITION_SAVE%) 
        beep question
        inkey /x %WAIT_OPS% /c /k"%ALLOWABLE_KEYS%" %INKEY_QUESTION% %%OUR_ANSWER

REM set default answer if we hit ENTER, or timed out (which should only happen if WAIT_OPS exists):
        if "%WAIT_OPS%" ne "" .and. ("%OUR_ANSWER%" eq "" .or. "%OUR_ANSWER%" eq "@28") (
            REM echo.
            set OUR_ANSWER=%default_answer%
            call print-if-debug "timed out, OUR_ANSWER set to '%OUR_ANSWER%'"
        )        

REM Make sure we have an answer, and initialize our return values
        call validate-environment-variable OUR_ANSWER
        set DO_IT=0
        :pushet ANSWER=N
        set ANSWER=%OUR_ANSWER%

REM Process the enter key into our default answer
        if %OUR_ANSWER% eq "@28" .or. "%@ASCII[%OUR_ANSWER]"=="64 50 56" (
            if  "%default_answer%" eq "no"  ( set DO_IT=0 %+ set ANSWER=N )
            if  "%default_answer%" eq "yes" ( set DO_IT=1 %+ set ANSWER=Y )                  
            echos  ``
            call print-if-debug "enter key processing, answer is now '%ANSWER%'"
        ) 

REM Timer-bug fix stuff:
        call print-if-debug "our_answer is '%OUR_ANSWER', default_answer is '%DEFAULT_ANSWER%', answer is '%ANSWER%'"
        if "%ANSWER" eq "Y" .or. "%ANSWER" eq "yes" (set OUR_ANSWER_PRETTY=%ANSI_BRIGHT_GREEN%%ITALICS_ON%%DOUBLE_UNDERLINE_ON%Yes%DOUBLE_UNDERLINE_OFF%%BLINK_ON%!%BLINK_OFF%%ITALICS_OFF%)
        if "%ANSWER" eq "N" .or. "%ANSWER" eq "no"  (set OUR_ANSWER_PRETTY=%ANSI_BRIGHT_RED%%ITALICS_ON%%DOUBLE_UNDERLINE_ON%No%DOUBLE_UNDERLINE_OFF%%BLINK_ON%!%BLINK_OFF%%ITALICS_OFF%)
        echos %BLINK_OFF%
        rem WAIT_TIMER_ACTIVE eq 1                          (                echos %@ANSI_MOVE_TO_COL[1]%TIMER_SPACER%%@ANSI_MOVE_TO_COL[1]%ANSI_BRIGHT_WHITE%%ITALICS_ON%%OUR_ANSWER_PRETTY%%ITALICS_OFF%%BLINK_OFF%%ANSI_POSITION_RESTORE%)
        rem WAIT_TIMER_ACTIVE eq 1 .and. %BIG_QUESTION eq 1 (echos %ANSI_MOVE_UP_1%%@ANSI_MOVE_TO_COL[1]%TIMER_SPACER%%@ANSI_MOVE_TO_COL[1]%ANSI_BRIGHT_WHITE%%ITALICS_ON%%OUR_ANSWER_PRETTY%%ITALICS_OFF%%BLINK_OFF%%ANSI_POSITION_RESTORE%)
        
        rem if %WAIT_TIMER_ACTIVE eq 1  (echos %ANSI_POSITION_RESTORE% Yes)
        rem if %WAIT_TIMER_ACTIVE eq 1  (echos %ANSI_POSITION_RESTORE% %ANSI_BRIGHT_WHITE%%ITALICS_ON%%OUR_ANSWER_PRETTY%%ITALICS_OFF%%BLINK_OFF%)
        rem if %WAIT_TIMER_ACTIVE eq 1 .and. %BIG_QUESTION eq 1 (echos %ANSI_MOVE_UP_1%%TIMER_SPACER%%ANSI_BRIGHT_WHITE%%ITALICS_ON%%OUR_ANSWER_PRETTY%%ITALICS_OFF%%BLINK_OFF%%ANSI_POSITION_RESTORE%)

        rem echos %ANSI_COLOR_INPUT%%ANSI_POSITION_SAVE%

REM Set our return values
        call print-if-debug "if '%WAIT_OPS%' ne '' .and. '%OUR_ANSWER%' eq ''"
        if "%OUR_ANSWER%" eq "Y" .or. "%OUR_ANSWER%" eq "yes" ( set DO_IT=1 %+ set ANSWER=Y)
        if "%OUR_ANSWER%" eq "N" .or. "%OUR_ANSWER%" eq "no"  ( set DO_IT=0 %+ set ANSWER=N) 
        
        REM Echo out what we just typed
        REM In the case of big text, we need to go up a line and fill in the top-half of the letter we just typed!
        rem if %BIG_QUESTION ne 1 (echo %@ANSI_LEFT[1]%ITALICS%%BOLD%%BLINK_ON%%ANSWER%%BLINK_OFF%%BOLD_OFF%%ITALICS_OFF%)
        REM if %BIG_QUESTION ne 1 (echo %ANSI_POSITION_RESTORE%%ANSI_MOVE_UP_1%%ITALICS%%BOLD%%BLINK_ON%%ANSWER%%BLINK_OFF%%BOLD_OFF%%ITALICS_OFF%)       
        if %BIG_QUESTION ne 1 .and. %WAIT_TIMER_ACTIVE eq 0 (echo %@ANSI_MOVE_LEFT[1] %OUR_ANSWER_PRETTY% %@ANSI_MOVE_TO_COL[1]%QUESTION%)  %+ rem re-copy the question over itself to stop the prompt-related blinking  
        if %BIG_QUESTION ne 1 .and. %WAIT_TIMER_ACTIVE eq 1 (echo %@ANSI_MOVE_TO_COL[1]%QUESTION% %OUR_ANSWER_PRETTY%      ``)              %+ rem re-copy the question over itself to stop the prompt-related blinking  
        if %BIG_QUESTION eq 1 (echo %ANSI_POSITION_RESTORE%%BLINK_ON%%OUR_ANSWER_PRETTY%%BLINK_OFF%%ANSI_ERASE_TO_END_OF_LINE%%ANSI_POSITION_RESTORE%%@ANSI_MOVE_UP[1]%BIG_TOP%%BLINK_ON%%OUR_ANSWER_PRETTY%%BLINK_OFF%%ANSI_ERASE_TO_END_OF_LINE%%ANSI_POSITION_RESTORE%%ANSI_RESET%)
        REM echo OUR_ANSWER=%OUR_ANSWER%


goto :END


                :Oops
                    call fatal_error "That was not a valid way to call %0 ... You need a 2nd parameter of 'yes' or 'no' to set a default_answer for when ENTER is pressed"
                 goto :END


:END

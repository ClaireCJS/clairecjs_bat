@set RECEIVED_ERRORLEVEL_2=%?
@set RECEIVED_ERRORLEVEL_1=%_?
@REM keep those in "2,1" order!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! —— _? contains the exit code of the last internal command. You must use or save this value immediately, because it is set by every internal command, including the one used to save it. Result codes: 0 command successful,1=usage error occurred,2=another TCC error occurred         
@Echo OFF
@on break cancel



rem   😎😎😎😎       ███████  ███ ███  ███████         ███ ███  █████    ███████   █████   ██   ██     █    ███████  ███████          😎😎😎😎
rem   😎😎😎😎       █  █  █   █   █    █    █          █   █     █      █  █  █     █      █   █      █    █  █  █   █    █          😎😎😎😎
rem   😎😎😎😎          █      █   █    █               █   █     █         █        █      ██ ██     █ █      █      █               😎😎😎😎   
rem   😎😎😎😎          █      █   █    █  █            █   █     █         █        █      ██ ██     █ █      █      █  █            😎😎😎😎
rem   😎😎😎😎          █      █████    ████            █   █     █         █        █      █ █ █    █   █     █      ████            😎😎😎😎
rem   😎😎😎😎          █      █   █    █  █            █   █     █         █        █      █ █ █    █   █     █      █  █            😎😎😎😎
rem   😎😎😎😎          █      █   █    █               █   █     █         █        █      █   █    █████     █      █               😎😎😎😎
rem   😎😎😎😎          █      █   █    █    █          █   █     █   █     █        █      █   █    █   █     █      █    █          😎😎😎😎
rem   😎😎😎😎         ███    ███ ███  ███████          █████   ███████    ███     █████   ███ ███  ███ ███   ███    ███████          😎😎😎😎
rem   😎😎😎😎                                                                                                                        😎😎😎😎
rem   😎😎😎😎                                                                                                                        😎😎😎😎
rem   😎😎😎😎    ███████  ██████   ██████     ███    ██████            ████      █    ███████    ████   ███ ███  ███████  ██████     😎😎😎😎
rem   😎😎😎😎     █    █   █    █   █    █   █   █    █    █          █    █     █    █  █  █   █    █   █   █    █    █   █    █    😎😎😎😎
rem   😎😎😎😎     █        █    █   █    █  █     █   █    █         █           █       █     █         █   █    █        █    █    😎😎😎😎
rem   😎😎😎😎     █  █     █    █   █    █  █     █   █    █         █          █ █      █     █         █   █    █  █     █    █    😎😎😎😎
rem   😎😎😎😎     ████     █████    █████   █     █   █████          █         █   █     █     █         █████    ████     █████     😎😎😎😎
rem   😎😎😎😎     █  █     █  █     █  █    █     █   █  █           █         █   █     █     █         █   █    █  █     █  █      😎😎😎😎
rem   😎😎😎😎     █        █  █     █  █    █     █   █  █           █         █████     █     █         █   █    █        █  █      😎😎😎😎
rem   😎😎😎😎     █    █   █   █    █   █    █   █    █   █           █    █   █   █     █      █    █   █   █    █    █   █   █     😎😎😎😎
rem   😎😎😎😎    ███████  ███  ██  ███  ██    ███    ███  ██           ████   ███ ███   ███      ████   ███ ███  ███████  ███  ██    😎😎😎😎




rem      WHEN TO USE?:   * Use after any important command in any workflow, ever.
rem                      * Not only will it halt things on error, but it will set a %REDO flag which one can 
rem                        use to repeat a block of script over and over until the errors condition is fixed.
rem                        SUPER USEFUL for complicated-workflow-where-a-single-step-might-break situations.



rem      INSTALLATION:   Requires an alias to be set up to capture values when something is called:
rem                      call=`set _callingerrorlevel=%_? %+ set _callingerrorlevel2=%? %+ set _callingfile=%@full[%%0] %+ *call %$`



rem      USAGE:          call errorlevel.bat                          <---- do this! after everything! everythiiiinnng! any program! any command! at the end of bat-files!
rem                      call errorlevel.bat "fail msg"               <---- if you need a more informative  error message when things go wrong
rem                      call errorlevel.bat "fail msg" "success msg" <---- if you need a more reassuring success message when things go right


rem      SIDE EFFECTS:   
rem                      1) sets %REDO_BECAUSE_OF_ERRORLEVEL% to 1 so you can use that result to re-run your situation infinitely until the error goes away
rem                      2) sets cursor color to green on success, red on failure
rem                      3) also outputs a .BAT pattern that can be incorporated into calling scripts


:PUBLISH:
:DESCRIPTION: TODO
:DEPENDENCIES: validate-in-path.bat   echos beep sed color colors.bat colortool.bat randcolor.bat print-message.bat fatal_error.bat fatalerror.bat exit-maybe.bat important.bat advice.bat debug.bat print-if-debug.bat settmpfile.bat 

iff  1   ne  %validated_errorlevel then
         call validate-in-path       echos beep sed color colors.bat colortool.bat randcolor.bat print-message.bat fatal_error.bat fatalerror.bat exit-maybe.bat important.bat advice.bat debug.bat print-if-debug.bat settmpfile.bat 
         call validate-env-vars      ANSI_CURSOR_CHANGE_TO_BLOCK_BLINKING ANSI_PREFERRED_CURSOR_SHAPE ANSI_ERASE_TO_EOL ANSI_BACKGROUND_BLACK ANSI_COLOR_BRIGHT_RED COLOR_SUCCESS COLOR_SUCCESS_HEX COLOR_NORMAL COLOR_ADVICE ANSI_COLOR_WARNING COLOR_ALARM_HEX ITALICS_ON ITALICS_OFF BLINK_ON BLINK_OFF STAR
         call validate-functions     ANSI_CURSOR_CHANGE_COLOR_HEX
         set  validated_errorlevel=1
endiff


REM Configuration: Debug
    set DEBUG_CALLER_ERRORLEVEL=0


REM Parameters: Process: errorlevel
    REM RECEIVED_ERRORLEVEL_1=%_?     Moved to top of file, in reverse order, for very specific reasons!  
    REM RECEIVED_ERRORLEVEL_2=%?      Moved to top of file, in reverse order, for very specific reasons!
    set OUR_ERRORLEVEL=0
    if %DEBUG_CALLER_ERRORLEVEL gt 0 call debug "OUR_ERRORLEVEL is[A] '%OUR_ERRORLEVEL%', RECEIVED_ERRORLEVEL_1=%RECEIVED_ERRORLEVEL_1%, RECEIVED_ERRORLEVEL_2=%RECEIVED_ERRORLEVEL_2%, _callingerrorlevel='%_callingerrorlevel%', _callingerrorlevel2='%_callingerrorlevel2%', _callingfile='%_callingfile'"

    if %RECEIVED_ERRORLEVEL_1   gt %OUR_ERRORLEVEL   (set OUR_ERRORLEVEL=%RECEIVED_ERRORLEVEL_1)
    if %RECEIVED_ERRORLEVEL_2   gt %OUR_ERRORLEVEL   (set OUR_ERRORLEVEL=%RECEIVED_ERRORLEVEL_2)
    if  %_callingerrorlevel     gt %OUR_ERRORLEVEL   (set OUR_ERRORLEVEL=%_callingerrorlevel   )
    if  %_callingerrorlevel2    gt %OUR_ERRORLEVEL   (set OUR_ERRORLEVEL=%_callingerrorlevel2  )
    
    if %DEBUG_CALLER_ERRORLEVEL gt 0 (call debug "OUR_ERRORLEVEL is[B] '%OUR_ERRORLEVEL%', _callingerrorlevel='%_callingerrorlevel%', _callingerrorlevel2='%_callingerrorlevel2%', _callingfile='%_callingfile'")


REM Parameters: Process: calling file
    set CALLING_FILE_UNKNOWN=(calling file unknown)
    set OUR_CALLING_FILE=%CALLING_FILE_UNKNOWN%
    if defined %_callingfile set OUR_CALLING_FILE=%_callingfile
                             set OUR_CALLING_FILE_2=%_pbatchname
    rem echo OUR1==%OUR_CALLING_FILE%,OUR2==%OUR_CALLING_FILE_2% BUT pbatchname==%_pbatchname  callingfile==%_callingfile

    REM If there is a %3 then we didn't listen to the invocation instructions and screwed up -- just treat the entire set of parameters as one big error message
    iff "%3" ne "" then
        set OUR_FAILURE_MESSAGE=%@UNQUOTE[%*]
        set OUR_SUCCESS_MESSAGE=
    else
        set OUR_FAILURE_MESSAGE=%@UNQUOTE[%1]
        set OUR_SUCCESS_MESSAGE=%@UNQUOTE[%2]
    endiff



iff %OUR_ERRORLEVEL% le 0 then
        echos %@ANSI_CURSOR_CHANGE_COLOR_HEX[%color_success_hex]%ANSI_PREFERRED_CURSOR_SHAPE%
        iff defined OUR_SUCCESS_MESSAGE then
                @Echo ON
                %COLOR_SUCCESS%
                echo %OUR_SUCCESS_MESSAGE%
                %COLOR_NORMAL%
        endiff
        
        rem Set return value (and a couple aliases of convenience):
                set REDO_BECAUSE_OF_ERRORLEVEL=0
                set ERRORCATCHER_ERRORLEVEL=0
                set REDO=0
endiff

iff %OUR_ERRORLEVEL% gt 0 then
        set ERRORCATCHER_ERRORLEVEL=%OUR_ERRORLEVEL%
        set REDO_BECAUSE_OF_ERRORLEVEL=1
        set REDO=

        rem Change cursor to angry: BIG BLINKING RED BLOCK:
                if not defined ANSI_PREFERRED_CURSOR_SHAPE (SET ANSI_PREFERRED_CURSOR_SHAPE=%ANSI_CURSOR_CHANGE_TO_BLOCK_BLINKING%)
                echos %@ANSI_CURSOR_CHANGE_COLOR_HEX[%color_alarm_hex]%ANSI_PREFERRED_CURSOR_SHAPE%

        iff "%OUR_FAILURE_MESSAGE%" eq "" then
                set OUR_FAILURE_MESSAGE=An ERRORLEVEL of %OUR_ERRORLEVEL% (bad) was returned, which is greater than 0 (good)!
        else
                set OUR_FAILURE_MESSAGE=%OUR_FAILURE_MESSAGE%   [errorlevel=%OUR_ERRORLEVEL%]
        endiff
        REM call  print-if-debug * ARGV is: %*


        set OUR_COMMAND=that_thing_you_did[.exe/.bat/etc]
        if "%OUR_CALLING_FILE%"   ne "" (set OUR_COMMAND=%OUR_CALLING_FILE%)
        if "%OUR_CALLING_FILE_2%" ne "" (set OUR_COMMAND_2=%OUR_CALLING_FILE_2%)

        set   optional_success_msg_in_quotes="optional success message in quotes"
        set   optional_failure_msg_in_quotes="optional failure message in quotes"
        if "%OUR_SUCCESS_MESSAGE%" ne "" (set optional_success_msg_in_quotes=%@QUOTE[%OUR_SUCCESS_MESSAGE])
        if "%OUR_FAILURE_MESSAGE%" ne "" (set optional_failure_msg_in_quotes=%@QUOTE[%OUR_FAILURE_MESSAGE]
                                          set optional_failure_msg_in_quotes=%@EXECSTR[echo %optional_failure_msg_in_quotes|:u8sed -r 's/ *\[errorlevel\=[0-9]+\]//'])

        echo.
        color bright white on blue
        echo %ANSI_ERASE_TO_EOL%
        echo %STAR% %OUR_FAILURE_MESSAGE%%ANSI_ERASE_TO_EOL%
        echo %STAR% Calling BAT: %ITALICS_ON%%blink_on%%ANSI_COLOR_BRIGHT_RED%%ANSI_BACKGROUND_BLACK% %[_PBATCHNAME]%ITALICS_OFF%%blink_off% %ANSI_COLOR_WARNING%%ANSI_ERASE_TO_EOL%
        %COLOR_NORMAL% 
        repeat 3 echo.
        call advice "* You can put code like this in your script:"
        call advice "     :Redo_1"
        if "%OUR_COMMAND%" ne "%CALLING_FILE_UNKNOWN%" (call advice "                         %OUR_COMMAND%" )
        call advice "             call %OUR_COMMAND_2%" 
        REM call advice "             call %0 %optional_success_msg_in_quotes% %optional_failure_msg_in_quotes%"
        %COLOR_ADVICE%
        echos                       ``
        echo call %0 "optional success message" "optional failure message"
        REM having to use 64 or 128 or 256 percent signs to sextuple-escape the character is peak-lifetime-level madness and somehow i feel a lack of setdos commands in the lineage up to this point made this unnecessarily happen... other times, I think this is a testament to just how far I'll go:
        call advice "     if %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%REDO eq 1 (goto :Redo_1)"
        echo.
        call advice "     %ITALICS_ON%(You can also use the variable 'REDO_BECAUSE_OF_ERRORLEVEL', if 'REDO' gives you fears of namespace collision. %DOUBLE_UNDERLINE_ON%Both%DOUBLE_UNDERLINE_OFF% get set.)%ITALICS_OFF%"
        echo.
        beep
        setlocal
                set NOPAUSE=0
                call exit-maybe
        endlocal
endiff


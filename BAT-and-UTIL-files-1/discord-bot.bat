@loadBTM on
@Echo OFF
 on break cancel
rem cls


:USAGE: call discord-bot
:USAGE: call discord-bot testing ——— won’t hidei t



rem CONFIG: 
        set                SLEEP_TIME_AFTER_RUNNING_BEFORE_IT_HAS_STARTED=2

        set        ECHOABLE_NAME_OF_WHAT_WE_ARE_RUNNING=Discord ClaireCJS bot
        set PROCESS_WINDOW_TITLE_OF_WHAT_WE_ARE_RUNNING=Discord ClaireCJS_Bot
        set                       SCRIPT_WE_ARE_RUNNING=%bat%\discord_bot_clairecjs_bot.py
        set         INVOCATION_OF_SCRIPT_WE_ARE_RUNNING=python %SCRIPT_WE_ARE_RUNNING%
        set        PROCESS_REGEX_OF_WHAT_WE_ARE_RUNNING=python.*discord_bot_clairecjs_bot


rem Validate environment:
        iff "1" != "%validated_discordbot%" then
                call validate-environment-variables SCRIPT_WE_ARE_RUNNING PROCESS_REGEX_OF_WHAT_WE_ARE_RUNNING emoji_have_been_set ansi_colors_have_been_set
                call validate-in-path               python isRunning tasklist grep sed wait sleep bigecho
                set  validated_discordbot=1
        endiff

rem Parameter branching:
        set MIN=/min
        set testing_discord_bot=0
        if "%1" == "verify" .or. "%1" == "/v" .or. "%1" == "-v" goto :verification
        if "%1" == "test" .or. "%1" == "testing" .or. "%1" == "debug" .or. "%1" == "debugging" (set testing_discord_bot=1 %+ unset /q min)

rem Check if it’s running already:
        unset /q ASK_FOR_RERUN
        call bigecho "%STAR% %ANSI_COLOR_IMPORTANT%Checking if %italics_on%%ECHOABLE_NAME_OF_WHAT_WE_ARE_RUNNING%%italics_off% is already running..."
        :Recheck
        set  isRunning=0
        call isRunning %PROCESS_REGEX_OF_WHAT_WE_ARE_RUNNING% quiet >NUL
        iff "%isRunning%" == "1" then
                unset /q PID
                set PID=%@EXECSTR[0,tasklist /l |:u8grep -i "%PROCESS_REGEX_OF_WHAT_WE_ARE_RUNNING%"|:u8grep -v grep|:u8sed -e "s/^ *//ig" -e "s/ .*$//ig" -e "s/[^0-9]//ig"]
                %color_removal%
                rem call debug "%ECHOABLE_NAME_OF_WHAT_WE_ARE_RUNNING% is already running. Killing and restarting. %faint_on%PID='%italics_on%%PID%%italics_off%'%faint_off%"
                iff defined PID then
                        unset /q ANSWER
                        call AskYN "Already running [pid#%italics_on%%blink_on%%pid%%blink_off%%italics_off%]! Terminate" yes 30 
                        iff "Y" == "%ANSWER%" then
                                call bigecho %STAR% %ANSI_COLOR_REMOVAL%Terminating previous instance%ANSI_COLOR_IMPORTANT% of %italics_on%%ECHOABLE_NAME_OF_WHAT_WE_ARE_RUNNING%%italics_off%, pid %emphasis%%PID%%deemphasis%...
                                set ASK_FOR_RERUN=1
                                taskend /f %PID%
                        else
                                echo %no% Nevermind, then...
                                goto /i END
                        endiff
                else
                        call warning "could not find pid"
                        goto /i break_recheck
                endiff
                goto /i Recheck
        endiff
        :break_recheck

rem Ask to re-run it, if and only if we terminated an existing instance(s):
        iff "1" == "%ASK_FOR_RERUN%" then
                unset /q ANSWER
                call AskYN "Re-run %ECHOABLE_NAME_OF_WHAT_WE_ARE_RUNNING%" yes 30 
                iff "Y" != "%ANSWER%" then
                        echo %NO% Okay then...
                        goto /i END
                endiff
        endiff

rem Start it up if it’s not yet running:
        call bigecho "%STAR% %ANSI_COLOR_IMPORTANT%Starting %italics_on%%ECHOABLE_NAME_OF_WHAT_WE_ARE_RUNNING%%italics_off%..."
                rem                         *start "%PROCESS_WINDOW_TITLE_OF_WHAT_WE_ARE_RUNNING%" /MIN c:\bat\calendar-monitor-helper.bat %*
                rem                         *start "%PROCESS_WINDOW_TITLE_OF_WHAT_WE_ARE_RUNNING%" /MIN python c:\bat\ingest_ics.py %*
                set last_start_command_used=*start "%PROCESS_WINDOW_TITLE_OF_WHAT_WE_ARE_RUNNING%" %MIN% %INVOCATION_OF_SCRIPT_WE_ARE_RUNNING% %*
                echo %ansi_color_debug%- DEBUG: start command will be: %italics_on%%last_start_command_used%%italics_off%%ansi_color_normal%
                %last_start_command_used
                call wait %SLEEP_TIME_AFTER_RUNNING_BEFORE_IT_HAS_STARTED% wipe

rem Minimize after it starts:
        rem call bigecho  "%STAR% %ANSI_COLOR_IMPORTANT%Minimizing %italics_on%%ECHOABLE_NAME_OF_WHAT_WE_ARE_RUNNING%%italics_off% to %italics_on%tray%italics_off%..."
        rem call minimize "*PROCESS_WINDOW_TITLE_OF_WHAT_WE_ARE_RUNNING*"

rem Confirmation:
        :verification        
        unset /q running_verification
        set      running_verification=%@EXECSTR[tasklist /o /l |:u8 grep -i "%PROCESS_REGEX_OF_WHAT_WE_ARE_RUNNING%"]
        echos %ansi_color_success%       %star2% %underline_on%Running%underline_off%:          %@colorful[%running_verification%]

rem Offer any additional advice here:
        rem call bigecho "%STAR% %ANSI_COLOR_ADVICE%Drop ICS files into:"
        rem call bigecho    "    %ANSI_COLOR_ADVICE%    %italics_on%%faint_on%c:\Calendar\%faint_off%%italics_off% or %italics_on%%faint_on%c:\Cal\%faint_off%%italics_off%..."

:END


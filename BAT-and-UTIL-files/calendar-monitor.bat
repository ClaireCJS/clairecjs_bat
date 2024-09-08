@Echo OFF
rem cls

set MONITORING_SCRIPT=%BAT%\ingest_ics.py
set PROCESS_REGEX=python.*ingest_ics
set PROCESS_WINDOW_TITLE=Calendar Monitor


call validate-environment-variable MONITORING_SCRIPT PROCESS_REGEX
call validate-in-path              helper-start calendar-monitor-helper python isRunning tasklist grep sed

call bigecho %STAR% %ANSI_COLOR_IMPORTANT%Checking if %italics_on%Calendar Monitor%italics_off% is already running...
        :Recheck
        set  isRunning=0
        call isRunning %PROCESS_REGEX% quiet >NUL
        if  %isRunning eq 1 (
            unset /q PID
            set PID=%@EXECSTR[0,tasklist /l |grep -i ingest_ics|grep -v grep|sed -e "s/^ *//ig" -e "s/ .*$//ig" -e "s/[^0-9]//ig"]
            %color_removal%
            rem call debug "Calendar Monitor is already running. Killing and restarting. %faint_on%PID='%italics_on%%PID%%italics_off%'%faint_off%"
            if defined PID (
                call bigecho %STAR% %ANSI_COLOR_IMPORTANT%Terminating previous instance of %italics_on%Calendar Monitor%italics_off%, pid %emphasis%%PID%%deemphasis%...
                taskend /f %PID%
            )
            if not defined PID (
                call warning "could not find pid"
                goto :break_recheck
            )
            goto :Recheck
        )
        :break_recheck

call bigecho %STAR% %ANSI_COLOR_IMPORTANT%Starting %italics_on%Calendar Monitor%italics_off%...
call helper-start /INV calendar-monitor-helper %*

call sleep 2
call bigecho %STAR% %ANSI_COLOR_IMPORTANT%Minimizing %italics_on%Calendar Monitor%italics_off% to %italics_on%tray%italics_off%...
activate "Calendar Monitor*" tray

call bigecho "%STAR% %ANSI_COLOR_ADVICE%Drop ICS files into:"
call bigecho    "    %ANSI_COLOR_ADVICE%    %italics_on%%faint_on%c:\Calendar\%faint_off%%italics_off% or %italics_on%%faint_on%c:\Cal\%faint_off%%italics_off%..."

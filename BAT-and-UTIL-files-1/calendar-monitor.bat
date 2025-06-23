@Echo OFF
 on break cancel
rem cls


rem Configuration:
        set MONITORING_SCRIPT=%bat%\ingest_ics.py
        set PROCESS_REGEX=python.*ingest_ics
        set PROCESS_WINDOW_TITLE=Calendar Monitor


rem Validate environment:
        call validate-environment-variable MONITORING_SCRIPT PROCESS_REGEX
        call validate-in-path              helper-start calendar-monitor-helper python isRunning tasklist grep sed minimize


rem Kill it if it’s already running:
        call bigecho %STAR% %ANSI_COLOR_IMPORTANT%Checking if %italics_on%Calendar Monitor%italics_off% is already running...
        :Recheck
        set  isRunning=0
        call isRunning %PROCESS_REGEX% quiet >NUL
        if  %isRunning eq 1 (
            unset /q PID
            set PID=%@EXECSTR[0,tasklist /l |:u8grep -i ingest_ics|:u8grep -v grep|:u8sed -e "s/^ *//ig" -e "s/ .*$//ig" -e "s/[^0-9]//ig"]
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



rem Sometimes we save .cal files in c:\ because we don’t feel like opening them JUST yet. 
rem Let’s not forget about those!
        if exist c:\*.ics mv c:\*.ics c:\calendar\


rem Start it up:
        call bigecho %STAR% %ANSI_COLOR_IMPORTANT%Starting %italics_on%Calendar Monitor%italics_off%...

        rem *start "Calendar Monitor" /MIN c:\bat\calendar-monitor-helper.bat %*
            *start "Calendar Monitor" /MIN python c:\bat\ingest_ics.py %*



rem Deprecated code to minimize it:
        call sleep 2
        call bigecho %STAR% %ANSI_COLOR_IMPORTANT%Minimizing %italics_on%Calendar Monitor%italics_off% to %italics_on%tray%italics_off%...
        rem call minimize /hide  "Calendar Monitor"
        rem activate "Calendar Monitor*" tray
        rem call minimize /hide "*ingest_ics.py*
        rem window activate
        rem  rem call minimize "*ingest_ics*"
        activate "*ingest_ics*" tray


rem Some advice:
        call bigecho "%STAR% %ANSI_COLOR_ADVICE%Drop ICS files into:"
        call bigecho    "    %ANSI_COLOR_ADVICE%    %italics_on%%faint_on%c:\Calendar\%faint_off%%italics_off% or %italics_on%%faint_on%c:\Cal\%faint_off%%italics_off%..."

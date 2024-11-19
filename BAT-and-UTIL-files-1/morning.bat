@Echo Off
@on break cancel

rem call validate-in-path restore-window-positions asleep deal-with-finished-torrents hi-morning hi-afternoon

::::: Run work-specific one if we are on a work-specific machine:
	if %@UPPER["%machinename%"] eq "WORK" c:\bat\work\morning.bat


::::: COMMON PRE-HI: Restore saved window positions:
    call restore-window-positions.bat

::::: Make sure we are still set in asleep mode, in case one of us got up early:
    call asleep

::::: Run different 'hi' commands based on the time of the day:
    if %_hour ge  4 .and. %_hour lt 12 (call hi-morning  )
    if %_hour ge 12 .and. %_hour le 23 (call hi-afternoon)


::::: COMMON POST-HI: Push incoming files one step further in our workflows:
    call deal-with-finished-torrents

rem we stoppedu sing Karen's replicator after Karen died and development stopped and we rolled our own backup script:  s::::: Kill Karen's Replicator, which is run during bedtime: call killifrunning PTREPL~1 PTREPL~1


::::: SET AWAKE:
    call awake
    %COLOR_ADVICE% %+ echo *** If someone is still asleep, run "asleep" again! %+ %COLOR_NORMAL%
    %COLOR_ADVICE% %+ echo *** If no  one is still asleep, run "b1 on"!        %+ %COLOR_NORMAL%

call fix-window-title

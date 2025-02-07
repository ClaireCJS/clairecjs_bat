@loadBTM on
@Echo OFF
@call bat-init

rem Validate environment (once):
        iff "1" != "%validated_revtragalyr%" then
                call validate-environment-variable FILEMASK_AUDIO italics_on italics_off blink_on blink_off
                call validate-in-path              warning_soft  divider  AskYN  print-message
                set  validated_revtragalyr=1
        endiff

rem Check initial conditions:
        if not defined FILEMASK_SUBTITLE set FILEMASK_SUBTITLE=*.lrc;*.srt
        iff not exist %FILEMASK_AUDIO% then
                call warning_soft "No audio files present"
                goto :end
        endiff
        iff not exist %FILEMASK_SUBTITLE% then
                call warning_soft "No subtitle files present"
                goto :end
        endiff


rem Decide which file(s) to do it to:
        set filemask_to_use=%FILEMASK_AUDIO%
        if exist %1 set filemask_to_use=%1

rem Count how many times we’ll be doing it:
        set NUMBER_TO_COMPARE=0
        for %%tmpfile in (%filemask_to_use%) do gosub :do_it "%@UNQUOTE["%tmpfile%"]" count
        set NUMBER_REMAINING=%NUMBER_TO_COMPARE%

rem Then actually do it:
        for %%tmpfile in (%filemask_to_use%) do gosub :do_it "%@UNQUOTE["%tmpfile%"]"



goto :end
    :━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    :━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 
        :do_it [opt1 count]
                rem Get audio filename:
                        set                   aud=%@UNQUOTE["%opt1%"]
                        set      base=%@NAME[%aud%]
                        set       ext=%@EXT[ %aud%]

                rem Stop if it’s not actuall an audio file:
                        if 0 eq %@RegEx[%ext%,%FILEMASK_AUDIO%] return

                rem Get sidecar filenames:
                        set txt=%base%.txt
                        set lrc=%base%.lrc
                        set srt=%base%.srt
                        echo %@randfg[]%staru%%ansi_color_normal% Checking “%aud%”...
                        rem debug echo base=%base%  srt=%srt%  lrc=‘%lrc%’

                rem Check for do-nothing conditions: having no subtitles:
                        iff not exist "%srt%" .and. not exist "%lrc%" then
                                echo %tab%%@randfg[]%staru%%ansi_color_normal% No subtitles...
                                return
                        endiff

                rem Check for do-nothing conditions: having no text lyrics:
                        iff not exist "%txt%" then
                                echo %tab%%@randfg[]%staru%%ansi_color_normal% No txt lyrics...
                                return
                        endiff

                rem At this point we definitely have subtitles!

                rem Count-only pre-run mode:
                        iff "%count%" == "count" then
                                set NUMBER_TO_COMPARE=%@EVAL[%NUMBER_TO_COMPARE+1]
                                return
                        endiff

                rem Cosmetics:
                        repeat %@EVAL[%_ROWS-5] echo.
                        call divider

                rem Head it with the audio file:
                        call bigecho %emphasis%%STAR% %aud% %STAR%%deemphasis%

                rem Then show the TXT file we used to generate our prompt:
                        if exist "%txt%" call review-file -wh "%txt%" 

                rem Then show the karaoke (“wordy-scrolly”) that we generated:
                        if exist "%srt%" call review-file -wh "%srt%" 
                        if exist "%lrc%" call review-file -wh "%lrc%" 
                        call divider
                                
                rem Pause if there are multiple files:
                        iff %NUMBER_TO_COMPARE% gt 1 then
                                set NUMBER_REMAINING=%@EVAL[%NUMBER_REMAINING% - 1]
                                pause "%blink_on%%italics_on%%NUMBER_REMAINING%%italics_off%%blink_off% remaining to compare..."
                        endiff
        return
    :━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    :━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

:end

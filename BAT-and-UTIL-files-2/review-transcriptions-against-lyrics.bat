@loadBTM on
@Echo OFF
@call bat-init



rem Validate:
        call validate-environment-variable FILEMASK_AUDIO
        call validate-in-path              warning_soft  divider


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


rem Now do it!
        for %%tmpfile in (%FILEMASK_AUDIO%) do gosub :do_it "%@UNQUOTE["%tmpfile%"]"


goto :end
    :━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    :━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 
        :do_it [opt1]
                rem Deal with filenames:
                        set                   aud=%@UNQUOTE["%opt1%"]
                        set      base=%@NAME[%aud%]
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

                rem At this point we have subtitles, so let’s review them...
                        if exist "%txt%" call review-file "%txt%"
                        if exist "%srt%" call review-file "%srt%"
                        if exist "%lrc%" call review-file "%lrc%"
                        call divider

        return


    :━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    :━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
:end


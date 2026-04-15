@loadbtm on
@Echo OFF
@on break cancel

:DESCRIPTION: To review SRT files along with adjacent LRC & TXT files, to see if any do not match and any need to be deleted. Deleted ones are regenerated from the SRT.


rem                         review-SRTs          is: @call review-files -wh -st *.srt;*.lrc
rem      so you would think review-SRTs-and-TXTs is: @call review-files -wh -st *.srt;*.lrc;*.txt

rem     But in order to do them one song per time, we actually need to:
rem                     1) go through all the SRT files 
rem                     2) see if there are TXT/LRC sidecars
rem                     3) send JUST the 3 of them to review-files
rem                     4) with an option to delete TXT/LRC/SIDECAR



rem Validate environment (once):
        iff "1" != "%validated_review_transcriptions%" then
                if not defined emoji_have_been_set     validate-environment-variable emoji_have_been_set 
                if not defined ansi_color_has_been_set validate-environment-variable ansi_color_has_been_set 
                call validate-in-path clean-up-AI-transcription-trash-files-here.bat review-files review-file AskYN unapprove-subtitles unapprove-lyrics approve-subtitles approve-lyrics srt2txt srt2lrc error print-message
                set  validated_review_transcriptions=1                                                                      
        endiff


rem Process parameters:
        iff "%1" == "all" then
                set REVIEW_ALL_SRT_FILES=1
                shift
        else
                set REVIEW_ALL_SRT_FILES=0
        endiff


rem First, clean up any trash files, so we don’t have to waste time looking at pointless trash:
        call clean-up-AI-transcription-trash-files-here.bat 


rem Go through each subtitle file to look for our comparison files...
echo.
do tmp_file in *.srt
        gosub process_file "%@UNQUOTE[%tmp_file%]"
enddo



goto :END

        :process_file [tmp_file]
                rem Generate comparison (sidecar) filenames:
                        set srt=%@UNQUOTE[%tmp_file%]
                        set lrc=%@name["%srt%"].lrc
                        set txt=%@name["%srt%"].txt

                rem If there’s nothing to compare this SRT to, skip this one...
                        iff not exist "%lrc%" .and. not exist "%txt%" .and. "1" != "%REVIEW_ALL_SRT_FILES%" then
                                echo %ansi_color_important%* Skipping: %italics_on%%SRT%%italics_off% %faint_on%(no TXT/LRC sidecars)%faint_off%%ansi_color_normal%
                                echo %ansi_color_advice%            (add %lq%all%rq% parameter to process these files as well)%ansi_color_normal%
                                repeat 4 echo.
                                return
                        endiff

                rem If there IS something to compare it to, we actually want to show in the order of 
                rem TXT ➜ LRC ➜ SRT to match what we’re used to with the AI-transcription system:
                        gosub  divider
                        if     exist %TXT%                   call review-files -wh -stL "%TXT%" %+ rem Start with TXT and it’s representation stripe at the bottom
                        if     exist %TXT% .and. exist %LRC% call review-files -wh -stB "%LRC%" %+ rem If    TXT and LRC, then LRC will be representation-striped on both sides
                        if not exist %TXT% .and. exist %LRC% call review-files -wh -stL "%LRC%" %+ rem If no TXT and LRC, then LRC will be representation-striped on the bottom — no need for top because no TXT to compare stripes to
                        if     exist %SRT%                   call review-files -wh -stU "%SRT%" %+ rem SRT will be representation-striped at the top
                        gosub  divider

                rem Ask if user wants to delete any of them?
                        :re_ask
                        call AskYN "Delete any? [%ansi_color_bright_green%N%ansi_color_prompt%o/Next, del %ansi_color_bright_green%t%ansi_color_prompt%xt,del %ansi_color_bright_green%s%ansi_color_prompt%ubs,del %ansi_color_bright_green%L%ansi_color_prompt%RC,approve sub(%ansi_color_bright_green%A%ansi_color_prompt%)/lyr(%ansi_color_bright_green%B%ansi_color_prompt%)/%ansi_color_bright_green%C%ansi_color_prompt%=%italics_on%both%italics_off%,unapprove sub(%ansi_color_bright_green%U%ansi_color_prompt%)/lyr(%ansi_color_bright_green%V%ansi_color_prompt%)/%ansi_color_bright_green%W%ansi_color_prompt%=%italics_on%both%italics_off%]" No 0 YNABCUVWTSL Y:Yeah,N:No!,A:approve_karaoke,B:approve_lyrics,C:approve_all U:unapprove_karaoke,V:unapprove_lyrics,W:unapprove_all,T:delete_TXT_lyrics,S:delete_subtitles,L:delete_LRC

                        if "N" == "%ANSWER%" goto :done_with_this_one
                        if "T" == "%ANSWER%" (gosub delete_file "%TXT%" %+ goto /i :re_ask)
                        if "S" == "%ANSWER%" (gosub delete_file "%SRT%" %+ call srt2txt "%SRT%" %+ goto /i :re_ask)
                        if "L" == "%ANSWER%" (gosub delete_file "%LRC%" %+ call srt2lrc  >nul   %+ goto /i :re_ask)
                        if "A" == "%ANSWER%" (if exist "%SRT%" call   approve-subtitles "%SRT%" %+ goto /i :re_ask)
                        if "B" == "%ANSWER%" (if exist "%TXT%" call   approve-lyrics    "%TXT%" %+ goto /i :re_ask)
                        if "U" == "%ANSWER%" (if exist "%SRT%" call unapprove-subtitles "%SRT%" %+ goto /i :re_ask)
                        if "V" == "%ANSWER%" (if exist "%TXT%" call unapprove-lyrics    "%TXT%" %+ goto /i :re_ask)
                        if "C" == "%ANSWER%" (if exist "%TXT%" call   approve-lyrics    "%TXT%" %+ if exist "%SRT%" call   approve-subtitles "%SRT%" %+ goto /i :re_ask)
                        if "W" == "%ANSWER%" (if exist "%TXT%" call unapprove-lyrics    "%TXT%" %+ if exist "%SRT%" call unapprove-subtitles "%SRT%" %+ goto /i :re_ask)
                        
                        iff "Y" == "%ANSWER%" then
                                if exist "%TXT%" call AskYN "delete the TXT lyrics" no 0 %+ if exist "%TXT%" if "Y" == "%ANSWER%" gosub delete_file "%TXT%"
                                if exist "%LRC%" call AskYN "delete the LRC subs"   no 0 %+ if exist "%LRC%" if "Y" == "%ANSWER%" gosub delete_file "%LRC%"
                                if exist "%SRT%" call AskYN "delete the SRT subs"   no 0 %+ if exist "%SRT%" if "Y" == "%ANSWER%" gosub delete_file "%SRT%"
                        endiff

                rem Close out this file:
                        :done_with_this_one
                        gosub divider
                        gosub divider
                        repeat 4 echo.
        return

        :delete_file [fil]
                :delete_it
                *del /q /Ns %fil% >&>nul
                echos %ansi_color_normal%
                iff exist %fil% then
                        call error "uh oh! file still exists!: %@UNQUOTE[%fil%]"
                        call askyn "Try deleting again" yes 0
                        if "Y" == "%ANSWER%" goto /i :delete_it
                else
                echo %ansi_color_warning_soft%%EMOJI_AXE% %underline_on%Deleted%underline_off%: %fil% %EMOJI_GHOST%%ansi_color_normal%
                endiff
        return

        :divider [divider_param]
                iff "1" == "%suppress_next_divider%" then
                        set  suppress_next_divider=0
                        return
                endiff

                rem Determine divider file to use:
                        set wd=%@EVAL[%_columns - 1]
                        set nm=%bat%\dividers\rainbow-%wd%.txt

                rem Type divider file if it exists:
                        iff exist %nm% then
                                *type %nm%
                                rem set last_divider_method=type
                                rem set last_divider_param=%divider_param%
                rem Otherwise, manually draw the divider:
                        else
                                echo %@char[27][93m%@REPEAT[%@CHAR[9552],%wd%]%@char[27][0m
                                rem set last_divider_method=echo
                        endiff

                rem Our divider files do not include newlines. Do we add one ourself?
                        rem debug: *pause>nul
                        iff "%divider_param%" == "NoNewline"  then
                                set last_divider_newline=False
                        else 
                                set last_divider_newline=True

                                rem Go to the next line:           
                                        rem echos %NEWLINE%
                                        echo.

                                rem Then move to column 0/1 [which are the same column]:
                                        echos %@ANSI_MOVE_TO_COL[0] 

                        endiff

                rem Debug: echo wtf last_divider_newline=%last_divider_newline% should we do one? >nul
        return

:END


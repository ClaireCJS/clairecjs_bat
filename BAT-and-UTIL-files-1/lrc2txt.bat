@loadbtm on
@Echo OFF
 on break cancel


rem Validate environment (once):
        if not defined FILEEXT_AUDIO set FILEEXT_AUDIO=mp3   wav   rm   voc   au   mid   stm   mod   vqf   ogg   mpc   wma   mp4   flac   snd   aac   opus   ac3
        if not defined BAT and isdir c:\bat set BAT=c:\bat
        iff 1 ne %validated_lrc2txt_env% then
                call validate-environment-variables FILEEXT_AUDIO EMOJIS_HAVE_BEEN_SET ANSI_COLORS_HAVE_BEEN_SET
                call validate-in-path               errorlevel.bat lrc2txt.py review-files.bat approve-lyrics.bat python approve-lyriclessness.bat 
                set  validated_lrc2txt_env=1
        endiff

rem Usage:
        iff "%1" == "" then
                repeat 2 echo. %+ echo USAGE: lrc2txt whatever.lrc [silent]      %zzzzzz%   ━━   generates whatever.txt, if “silent” is 2nd option, then does so without post-review
                repeat 2 echo. %+ echo USAGE: lrc2txt -t                         %zzzzzz%   ━━   run testing suite (which is just about quote conversion right now)  
                repeat 2 echo. %+ echo USAGE: lrc2txt -a `|` -all `|` all `|` * `|` *.lrc   ━━   process all LRC files in the current directory
                echo.
                goto :END
        endiff

rem Parameter fetch:
        set OPTION=%@UNQUOTE["%@LOWER["%1"]"]
        set PROCESS_ALL=0
        iff "%OPTION%" == "-a"  .or. "%OPTION%" == "-all" .or. "%OPTION%" == "all"  .or. "%OPTION%" == "*"  .or. "%OPTION%" == "*.lrc" then            %+ rem Check for the “all” option
                set PROCESS_ALL=1
        else
                set LRC_file=%@UNQUOTE["%1"]
                set output_file=%@UNQUOTE["%@NAME["%lrc_file%"]``"``].txt
        endiff


rem Parameter validate:
        iff 0 eq %PROCESS_ALL% then 

                rem Validate input file:
                        call validate-environment-variable   LRC_file 
                        call validate-is-extension         "%LRC_file%"  *.lrc

                rem Prevent output file collision:
                        rem if exist "%output_file%" (call less_important "TXT file already exists: “%italics_on%%output_file%italics_off%”" %+ goto :END)
                        if exist "%Output_file%" (call deprecate "%output_file%" >nul lr>&>nul)

        endiff
        unset /q FILE_OR_FILES_TO_REVIEW
        

rem Cosmetics:
        if "%2" != "silent" gosub divider
        

rem Perform the actual conversion:        
        rem lrc2txt.py "%LRC_file%"
        iff 1 eq %PROCESS_ALL% then
                for %%Ffff in (*.lrc) do (
                        rem echo Processing: "%Ffff"
                        lrc2txt.py           "%Ffff"
                        call ErrorLevel
                        set  expected_output_file=%@UNQUOTE["%@NAME["%FFFF"]"].txt
                        echo expected_output_file="%expected_output_file%">nul
                        set FILE_OR_FILES_TO_REVIEW=%FILE_OR_FILES_TO_REVIEW% "%expected_output_file%"
                )
        else
                set  FILE_OR_FILES_TO_REVIEW="%OUTPUT_FILE%"
                lrc2txt.py "%LRC_file%"
                call ErrorLevel
                iff %@filesize["%@unquote["%output_file%"]"] eq 0 then
                        *del /q "%OUTPUT_FILE%" >nul
                        echo %ansi_color_warning%%emoji_warning Zero-byte file generated! %emoji_warning%%ansi_reset% 
                        echo %ansi_color_less_important%%star% Reviewing the source LRC...%ansi_reset% 
                        call review-file "%LRC_FILE%"
                        call AskYN "Delete the LRC file" no 90
                        if "Y" == "%ANSWER" (*del /q "%LRC_FILE%" >nul)
                        call AskYN "Mark corresponding audio as lyric%underline_on%less%underline_off%? [I=instrumental]" yes 8 I I:mark_as_instrumental_instead
                                set lrc2txtmark_answer=%answer%
                                gosub "%BAT%\get-lyrics-for-file.btm" rename_audio_file_as_instr_if_answer_was_I
                                if  "I" == "%lrc2txtmark_answer%" goto :END

                        for %%tmpMask in (%fileext_audio%) do (
                                set proposed_audio_file=%@unquote["%@name["%lrc_file%"]"].%tmpMask
                                set rem=echo Checking[dd] if exist "%proposed_audio_file%"
                                if exist "%proposed_audio_file%" (
                                        rem echo %check% Approving lyriclessness for "%proposed_audio_file%"
                                        rem call approve-lyriclessness "%proposed_audio_file%"
                                        gosub "%BAT%\get-lyrics-for-file.btm" mark_as_lyricless "%proposed_audio_file%"
                                ) else (
                                        set rem=echo       ...It does not.
                                )
                        )
                        goto :END
                endiff
                call validate-environment-variable FILE_OR_FILES_TO_REVIEW
        endiff


rem Review output:
        iff "%2" != "silent" then
                set first_file=1
                for %%tmp_review_file in (%file_or_files_to_review%) do (
                        set idea=maybe ask to hand-edit
                        if 1 eq %first_file% (
                                set first_file=2
                        ) else (
                                echo Major confusion when running %0
                                repeat 5 pause
                        )

                        call review-files  "%@UNQUOTE["%tmp_review_file%"]"                        
                        if "%Approve_Generated_Lyrics_CTLFKF%" != "False" (call approve-lyrics "%@UNQUOTE["%tmp_review_file%"]")
                )
        endiff

:END


goto :skip_subroutines
        :divider []
                rem Use my pre-rendered rainbow dividers, or if they don’t exist, just generate a divider dynamically
                set wd=%@EVAL[%_columns - 1]
                set nm=%bat%\dividers\rainbow-%wd%.txt
                iff exist %nm% then
                        *type %nm%
                        if "%1" ne "NoNewline" .and. "%2" ne "NoNewline" .and. "%3" ne "NoNewline" .and. "%4" ne "NoNewline" .and. "%5" ne "NoNewline"  .and. "%6" ne "NoNewline" (echos %NEWLINE%%@ANSI_MOVE_TO_COL[1])
                else
                        echo %@char[27][93m%@REPEAT[%@CHAR[9552],%wd%]%@char[27][0m
                endiff
        return
:skip_subroutines

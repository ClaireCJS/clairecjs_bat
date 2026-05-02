@loadbtm on
@on break cancel
@Echo off

rem Validate environment (once):
        iff "2" != "%validated_displaymp3length%" then
                if not defined FILEMASK_AUDIO   call validate-environment-variable FILEMASK_AUDIO
                call validate-in-path validate-file-extension display-mp3-tags grep sed set-tmp-file subtitle_length.py
                call validate-function strip_ansi %+ rem we must use stripansi, strip_ansi is just a placeholder/semaphore
                call validate-environment-variables emoji_have_been_set ansi_colors_have_been_set
                set  validated_displaymp3length=2
        endiff


rem Usage:
        iff "%1" == "" .or. "%1" == "--help" .or. "%1" == "-help" .or. "%1" == "-h" .or. "%1" == "-?" .or. "%1" == "/?" then
                echo.
                echos %ansi_color_advice%
                echo ✨ USAGE: %0 {audio filename or LRC file} [silent`|`verbose]
                echo.
                echo. EXAMPLE 1: display-audio-file-length.bat whatever.mp3         — mode 1/default mode: displays one-line blurb showing length
                echo. EXAMPLE 2: display-audio-file-length.bat whatever.mp3  silent — mode 2/silent  mode: only sets return value variables
                echo. EXAMPLE 3: display-audio-file-length.bat whatever.mp3 verbose — mode 3/testing mode: outputs all return values so you can pick the one you like
                echo. EXAMPLE 4: display-audio-file-length.bat subtitles.lrc        — mode 1/default mode: displays one-line blurb showing approximate length of LRC subtitle file
                echo. EXAMPLE 5: display-audio-file-length.bat subtitles.srt        — mode 1/default mode: displays one-line blurb showing approximate length of SRT subtitle file

                echos %ansi_color_important%
                echo.
                echo %star% OUTPUT FORMATS: %tar%
                echo.
                echos %ansi_color_important_less%
                set reader_output=666
                set verbose_dafl=1
                goto /i compute_alternate_return_values

                echos %ansi_color_normal%

                goto :END
        else
                set verbose_dafl=0
        endiff
        if "%2" == "verbose" set verbose_dafl=1


rem Validate parameters:
        set DAFL_FILE=%@UNQUOTE[%1]
        set PRETTY_DAFL_FILE=%@UNQUOTE[%DAFL_FILE%] 
        if not exist "%DAFL_FILE%" call validate-environment-variable DAFL_FILE "Must pass an audio or LRC/SRT file as 1ˢᵗ parameter"

rem Get extension of input file, and strip off ".maybe" post-extension if it exists:
        set EXT=%@EXT["%DAFL_FILE%"]
        if "%EXT%" == "maybe" set EXT=%@EXT[%@NAME["%DAFL_FILE%"]]

rem Validate extension of input file:
        if "%EXT%" != "mp3" .and. "%EXT%" != "flac" .and. "%EXT%" != "lrc" .and. "%EXT%" != "srt" call validate-file-extension  "%DAFL_FILE%" %FILEMASK_AUDIO%



rem Cosmetics:
        echos %@CURSOR_COLOR[indigo]%ANSI_COLOR_RUN%%EMOJI_GEAR% Reading length of: %faint_on%%italics_on%%@NAME["%DAFL_FILE%"]%italics_off%...%faint_off%%@ANSI_MOVE_TO_COL[0]


rem History:
        rem set DISPLAYMP3LENGTH_OUTPUT=%@EXECSTR[call display-mp3-tags %DAFL_FILE% |:u8 grep -i length |:u8 sed -e "s/ 00:/ /" -e "s/ 0/  /" -e "s/ *:/:/" -e "s/^ *//ig" -e "s/:/:%ANSI_COLOR_IMPORTANT%%ITALICS_ON%/" ]
        rem set NEWPUT=%@EXECSTR[grep -i length %tmpfile1% |:u8 sed -e "s/ 00:/ /" -e "s/ 0/  /" -e "s/ *:/:/" -e "s/^ *//ig" -e "s/:/:%ANSI_COLOR_IMPORTANT%%ITALICS_ON%/" ]



rem Create tmp file:
        if not defined tmpfile1 call set-tmp-file "display-audio-file-length"




rem Read file length: set Default values in case the read fails:
        set DISPLAY_AUDIO_FILE_LENGTH_SECONDS_FLOAT=-1
        set DISPLAY_AUDIO_FILE_LENGTH_MINUTES_FLOAT=-1
        set DISPLAY_AUDIO_FILE_LENGTH_HOURS_FLOAT=-1
        unset /q READER_OUTPUT DISPLAY_AUDIO_FILE_LENGTH_OUTPUT


rem Read non-audio file length: do the actual read:
        iff "%EXT%" == "lrc" .or. "%EXT%" == "srt" then                
                set READER_OUTPUT=%@execstr[subtitle_length.py "%DAFL_FILE%"]
rem Read audio file length: do the actual read:
        else
                rem old way, 2.05sec: set READER_OUTPUT=%@EXECSTR[call display-mp3-tags "%DAFL_FILE%" |& grep -i Length |& sed -e "s/^ *Length *: [0:]*//i"]
                rem new way: 0.05sec:
                        set READER_OUTPUT=%@EXECSTR[ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "%DAFL_FILE%"]
                rem Set base time value: Floating point i.e.  1.97528 hours, 118.51667 minutes, 7111.569000 second:
        endiff

rem ffprobe faliure value but we could use this failure value for non-ffprobe situations too if we were so inclined:
        if "N/A" == "%READER_OUTPUT%" goto /i :ffmpeg_fail

rem Saving the results:
        rem call debug "READER_OUTPUT is “%READER_OUTPUT%”"
        :compute_alternate_return_values
        unset /q display_audio_file*
        set DISPLAY_AUDIO_FILE_LENGTH_OUTPUT=%READER_OUTPUT%

rem Compute various values: calculate derived values:
        rem Original minutes/hours calculated from seconds:
                set DISPLAY_AUDIO_FILE_LENGTH_SECONDS_FLOAT=%DISPLAY_AUDIO_FILE_LENGTH_OUTPUT%
                set DISPLAY_AUDIO_FILE_LENGTH_MINUTES_FLOAT=%@FORMATn[.2,%@EVAL[%@FLOOR[%DISPLAY_AUDIO_FILE_LENGTH_OUTPUT+.05]/60]]
                set DISPLAY_AUDIO_FILE_LENGTH_HOURS_FLOAT=%@FORMATn[.2,%@EVAL[%@FLOOR[%DISPLAY_AUDIO_FILE_LENGTH_OUTPUT+.05]/60/60]]
        rem truncated integar values i.e.  1 hours, 118 minutes, 7111 second:
                :ffmpeg_fail
                set DISPLAY_AUDIO_FILE_LENGTH_MINUTES_INT=%@FLOOR[%DISPLAY_AUDIO_FILE_LENGTH_MINUTES_FLOAT%]
                set DISPLAY_AUDIO_FILE_LENGTH_SECONDS_INT=%@FLOOR[%DISPLAY_AUDIO_FILE_LENGTH_SECONDs_FLOAT%]
                set DISPLAY_AUDIO_FILE_LENGTH_HOURS_INT=%@FLOOR[%DISPLAY_AUDIO_FILE_LENGTH_HOURS_FLOAT%]
        rem rounded integer individual values i.e.  2 hours, 119 minutes, 7112 second:
                set DISPLAY_AUDIO_FILE_LENGTH_MINUTES_ROUND=%@FLOOR[%@eval[%DISPLAY_AUDIO_FILE_LENGTH_MINUTES_FLOAT%+.5]]
                set DISPLAY_AUDIO_FILE_LENGTH_SECONDS_ROUND=%@FLOOR[%@eval[%DISPLAY_AUDIO_FILE_LENGTH_SECONDS_FLOAT%+.5]]
                set DISPLAY_AUDIO_FILE_LENGTH_HOURS_ROUND=%@FLOOR[%@eval[%DISPLAY_AUDIO_FILE_LENGTH_HOURS_FLOAT%+.5]]
        rem modded floating point values i.e. 1 hour, 58 minutes, 57 seconds:
                set DISPLAY_AUDIO_FILE_LENGTH_MINUTES_float_MOD60=%@EVAL[%@FLOOR[%@eval[%DISPLAY_AUDIO_FILE_LENGTH_MINUTES_FLOAT%]] mod 60]
                set DISPLAY_AUDIO_FILE_LENGTH_SECONDS_float_MOD60=%@EVAL[%@FLOOR[%@eval[%DISPLAY_AUDIO_FILE_LENGTH_SECONDS_FLOAT%]] mod 60]
                set DISPLAY_AUDIO_FILE_LENGTH_HOURS_float_MOD12=%@EVAL[%@FLOOR[%@eval[%DISPLAY_AUDIO_FILE_LENGTH_HOURS_FLOAT%]] mod 12]
        rem modded founded point values i.e. 2 hour, 58 minutes, 57 seconds:
                set DISPLAY_AUDIO_FILE_LENGTH_MINUTES_ROUND_MOD60=%@EVAL[%@FLOOR[%@eval[%DISPLAY_AUDIO_FILE_LENGTH_MINUTES_ROUND%+.5]] mod 60]
                set DISPLAY_AUDIO_FILE_LENGTH_SECONDS_ROUND_MOD60=%@EVAL[%@FLOOR[%@eval[%DISPLAY_AUDIO_FILE_LENGTH_SECONDS_ROUND%+.5]] mod 60]
                set DISPLAY_AUDIO_FILE_LENGTH_HOURS_ROUND_MOD12=%@EVAL[%@FLOOR[%@eval[%DISPLAY_AUDIO_FILE_LENGTH_HOURS_FLOAT%+.5]] mod 12]


rem Format various values:
        set DISPLAY_AUDIO_FILE_LENGTH_readable1=%@IF[%DISPLAY_AUDIO_FILE_LENGTH_MINUTES_ROUND% gt 59,%DISPLAY_AUDIO_FILE_LENGTH_HOURS_float_MOD12%:]%@IF[%DISPLAY_AUDIO_FILE_LENGTH_SECONDS_float% gt 59,%DISPLAY_AUDIO_FILE_LENGTH_MINUTES_float_MOD60%:]%@formatn[02.0,%DISPLAY_AUDIO_FILE_LENGTH_SECONDS_float_MOD60%]
        set DISPLAY_AUDIO_FILE_LENGTH_HH_MM_SS=%DISPLAY_AUDIO_FILE_LENGTH_readable1%
        set DISPLAY_AUDIO_FILE_LENGTH_readable2=%@IF[%DISPLAY_AUDIO_FILE_LENGTH_MINUTES_ROUND% gt 59,%DISPLAY_AUDIO_FILE_LENGTH_HOURS_float_MOD12%h:]%@IF[%DISPLAY_AUDIO_FILE_LENGTH_SECONDS_float% gt 59,%DISPLAY_AUDIO_FILE_LENGTH_MINUTES_float_MOD60%m:]%DISPLAY_AUDIO_FILE_LENGTH_SECONDS_float_MOD60%s
        set DISPLAY_AUDIO_FILE_LENGTH_readable3=%@IF[%DISPLAY_AUDIO_FILE_LENGTH_MINUTES_ROUND% gt 59,%DISPLAY_AUDIO_FILE_LENGTH_HOURS_float_MOD12%h:]%@IF[%DISPLAY_AUDIO_FILE_LENGTH_SECONDS_float% gt 59,%DISPLAY_AUDIO_FILE_LENGTH_MINUTES_float_MOD60%m:]%@formatn[02.0,%DISPLAY_AUDIO_FILE_LENGTH_SECONDS_float_MOD60%]s
        set DISPLAY_AUDIO_FILE_LENGTH_readable4=%@IF[%DISPLAY_AUDIO_FILE_LENGTH_MINUTES_ROUND% gt 59,%DISPLAY_AUDIO_FILE_LENGTH_HOURS_float_MOD12%h]%@IF[%DISPLAY_AUDIO_FILE_LENGTH_SECONDS_float% gt 59,%DISPLAY_AUDIO_FILE_LENGTH_MINUTES_float_MOD60%m]%DISPLAY_AUDIO_FILE_LENGTH_SECONDS_float_MOD60%s
        set DISPLAY_AUDIO_FILE_LENGTH_readable5=%@IF[%DISPLAY_AUDIO_FILE_LENGTH_MINUTES_ROUND% gt 59,%DISPLAY_AUDIO_FILE_LENGTH_HOURS_float_MOD12%h]%@IF[%DISPLAY_AUDIO_FILE_LENGTH_SECONDS_float% gt 59,%DISPLAY_AUDIO_FILE_LENGTH_MINUTES_float_MOD60%m]%@formatn[02.0,%DISPLAY_AUDIO_FILE_LENGTH_SECONDS_float_MOD60%]s
        set DISPLAY_AUDIO_FILE_LENGTH_readable6=%@IF[%DISPLAY_AUDIO_FILE_LENGTH_MINUTES_ROUND% gt 59,%DISPLAY_AUDIO_FILE_LENGTH_HOURS_float_MOD12%h ]%@IF[%DISPLAY_AUDIO_FILE_LENGTH_SECONDS_float% gt 59,%DISPLAY_AUDIO_FILE_LENGTH_MINUTES_float_MOD60%m ]%DISPLAY_AUDIO_FILE_LENGTH_SECONDS_float_MOD60%s
        set DISPLAY_AUDIO_FILE_LENGTH_readable7=%@IF[%DISPLAY_AUDIO_FILE_LENGTH_MINUTES_ROUND% gt 59,%DISPLAY_AUDIO_FILE_LENGTH_HOURS_float_MOD12%hr ]%@IF[%DISPLAY_AUDIO_FILE_LENGTH_SECONDS_float% gt 59,%DISPLAY_AUDIO_FILE_LENGTH_MINUTES_float_MOD60%min ]%DISPLAY_AUDIO_FILE_LENGTH_SECONDS_float_MOD60%sec
        set DISPLAY_AUDIO_FILE_LENGTH_readable8=%@IF[%DISPLAY_AUDIO_FILE_LENGTH_MINUTES_ROUND% gt 59,%DISPLAY_AUDIO_FILE_LENGTH_HOURS_float_MOD12%hr`,` ]%@IF[%DISPLAY_AUDIO_FILE_LENGTH_SECONDS_float% gt 59,%DISPLAY_AUDIO_FILE_LENGTH_MINUTES_float_MOD60%min`,` ]%DISPLAY_AUDIO_FILE_LENGTH_SECONDS_float_MOD60%sec
        set DISPLAY_AUDIO_FILE_LENGTH_readable9=%@IF[%DISPLAY_AUDIO_FILE_LENGTH_MINUTES_ROUND% gt 59,%DISPLAY_AUDIO_FILE_LENGTH_HOURS_float_MOD12% hr`,` ,]%@IF[%DISPLAY_AUDIO_FILE_LENGTH_SECONDS_float% gt 59,%DISPLAY_AUDIO_FILE_LENGTH_MINUTES_float_MOD60% min`,` ,]%DISPLAY_AUDIO_FILE_LENGTH_SECONDS_float_MOD60% sec
        set DISPLAY_AUDIO_FILE_LENGTH_AiTranscriptionSystem=%DISPLAY_AUDIO_FILE_LENGTH_readable9%
        set DISPLAY_AUDIO_FILE_LENGTH_readable10=%@IF[%DISPLAY_AUDIO_FILE_LENGTH_MINUTES_ROUND% gt 59,%DISPLAY_AUDIO_FILE_LENGTH_HOURS_float_MOD12% hour%HOUR_S_MAYBE% ,]%@IF[%DISPLAY_AUDIO_FILE_LENGTH_SECONDS_float% gt 59,%DISPLAY_AUDIO_FILE_LENGTH_MINUTES_float_MOD60% minute%MIN_S_MAYBE% ,]%DISPLAY_AUDIO_FILE_LENGTH_SECONDS_float_MOD60% second%SEC_S_MAYBE%
        set DISPLAY_AUDIO_FILE_LENGTH_readable11=%@IF[%DISPLAY_AUDIO_FILE_LENGTH_MINUTES_ROUND% gt 59,%DISPLAY_AUDIO_FILE_LENGTH_HOURS_float_MOD12% hour%HOUR_S_MAYBE%`,` ,]%@IF[%DISPLAY_AUDIO_FILE_LENGTH_SECONDS_float% gt 59,%DISPLAY_AUDIO_FILE_LENGTH_MINUTES_float_MOD60% minute%MIN_S_MAYBE%`,` ,]%DISPLAY_AUDIO_FILE_LENGTH_SECONDS_float_MOD60% second%SEC_S_MAYBE%
        set HOUR_S_MAYBE=%@IF[%DISPLAY_AUDIO_FILE_LENGTH_HOURS_float_MOD12% gt 1,s,]
        set  MIN_S_MAYBE=%@IF[%DISPLAY_AUDIO_FILE_LENGTH_MINUTES_float_MOD60% gt 1,s,]
        set  SEC_S_MAYBE=%@IF[%DISPLAY_AUDIO_FILE_LENGTH_SECONDS_float_MOD60% gt 1,s,]


rem Main generic output:
        set  DISPLAY_AUDIO_FILE_LENGTH_DEFAULT_OUTPUT=%STAR% %ANSI_COLOR_BRIGHT_GREEN%Length of: %italics_on%%ansi_color_bright_yellow%%DISPLAY_AUDIO_FILE_LENGTH_readable5% %ITALICS_OFF%%ANSI_COLOR_BRIGHT_YELLOW%%DASH% %ANSI_COLOR_YELLOW%for file: %ANSI_COLOR_BRIGHT_YELLOW%%faint_on%%@REPLACE[.mp3,%ANSI_COLOR_YELLOW%.mp3,%PRETTY_DAFL_FILE%] %faint_off%%STAR%


rem Verbose output:
        if "%2" != "verbose" .and. "1" != "%VERBOSE_DAFL%" goto :verbose_end
                echo                       READER_OUTPUT: %reader_output%%ansi_eol%
                echo                                 int: %DISPLAY_AUDIO_FILE_LENGTH_HOURS_INT%%ZZZZZZ% hours, %DISPLAY_AUDIO_FILE_LENGTH_MINUTES_INT%%ZZZZZZ% minutes, %DISPLAY_AUDIO_FILE_LENGTH_SECONDS_INT%%ZZZZZZ% seconds%ansi_eol%
                echo                               round: %DISPLAY_AUDIO_FILE_LENGTH_HOURS_ROUND% hours, %DISPLAY_AUDIO_FILE_LENGTH_MINUTES_ROUND% minutes, %DISPLAY_AUDIO_FILE_LENGTH_SECONDS_ROUND% seconds (rounded values)%ansi_eol%
                echo                           round mod: %DISPLAY_AUDIO_FILE_LENGTH_HOURS_ROUND_MOD12% hours, %DISPLAY_AUDIO_FILE_LENGTH_MINUTES_ROUND_MOD60% minutes, %DISPLAY_AUDIO_FILE_LENGTH_SECONDS_ROUND_MOD60% seconds (rounded values)%ansi_eol%
                echo                               float: %DISPLAY_AUDIO_FILE_LENGTH_HOURS_FLOAT%%ZZZZ% hours, %DISPLAY_AUDIO_FILE_LENGTH_MINUTES_FLOAT%%ZZZZ% minutes, %DISPLAY_AUDIO_FILE_LENGTH_SECONDS_FLOAT%%ZZZZ% seconds%ansi_eol%
                echo                           float mod: %DISPLAY_AUDIO_FILE_LENGTH_HOURS_float_MOD12% hours, %DISPLAY_AUDIO_FILE_LENGTH_MINUTES_float_MOD60% minutes, %DISPLAY_AUDIO_FILE_LENGTH_SECONDS_float_MOD60% seconds (i.e. like a clock/watch)%ansi_eol%
                echo DISPLAY_AUDIO_FILE_LENGTH_readable1:  %DISPLAY_AUDIO_FILE_LENGTH_readable1%%ansi_eol%
                echo DISPLAY_AUDIO_FILE_LENGTH_readable2:  %DISPLAY_AUDIO_FILE_LENGTH_readable2%%ansi_eol%
                echo DISPLAY_AUDIO_FILE_LENGTH_readable3:  %DISPLAY_AUDIO_FILE_LENGTH_readable3%%ansi_eol%
                echo DISPLAY_AUDIO_FILE_LENGTH_readable4:  %DISPLAY_AUDIO_FILE_LENGTH_readable4%%ansi_eol%
                echo DISPLAY_AUDIO_FILE_LENGTH_readable5:  %DISPLAY_AUDIO_FILE_LENGTH_readable5%%ansi_eol%
                echo DISPLAY_AUDIO_FILE_LENGTH_readable6:  %DISPLAY_AUDIO_FILE_LENGTH_readable6%%ansi_eol%
                echo DISPLAY_AUDIO_FILE_LENGTH_readable7:  %DISPLAY_AUDIO_FILE_LENGTH_readable7%%ansi_eol%
                echo DISPLAY_AUDIO_FILE_LENGTH_readable8:  %DISPLAY_AUDIO_FILE_LENGTH_readable8%%ansi_eol%
                echo DISPLAY_AUDIO_FILE_LENGTH_readable9:  %DISPLAY_AUDIO_FILE_LENGTH_readable9%%ansi_eol%
                echo DISPLAY_AUDIO_FILE_LENGTH_readable10: %DISPLAY_AUDIO_FILE_LENGTH_readable9%%ansi_eol%
                echo DISPLAY_AUDIO_FILE_LENGTH_readable11: %DISPLAY_AUDIO_FILE_LENGTH_readable9%%ansi_eol%
                echo DISPLAY_AUDIO_FILE_LENGTH_DEFAULT_OUTPUT: %DISPLAY_AUDIO_FILE_LENGTH_DEFAULT_OUTPUT%%ansi_eol%
        :verbose_end

rem Aliases for the results:
        set                    OUTPUT=%DISPLAY_AUDIO_FILE_LENGTH_OUTPUT%
        set                MP3_LENGTH=%DISPLAY_AUDIO_FILE_LENGTH_OUTPUT% %+ rem Here for legacy compatibility when this was an mp3-only script
        set         AUDIO_FILE_LENGTH=%DISPLAY_AUDIO_FILE_LENGTH_OUTPUT%
        set DISPLAY_MP3_LENGTH_OUTPUT=%DISPLAY_AUDIO_FILE_LENGTH_OUTPUT% %+ rem Here for legacy compatibility when this was an mp3-only script


rem Pretty output unless we give the silent option:
        echos %CURSOR_RESET%
        if "%2" == "silent" .or. "%2" == "verbose" .or. "1" == "%verbose_dafl%" goto :silent_dmp3l

                echos %DISPLAY_AUDIO_FILE_LENGTH_DEFAULT_OUTPUT%

        :silent_dmp3l
        echos %ANSI_ERASE_TO_EOL%

REM END:
        goto :END

rem Failure endpoints:
        :ffmpeg_fail_backup
                echo %bang% %ansi_color_error% %italics_on%ffmpeg%italics_off% could not read a length for file: %faint_on%%italics_on%%DAFL_FILE%%italics_off%%faint_off% %ansi_color_normal% %bang%

rem End/Cleanup:
        :END        


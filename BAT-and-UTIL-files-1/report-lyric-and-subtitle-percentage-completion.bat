@loadbtm on
@Echo Off
rem @call init-bat

rem CONFIGURATION: MAIN:                                    
        c:\mp3\                                              %+ rem change into folder we will always run this report from:        
        set skip=27                                          %+ rem how many columns to skip to get to the nature column in our logfile - “T:\mp3,20250105120414,” == 27
        set NUM_SECONDS_BEFORE_NEW_FILELISTS=300             %+ rem how many seconds to wait before generating new filelists
        set NUM_SECONDS_BEFORE_NEW_FILELISTS=5               %+ rem how many seconds to wait before generating new filelists

rem CONFIGURATION: DEBUG:
        set DEBUG_SYSTEM_CALLS=0                             %+ rem set to 1 to see the grep commands that are being used
                                                            
rem CONFIGURATION: COSMETIC ALIGNMENT:
        set lines_to_show=%@FLOOR[%@EVAL[(%_ROWS - 18) / 2]] %+ rem how many lines from each progress logfile to show with the “tail” command
        set mover=%@ANSI_MOVE_TO_COL[38]

rem CONFIGURATION: FILENAMES:
        set           full_filelist=filelist-all.txt
        set           text_filelist=filelist-txt.txt
        set transcribeable_filelist=filelist-transcribeable.txt
        set  transcription_filelist=filelist-transcriptions.txt
        set report_log=lyric-subtitle-compliance.log
        set AI_TRASH_FILES=*._vad_collected_chunks*.wav *._vad_collected_chunks*.log *._vad_collected_chunks*.srt *._vad_original*.srt *._vad_pyannote_*chunks*.wav *._vad_pyannote_v3.txt create-the-missing-karaokes-here-temp*.bat get-the-missing-lyrics-here-temp*.bat get-the-missing-karaoke-here-temp*.bat
        rem If this changes, also update the similar values in clean-up-AI-transcription-trash-files-everywhere.bat:

rem Validate environment (once):
        iff "1" != "%validated_countsoffiletype%" then
                call validate-in-path               grep egrep uniq wc copy-move-post makefilelist warning_soft set-tmp-file fast_cat clean-up-AI-transcription-trash-files-everywhere.bat wc
                call validate-is-function           ansi_move_to_col
                call validate-environment-variables connecting_equals 
                set  validated_countsoffiletype=1
        endiff

rem Warn, unless we are in the same folder defined as MP3OFFICIAL in our environment:
        if "%1" == "force"                                     goto :No_warning
        if defined MP3OFFICIAL .and. "%_CWD" != "%MP3OFFICIAL" %mp3official%\
        if defined MP3OFFICIAL .and. "%_CWD" == "%MP3OFFICIAL" goto :No_warning
                call warning_soft "This report is supposed to be run in the base of your audio folder! Pass 2ⁿᵈ parameter of “force”"
                pause /# 3
                goto :END
        :No_warning

rem Re-create variable if not included in environment:
        if not defined filemask_audio_regex set filemask_audio_regex=(\.mp3|\.wav|\.rm|\.voc|\.au|\.mid|\.stm|\.mod|\.vqf|\.ogg|\.mpc|\.wma|\.mp4|\.flac|\.snd|\.aac|\.opus|\.ac3|\.ra)



rem Clean up trash files first
        if "%1" == "quick" .or. "%1" == "fast"  goto :skip_preclean
        cls
        call clean-up-AI-transcription-trash-files-everywhere.bat do_not_delete_BATs
        :skip_preclean
        cls

rem Count the file types:    
        echo.
        set dir=%_CWD
        set remake=0
        if   not   exist    %transcribeable_filelist% (set remake=1 %+ goto :remake)
        if   not   exist     %full_filelist%          (set remake=1 %+ goto :remake)
        if %@eval[%@makeage[%_date,%_time] - %@fileage[%transcribeable_filelist%]] gt %@EVAL[%NUM_SECONDS_BEFORE_NEW_FILELISTS * 10000000] (set remake=1)     %+ rem if it’s more than 180s old
        :remake
        if "%1"=="quick" .or. "%1"==fast goto :go_here_from_if_at_64
                iff "1" == "%remake%" then
                        rem make main filelist:
                                echos %ansi_color_important%%blink_on%%star2%%blink_off% Making master filelist%@RANDFG_SOFT[]... 
                                                          if "%1" != "quick" .and. "%1" != "fast"  ((dir /b /s /[!%AI_TRASH_FILES%]                   %filemask_audio%  >:u8%full_filelist%)) %+ echos %@RANDFG_SOFT[]...
                                if defined incoming_music if "%1" != "quick" .and. "%1" != "fast"  ((dir /b /s /[!%AI_TRASH_FILES%]  %incoming_music%\%filemask_audio% >>:u8%full_filelist%)) %+ echos %@RANDFG_SOFT[]...
                                echo %mover%%@COMMA[%@EXECSTR[type %full_filelist% | wc -l]] %faint_on%files%faint_off%

                        rem Make transcribeable filelist:
                                echos %ansi_color_important%%blink_on%%star2%%blink_off% Making transcribeable filelist%@RANDFG_SOFT[]... 
                                                          ((dir /b /s /[!%AI_TRASH_FILES%  "::\[instrumental\]" *sound?effect* *.mid *.midi *.stm *.s3m *.mod *.cmf *.rol *chiptune*]                  %filemask_audio%   >:u8%transcribeable_filelist)) %+ echos %@RANDFG_SOFT[]...
                                if defined incoming_music ((dir /b /s /[!%AI_TRASH_FILES%  "::\[instrumental\]" *sound?effect* *.mid *.midi *.stm *.s3m *.mod *.cmf *.rol *chiptune*] %incoming_music%\%filemask_audio%  >>:u8%transcribeable_filelist)) %+ echos %@RANDFG_SOFT[]...
                                echo %mover%%@COMMA[%@EXECSTR[type %transcribeable_filelist% | wc -l]] %faint_on%files%faint_off%

                        rem Make txt filelist:
                                echos %ansi_color_important%%blink_on%%star2%%blink_off% Making txt filelist%@RANDFG_SOFT[]... 
                                                          ((dir /b /s /[!%AI_TRASH_FILES% readme*.* *tablature*.txt *tabulature*.txt filelist*.* normalization-report*.* shn.txt dirlist*.txt delme*.* *lyrics*.txt *discography*.txt meaning*songmeaning*.txt dir.txt \lyrics\*.txt \lists*\*.txt foobar*.txt "amg review.txt" names.txt tree.txt "* - README.txt" track_*.txt "dir (?).txt" bridge-??.txt  "lyrics - *.txt"]                  *.txt  >:u8%text_filelist)) %+ echos %@RANDFG_SOFT[]...
                                if defined incoming_music ((dir /b /s /[!%AI_TRASH_FILES% readme*.* *tablature*.txt *tabulature*.txt filelist*.* normalization-report*.* shn.txt dirlist*.txt delme*.* *lyrics*.txt *discography*.txt meaning*songmeaning*.txt dir.txt \lyrics\*.txt \lists*\*.txt foobar*.txt "amg review.txt" names.txt tree.txt "* - README.txt" track_*.txt "dir (?).txt" bridge-??.txt  "lyrics - *.txt"] %incoming_music%\*.txt >>:u8%text_filelist)) %+ echos %@RANDFG_SOFT[]...
                                echo %mover%%@COMMA[%@EXECSTR[type %text_filelist% | wc -l]] %faint_on%files%faint_off%

                        rem Make txt filelist:
                                echos %ansi_color_important%%blink_on%%star2%%blink_off% Making transcribed filelist%@RANDFG_SOFT[]... %ansi_color_normal%
                                                          ((dir /b /s /[!%AI_TRASH_FILES%]                  *.srt;*.lrc  >:u8%transcription_filelist)) %+ echos %@RANDFG_SOFT[]...
                                if defined incoming_music ((dir /b /s /[!%AI_TRASH_FILES%] %incoming_music%\*.srt;*.lrc >>:u8%transcription_filelist)) %+ echos %@RANDFG_SOFT[]...
                                echo %mover%%@COMMA[%@EXECSTR[type %transcription_filelist% | wc -l]] %faint_on%files%faint_off%

                        rem Cosmetics
                                echo %mover%%@ANSI_MOVE_TO_COL[1]%ANSI_ERASE_TO_EOL%%@ANSI_MOVE_UP[1]
                                repeat 2 echo.
                endiff
        :go_here_from_if_at_64


rem Validate environment for what we need to finish:
        iff "1" !=  "%validated_rlaspctcsubtoo934%" then
                call  validate-in-path egrep wc
                set   validated_rlaspctcsubtoo934=1
        endiff
        if not exist "%transcribeable_filelist%" .or. not exist "%full_filelist%" call validate-environment-variables transcribeable_filelist full_filelist

rem Initialize audio file counts, though we trash some of these values so it’s unnecessary:
        unset /q *count*

        set TRANSCRIBEABLE_AUDIO_COUNT=0 %+ set TRANSCRIBEABLE_AUDIO_COUNT=%@EXECSTR[egrep "%@UNQUOTE[%filemask_audio_regex%]" %transcribeable_filelist% | wc -l]
        set            ALL_AUDIO_COUNT=0 %+ set            ALL_AUDIO_COUNT=%@EXECSTR[egrep "%@UNQUOTE[%filemask_audio_regex%]"           %FULL_FILELIST% | wc -l]

        rem echo ALL_AUDIO_COUNT is %ALL_AUDIO_COUNT% which should be 60619ish as of 20250219ish

rem Report our totals and percent  progress:
        call divider
        rem  :counttype [nature_clean nature FILECOUNT_THAT_EQUALS_100_PERCENT regex filelisttouse]

                set filelist_to_use=%transcribeable_filelist%
                iff "%@UNQUOTE[%nature_clean%]" == "instrumental" .or. "%@UNQUOTE[%nature_clean%]" == "total" then
                        set filelist_to_use=%full_filelist%
                else
                        set filelist_to_use=%transcribeable_filelist%
                endiff


        gosub lineyline
        gosub counttype          "total" "       total audio"  NULL                                  "%@UNQUOTE[%filemask_audio_regex%]"           "%full_filelist%" %+ set            ALL_AUDIO_COUNT_PROBED=%COUNT%
        gosub counttype   "instrumental" "  -   instrumental" %ALL_AUDIO_COUNT_PROBED% "instrumental.*%@UNQUOTE[%filemask_audio_regex%]"           "%full_filelist%" %+ set         INSTRUMENTAL_COUNT=%COUNT%
        gosub counttype      "chiptunes" "  -      chiptunes" %ALL_AUDIO_COUNT_PROBED%   "chiptunes*.*%@UNQUOTE[%filemask_audio_regex%]"           "%full_filelist%" %+ set             CHIPTUNE_COUNT=%COUNT%
        gosub counttype  "tracker songs" "  -  tracker songs" %ALL_AUDIO_COUNT_PROBED% "(\.mid|\.midi|\.stm|\.s3m|\.mod|\.cmf\*.rol)"              "%full_filelist%" %+ set         TRACKER_SONG_COUNT=%COUNT%
        gosub counttype   "sound effect" "  -   sound effect" %ALL_AUDIO_COUNT_PROBED% "sound.effect.*%@UNQUOTE[%filemask_audio_regex%]"           "%full_filelist%" %+ set         SOUND_EFFECT_COUNT=%COUNT%        
                                    echo    %@REPEAT[━,40]
        gosub counttype "transcribeable" "  = transcribeable" %ALL_AUDIO_COUNT_PROBED%               "%@UNQUOTE[%filemask_audio_regex%]" "%transcribeable_filelist%" %+ set TRANSCRIBEABLE_AUDIO_COUNT_PROBED=%COUNT% %+         gosub lineyline
        gosub counttype         "lyrics" "            lyrics" %TRANSCRIBEABLE_AUDIO_COUNT_PROBED%     "\.txt"                                      "%text_filelist%" %+ set           HAVE_LYRIC_COUNT=%COUNT%
        gosub counttype        "karaoke" "           karaoke" %TRANSCRIBEABLE_AUDIO_COUNT_PROBED%    "(\.lrc|\.srt)"                      "%transcription_filelist%" %+ set         HAVE_KARAOKE_COUNT=%COUNT%
        gosub lineyline
        call  divider
        echo.

rem Show the last few values of our progress in our log files:
        set highlight="[0-9][0-9]?\.[0-9][0-9]"
        rem need 4 temp files:
                call set-tmp-file  %+  set tmpfile1=%tmpfile%
                call set-tmp-file  %+  set tmpfile2=%tmpfile%
                call set-tmp-file  %+  set tmpfile3=%tmpfile%
                call set-tmp-file  %+  set tmpfile4=%tmpfile%
        rem lyric alignment progress:
                ((type %report_log%|grep -i  lyrics)|uniq -s%SKIP%) >:u8%tmpfile1% 
                head -1               %tmpfile1% |:u8 call highlight %highlight%  >:u8%tmpfile2% 
                tail -%lines_to_show% %tmpfile1% |:u8 call highlight %highlight% >>:u8%tmpfile2% 
                call fast_cat                                                         %tmpfile2%
        rem karaoke alignment progress:
                call divider %+ echo.
                ((type %report_log%|grep -i karaoke)|uniq -s%SKIP%) >:u8%tmpfile3% 
                head -1               %tmpfile3% |:u8 call highlight %highlight%  >:u8%tmpfile4% 
                tail -%lines_to_show% %tmpfile3% |:u8 call highlight %highlight% >>:u8%tmpfile4% 
                call fast_cat                                                         %tmpfile4%
                call divider

goto :END

:━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
:━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
:━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        :lineyline
                set width2use=40
                set divider=c:\bat\dividers\rainbow-%width2use%.txt
                if     exist %divider% (type %divider% %+ echo.)
                if not exist %divider%  echo %@REPEAT[%connecting_equals%,%width2use%]
                
        return
        :counttype [nature_clean nature FILECOUNT_THAT_EQUALS_100_PERCENT regex filelist_to_use]
                if %DEBUG gt 0 echo CALLED: :counttype [%nature% %FILECOUNT_THAT_EQUALS_100_PERCENT% %regex%]
                title counttype %nature %FILECOUNT_THAT_EQUALS_100_PERCENT %regex
                echos %@randfg_soft[]%italics_on%%@UNQUOTE[%Nature%]%italics_off%: %@randfg_soft[]

                rem DEBUG:
                        iff 1 == %DEBUG_SYSTEM_CALLS% then
                                echo %ansi_color_debug%- DEBUG: %tab%grep command is “egrep -i "%@unquote[%regex%]" "%filelist_to_use%"”%ansi_color_normal%
                                rem echos %newline%
                                rem setdos /x-5
                                rem         echos %%@EXECSTR[egrep -i "%@unquote[%regex%]" "%filelist_to_use%" `|` wc -l  ]
                                rem setdos /x5
                                rem echos %newline%%@ansi_move_to_col[15]
                        endiff

                rem count from our filelist:
                        set COUNT=%@EXECSTR[egrep -i "%@unquote[%regex%]" "%filelist_to_use%" | wc -l]
                        iff "NULL" == "%FILECOUNT_THAT_EQUALS_100_PERCENT%" then
                                set FILECOUNT_THAT_EQUALS_100_PERCENT_TO_USE=%ALL_AUDIO_COUNT_PROBED%
                        else
                                set FILECOUNT_THAT_EQUALS_100_PERCENT_TO_USE=%FILECOUNT_THAT_EQUALS_100_PERCENT%
                        endiff
                        echos %@FORMAT[6,%@COMMA[%@FORMATn[5.0,%COUNT%]]]

                rem percentage:
                        rem echo -DEBUG: FILECOUNT_THAT_EQUALS_100_PERCENT_TO_USE=“%FILECOUNT_THAT_EQUALS_100_PERCENT_TO_USE%” FOR %NATURE%
                        if %FILECOUNT_THAT_EQUALS_100_PERCENT_TO_USE% gt 0 goto :has_value_beg
                                                                            goto :has_value_end
                                :has_value_beg
                                        SET RAW_VALUE=%@EVAL[%COUNT%/%FILECOUNT_THAT_EQUALS_100_PERCENT_TO_USE%*100]
                                        set    VALUE=%@FORMATn[-4.1,%raw_value%]
                                        rem  %dir%,%_datetime,%@TRIM[%@UNQUOTE[%nature%]],%raw_value%%@CHAR[65285],%COUNT%,%FILECOUNT_THAT_EQUALS_100_PERCENT_TO_USE to %report_log%
                                        echo %dir%,%_datetime,%@UNQUOTE[%nature_clean%],%raw_value%%@CHAR[65285],%COUNT%,%FILECOUNT_THAT_EQUALS_100_PERCENT_TO_USE% >>%report_log%
                                        echos  %@randfg_soft[]%@FORMAT[8,(%VALUE%%@CHAR[65285])]
                                :has_value_end
                        echo.

                rem about to return
        return
        echo This is the line past return and we should never be here! %+ pause
:━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
:━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
:━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

:END


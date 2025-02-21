@loadbtm on
@Echo Off
rem @call init-bat


rem CONFIGURATION: MAIN:
        set AI_TRASH_FILES=*._vad_collected_chunks*.wav *._vad_collected_chunks*.log *._vad_collected_chunks*.srt *._vad_original*.srt *._vad_pyannote_*chunks*.wav *._vad_pyannote_v3.txt create-the-missing-karaokes-here-temp*.bat get-the-missing-lyrics-here-temp*.bat get-the-missing-karaoke-here-temp*.bat
        set NUM_SECONDS_BEFORE_NEW_FILELISTS=300
        set NUM_SECONDS_BEFORE_NEW_FILELISTS=5

rem CONFIGURATION: REST:
        set log=lyric-subtitle-compliance.log
        set vocal_filelist=filelist-non-instrumental.txt
        set full_filelist=filelist.txt
        set DEBUG_SYSTEM_CALLS=0                                        %+ rem set to 1 to see the grep commands that are being used
        rem If this changes, also update the similar values in clean-up-AI-transcription-trash-files-everywhere.bat:

rem Validate environment (once):
        iff 1   ne  %validated_countsoffiletype8% then
                call validate-in-path              grep egrep uniq wc copy-move-post makefilelist warning_soft set-tmp-file fast_cat clean-up-AI-transcription-trash-files-everywhere.bat
                call validate-is-function          ansi_move_to_col
                set  validated_countsoffiletype8=1
        endiff

rem Warn, unless we are in the same folder defined as MP3OFFICIAL in our environment:
        if "%1" == "force"                                     goto :No_warning
        if defined MP3OFFICIAL .and. "%_CWD" eq "%MP3OFFICIAL" goto :No_warning
                call warning_soft "This report is supposed to be run in the base of your audio folder! Pass 2ⁿᵈ parameter of “force”"
                pause /# 3
                goto :END
        :No_warning

rem Re-create variable if not included in environment:
        if not defined filemask_audio_regex set filemask_audio_regex=(\.mp3|\.wav|\.rm|\.voc|\.au|\.mid|\.stm|\.mod|\.vqf|\.ogg|\.mpc|\.wma|\.mp4|\.flac|\.snd|\.aac|\.opus|\.ac3|\.ra)



rem Clean up trash files first
        if "%1" == "quick" goto :skip_preclean
        cls
        call clean-up-AI-transcription-trash-files-everywhere.bat do_not_delete_BATs
        cls
        :skip_preclean

rem Count the file types:    
        echo.
        set dir=%_CWD
        set remake=0
        if   not   exist    %vocal_filelist%                                            (set remake=1 %+ goto :remake)
        if   not   exist     %full_filelist%                                            (set remake=1 %+ goto :remake)
        if %@eval[%@makeage[%_date,%_time] - %@fileage[%vocal_filelist%]] gt %@EVAL[%NUM_SECONDS_BEFORE_NEW_FILELISTS * 10000000] (set remake=1)     %+ rem if it’s more than 180s old
        :remake
        iff 1 eq %remake% then
                echos * Making filelists... 
                rem echo DEBUG: dir /b /s /[!%AI_TRASH_FILES% *instrumental*] %vocal_filelist
                rem echo DEBUG: dir /b /s /[!%AI_TRASH_FILES%]                %full_filelist%
                ((dir /b /s /[!%AI_TRASH_FILES% *instrumental*] >:u8%vocal_filelist) | copy-move-post) %+ echos ...
                ((dir /b /s /[!%AI_TRASH_FILES%]                >:u8%full_filelist%) | copy-move-post)
                rem echo %@ANSI_MOVE_UP[1]%@ANSI_MOVE_TO_COL[1]%ANSI_ERASE_TO_EOL%%@ANSI_MOVE_UP[1]
                                     echo %@ANSI_MOVE_TO_COL[1]%ANSI_ERASE_TO_EOL%%@ANSI_MOVE_UP[1]
        endiff


rem Validate environment for what we need to finish:
        iff "1" !=  "%validated_rlaspctcsubtoo934%" then
                call  validate-in-path egrep wc
                set   validated_rlaspctcsubtoo934=1
        endiff
        call validate-environment-variable vocal_filelist full_filelist

rem Initialize audio file counts, though we trash some of these values so it’s unnecessary:
        unset /q *count*
        set VOCAL_AUDIO_COUNT=0
        set   ALL_AUDIO_COUNT=%@EXECSTR[egrep "%@UNQUOTE[%filemask_audio_regex%]" %FULL_FILELIST%  | wc -l]
        set VOCAL_AUDIO_COUNT=%@EXECSTR[egrep "%@UNQUOTE[%filemask_audio_regex%]" %VOCAL_FILELIST% | wc -l]

        rem echo ALL_AUDIO_COUNT is %ALL_AUDIO_COUNT% which should be 60619ish as of 20250219ish

rem Report our totals:
        call divider
        gosub counttype        "total" "       total audio"  NULL                                  "%@UNQUOTE[%filemask_audio_regex%]"  %+ set    ALL_AUDIO_COUNT_PROBED=%COUNT%
        gosub counttype "instrumental" "      instrumental" %ALL_AUDIO_COUNT_PROBED% "instrumental.*%@UNQUOTE[%filemask_audio_regex%]"  %+ set INSTRUMENTAL_COUNT=%COUNT%
        gosub counttype        "audio" "             vocal" %ALL_AUDIO_COUNT_PROBED%               "%@UNQUOTE[%filemask_audio_regex%]"  %+ set  VOCAL_AUDIO_COUNT_PROBED=%COUNT%
        gosub counttype       "lyrics" "            lyrics" %VOCAL_AUDIO_COUNT%                               "\.txt"                   %+ set   HAVE_LYRIC_COUNT=%COUNT%
        gosub counttype      "karaoke" "           karaoke" %VOCAL_AUDIO_COUNT%                               "(\.lrc|\.srt)"           %+ set HAVE_KARAOKE_COUNT=%COUNT%
        call divider
        echo.

rem Report our findings:
        rem pause
        set skip=27
        set highlight="[0-9][0-9]?\.[0-9][0-9]"
        rem (type %log%|grep -i  lyrics)|uniq -s%SKIP%|call highlight %highlight%
        rem (type %log%|grep -i karaoke)|uniq -s%SKIP%|call highlight %highlight%
        call set-tmp-file %+ set tmpfile1=%tmpfile%
        call set-tmp-file %+ set tmpfile2=%tmpfile%
        call set-tmp-file %+ set tmpfile3=%tmpfile%
        call set-tmp-file %+ set tmpfile4=%tmpfile%
        call divider
                ((type %log%|grep -i  lyrics)|uniq -s%SKIP%)        >:u8%tmpfile1% 
                head -1 %tmpfile1% |:u8 call highlight %highlight%  >:u8%tmpfile2% 
                tail -6 %tmpfile1% |:u8 call highlight %highlight% >>:u8%tmpfile2% 
                call fast_cat                                           %tmpfile2%
        call divider
                ((type %log%|grep -i karaoke)|uniq -s%SKIP%)        >:u8%tmpfile3% 
                head -1 %tmpfile3% |:u8 call highlight %highlight%  >:u8%tmpfile4% 
                tail -6 %tmpfile3% |:u8 call highlight %highlight% >>:u8%tmpfile4% 
                call fast_cat                                           %tmpfile4%
        call divider

goto :END

:━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
:━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
:━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        :counttype [nature_clean nature AUDIO_COUNT_TOTAL_TO_USE_FOR_PCT_CALCS regex]
                if %DEBUG gt 0 echo CALLED: :counttype [%nature% %AUDIO_COUNT_TOTAL_TO_USE_FOR_PCT_CALCS% %regex%]
                title counttype %nature %AUDIO_COUNT_TOTAL_TO_USE_FOR_PCT_CALCS %regex
                echos %@randfg_soft[]
                echos %italics_on%%@UNQUOTE[%Nature%]%italics_off%: ``
                echos %@randfg_soft[]
                set filelist_to_use=%vocal_filelist%
                iff "%@UNQUOTE[%nature_clean%]" == "instrumental" .or. "%@UNQUOTE[%nature_clean%]" == "total" then
                        set filelist_to_use=%full_filelist%
                else
                        set filelist_to_use=%vocal_filelist%
                endiff

                rem DEBUG:
                        iff 1 == %DEBUG_SYSTEM_CALLS% then
                                echo %tab%grep command is egrep -i "%@unquote[%regex%]" "%filelist_to_use%"
                                echos %newline%
                                setdos /x-5
                                        echos %%@EXECSTR[egrep -i "%@unquote[%regex%]" "%filelist_to_use%" `|` wc -l  ]
                                setdos /x5
                                echos %newline%%@ansi_move_to_col[15]
                        endiff

                set COUNT=%@EXECSTR[egrep -i "%@unquote[%regex%]" "%filelist_to_use%" | wc -l  ]
                iff "NULL" == "%AUDIO_COUNT_TOTAL_TO_USE_FOR_PCT_CALCS%" then
                        set AUDIO_COUNT_TOTAL_TO_USE_FOR_PCT_CALCS_TO_USE=%COUNT%
                else
                        set AUDIO_COUNT_TOTAL_TO_USE_FOR_PCT_CALCS_TO_USE=%AUDIO_COUNT_TOTAL_TO_USE_FOR_PCT_CALCS%
                endiff
                echos %@FORMAT[6,%@COMMA[%@FORMATn[5.0,%COUNT%]]]
                if %AUDIO_COUNT_TOTAL_TO_USE_FOR_PCT_CALCS% gt 0 goto :has_value
                                      goto :has_value_end
                        :has_value
                                set RAW_VALUE=%@EVAL[%count/%AUDIO_COUNT_TOTAL_TO_USE_FOR_PCT_CALCS_TO_USE%*100]
                                set VALUE=%@FORMATn[-4.1,%raw_value%]
                                echo %dir%,%_datetime,%@TRIM[%@UNQUOTE[%nature%]],%raw_value%%@CHAR[65285],%COUNT% >>%log%
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


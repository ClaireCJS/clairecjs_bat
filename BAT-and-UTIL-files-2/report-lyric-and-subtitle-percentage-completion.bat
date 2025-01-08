@echo Off
 call init-bat

rem CONFIGURATION:
        set log=lyric-subtitle-compliance.log
        set filelist=filelist-non-instrumental.txt

rem Validate environment (once):
        iff 1 ne %validated_countsoffiletype6% then
                call validate-in-path              grep egrep uniq wc copy-move-post makefilelist warning_soft 
                call validate-is-function          ansi_move_to_col
                set  validated_countsoffiletype6=1
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

rem Count the file types:    
        echo.
        set dir=%_CWD
        set remake=0
        if   not   exist    %filelist%                                            (set remake=1 %+ goto :remake)
        if %@eval[%@makeage[%_date,%_time] - %@fileage[%filelist%]] gt 1800000000 (set remake=1)     %+ rem if it’s more than 180s old
        :remake
        iff 1 eq %remake% then
                echo * Making filelist... 
                ((dir /b /s /[!*instrumental*] >:u8%filelist%) | copy-move-post)
                echo %@ANSI_MOVE_UP[1]%@ANSI_MOVE_TO_COL[1]%ANSI_ERASE_TO_EOL%%@ANSI_MOVE_UP[1]
        endiff

        rem Initialize audio file count:
                set AUDIO_COUNT=0

        rem 1ˢᵗ gosub
                gosub :counttype "  audio" %AUDIO_COUNT% "%@UNQUOTE[%filemask_audio_regex%]"   

        rem Update audio file count with results from 1ˢᵗ gosub:
                set AUDIO_COUNT=%COUNT%

        rem 2ⁿᵈ gosub
                gosub :counttype " lyrics" %AUDIO_COUNT% "\.txt"

        rem 3ʳᵈ  gosub
                gosub :counttype "karaoke" %AUDIO_COUNT% "(\.lrc|\.srt)"

        echo.
        pause
        set skip=27
        set highlight="[0-9][0-9]?\.[0-9][0-9]"
        (type %log%|grep -i  lyrics)|uniq -s%SKIP%|call highlight %highlight%
        (type %log%|grep -i karaoke)|uniq -s%SKIP%|call highlight %highlight%

goto :END
        :counttype [nature audio_count regex]
                title counttype %nature %audio_count %regex
                echos %@randfg_soft[]
                echos %italics_on%%@UNQUOTE[%Nature%]%italics_off%: ``
                echos %@randfg_soft[]
                set COUNT=%@EXECSTR[egrep -i "%@unquote[%regex%]" %filelist% | wc -l  ]
                echos %@COMMA[%COUNT%]
                iff %audio_count% gt 0 then
                        set RAW_VALUE=%@EVAL[%count/%audio_COUNT%*100]
                        set VALUE=%@FORMATn[-4.1,%raw_value%]
                        echo %dir%,%_datetime,%@TRIM[%@UNQUOTE[%nature%]],%raw_value%%@CHAR[65285] >>%log%
                        echos  %@randfg_soft[](%VALUE%%@CHAR[65285]) 
                endiff
                echo.
        return
:END


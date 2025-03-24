@Echo OFF


rem Config:
        set OUR_LOG=%LOGS%\audiofile-transcription.log


rem Validate environment (once):
        iff "1" != "%validated_report_lyric_approval_progress_2%" then
                call validate-environment-variables OUR_LOG wrench cool_percent underline_on underline_off
                call validate-in-path               yyyymmdd grep wc divider
                call validate-function              randfg_soft
                set  validated_report_lyric_approval_progress_2=1
        endiff

rem Set current day:
        if "%1" != "" set day_to_report_on=%1
        if defined day_to_report_on goto :date_defined
                call                   yyyymmdd
                if   not    defined    yyyymmdd  call validate-environment-variable yyyymmdd
                set  day_to_report_on=%yyyymmdd%
        :date_defined

rem Allow us to change it if we want:
        if "%1" != "" goto :skip_this_part_30
                echo %wrench% Change date if you want:
                eset day_to_report_on
        :skip_this_part_30

rem Count totals for that date:
        set total_lyric_decision=%@EXECSTR[grep    %day_to_report_on%                            %our_log% | wc -l]
        set total_lyric_approval=%@EXECSTR[grep -i %day_to_report_on%.*Approved:.*Lyrics:        %our_log% | wc -l]
        set total_lyriclessness=%@EXECSTR[ grep -i %day_to_report_on%.*Approved:.*Lyriclessness: %our_log% | wc -l]

rem Display totals:
        call divider
        call bigecho "%STAR% %@randfg_soft[]%underline_on%DATE%underline_off%: %underline_on%%@LEFT[4,%day_to_report_on%]/%@RIGHT[2,%@LEFT[6,%day_to_report_on%]]/%@RIGHT[2,%day_to_report_on%]%underline_off% %STAR%"
        echo %@randfg_soft[]total lyric decisions made =====`>` %@randfg_soft[]%total_lyric_decision%
        echo %@randfg_soft[]       lyrics files  approvals =`>` %@randfg_soft[]%total_lyric_approval%
        echo %@randfg_soft[]       lyriclessness approvals =`>` %@randfg_soft[]%total_lyriclessness%
        iff 0 eq %total_lyric_decision% then
                set our_percentage=0
        else
                set our_percentage=%@floor[%@EVAL[total_lyric_approval / total_lyric_decision * 100]]
        endiff
        echo %@randfg_soft[]          percent lyrics found =`>` %@randfg_soft[]%our_percentage%%cool_percent%
        call divider

rem Cleanup:

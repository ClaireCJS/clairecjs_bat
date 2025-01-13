@loadbtm on
@Echo OFF
 on break cancel
 rem cls

rem Validate environemnt (once):
        iff 1 ne %validated_predownloadlyricshere% then
                call validate-in-path get-lyrics create-txt-lyrics-from-karaoke-files status-bar less_important
                call validate-environment-variables ansi_colors_have_been_set
                set  validated_predownloadlyricshere=1
        endiff


rem Variables to use:
        set tmpname=%@UNQUOTE[%@FILENAME["%_CWD"]]


rem Convert any LRC/SRT w/o TXT first:
        iff exist *.lrc;*.srt then
                call less_important " LRC/SRT %arrow  TXT in: %tmpname%"
                call status-bar      "LRC/SRT %arrow% TXT in: %tmpname%"
                call create-txt-lyrics-from-karaoke-files
                call status-bar unlock
        endiff

rem Pre-download the lyrics here:
        echos %@ANSI_MOVE_TO_COL[1]
        set tmpmsg=Getting lyrics in: %faint_on%%tmpname%%faint_off%
        echo %ansi_color_less_important%%star% %tmpmsg%%ansi_color_normal%
        call status-bar     "%tmpmsg%"
        set DONT_MESS_WITH_MY_STATUS_BAR=1
        call get-lyrics here genius
        set DONT_MESS_WITH_MY_STATUS_BAR=0
        cls
        rem echo PREDOWNLOADED_FOLDERS_JUST_NOW is at first “%PREDOWNLOADED_FOLDERS_JUST_NOW%”
        rem echo that plus one would be %@EVAL[1 + %PREDOWNLOADED_FOLDERS_JUST_NOW%]
        SET  new_value=%@EVAL[1 + %PREDOWNLOADED_FOLDERS_JUST_NOW%]
        rem echo new_value is “%new_value%” ... setting PREDOWNLOADED_FOLDERS_JUST_NOW to NEW_VALUE
        SET PREDOWNLOADED_FOLDERS_JUST_NOW=%new_value%
        rem echo PREDOWNLOADED_FOLDERS_JUST_NOW is now %PREDOWNLOADED_FOLDERS_JUST_NOW% %+ pause
        echo %ANSI_COLOR_success%%CHECK% %faint_on%Done getting lyrics in: %faint_off%%faint_on%%italics_on%%tmpname%%italics_off%%faint_off% %CHECK%%ansi_color_normal%
        gosub divider


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

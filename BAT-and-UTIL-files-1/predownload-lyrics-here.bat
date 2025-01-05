@Echo Off
 on break cancel
 rem cls

rem Validate environemnt (once):
        iff 1 ne %validated_predownloadlyricshere% then
                call validate-in-path get-lyrics create-txt-lyrics-from-karaoke-files status-bar less_important
                set  validated_predownloadlyricshere=1
        endiff


rem Variables to use:
        set tmpname=%@UNQUOTE["%@NAME["%_CWD"].%@EXT["%_CWD"]"]


rem Convert any LRC/SRT w/o TXT first:
        iff exist *.lrc;*.srt then
                call less_important "LRC/SRT %arrow  TXT in: %tmpname%"
                call status-bar     "LRC/SRT %arrow% TXT in: %tmpname%"
                call create-txt-lyrics-from-karaoke-files
                call status-bar unlock
        endiff

rem Pre-download the lyrics here:
        echos %@ANSI_MOVE_TO_COL[1]
        set tmpmsg=Getting lyrics in: %faint_on%%tmpname%%faint_off%
        call less_important "%tmpmsg%"
        call status-bar     "%tmpmsg%"
        set DONT_MESS_WITH_MY_STATUS_BAR=1
        call get-lyrics here genius
        set DONT_MESS_WITH_MY_STATUS_BAR=0
        cls
        call success  "Done getting lyrics in %tmpname%"
        call divider


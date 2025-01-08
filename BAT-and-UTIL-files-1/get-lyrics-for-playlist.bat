@Echo OFF
 on break cancel

rem USAGE:
        iff "%1" eq "" then
                %color_advice%
                text
                        USAGE: %0 {playlist_filename} -- to check all files of that playlist for approved lyrics
                endtext
                goto :END
        endiff

rem VALIDATE ENVIRONMENT:
        iff 1 ne    %validated_glfp then
                call validate-in-path check-for-missing-lyrics.bat
                set  validated_glfp=1
        endiff
        
rem GRAB + VALIDATE PARAMETER IS A M3U/TXT file:
        set                                 FILELIST_TO_USE=%@unquote[%1]
        call validate-environment-variable  FILELIST_TO_USE
        call validate-is-extension        "%FILELIST_TO_USE%" *.m3u;*.txt  "1ˢᵗ parameter to %0 must be of .%underline_on%m3u%underline_off% or .%underline_on%txt%underline_off% extension"
 
 rem Go through the file and check for missing lyrics:
        call check-for-missing-lyrics.bat "%FILELIST_TO_USE%" get %2$
         
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

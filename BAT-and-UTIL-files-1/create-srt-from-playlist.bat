@loadbtm on
@Echo OFF
 on break cancel
 setdos /x0

rem USAGE:
        iff "%1" eq "" then
                %color_advice%
                text
                        USAGE: %0 {playlist_filename} {limit} -- to check all files of that playlist for karokes, until we find our limit
                endtext
                goto /i END
        endiff

rem VALIDATE ENVIRONMENT:
        iff 1 ne    %validated_glfp then
                call validate-in-path check-for-missing-lyrics.bat
                set  validated_glfp=1
        endiff
        
rem GRAB + VALIDATE PARAMETER IS A M3U/TXT file:
        set FILELIST_TO_USE=%@unquote[%1]
        if not exist "%FILELIST_TO_USE%"  call validate-environment-variable  FILELIST_TO_USE
        call validate-is-extension        "%FILELIST_TO_USE%"   *.m3u;*.txt   "1ˢᵗ parameter to %0 must be of .%underline_on%m3u%underline_off% or .%underline_on%txt%underline_off% extension because it is a filelist"
 
 rem Go through the file and check for missing karaoke by using the script that does this for missing lyrics, but in “secret” karaoke mode:
        call check-for-missing-lyrics.bat karaoke "%FILELIST_TO_USE%" %2$
         
:END        


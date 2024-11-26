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
        iff 1 ne %VALIDATED_GLFP then
                call validate-in-path check-for-missing-lyrics.bat
                set  VALIDATED_GLFP=1
        endiff
        
rem GRAB + VALIDATE PARAMETER IS A M3U/TXT file:
        set FILELIST_TO_USE=%1
        call validate-environment-variable FILELIST_TO_USE
        call validate-is-extension       "%FILELIST_TO_USE%" *.m3u;*.txt  "1ˢᵗ parameter to %0 must be of .m3u or .txt extension"
 
 rem Go through the file and check for missing lyrics:
        call check-for-missing-lyrics.bat %FILELIST_TO_USE% get
         
:END        
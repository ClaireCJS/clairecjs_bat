@Echo OFF
 echo.

 
:DESCRIPTION: 2024/12/22: Renamed existing tag.bat to tag-pictures.bat because these days picture tagging is not our primary tagging activity! 
:DESCRIPTION:  Instead want a more dynamic tag.bat that reacts to what folder we are in



set         CURRENT_FOLDER_ROOT_FIRST_3_LETTERS=%@RIGHT[3,%@LEFT[6,%_CWD]]
set NATURE=%CURRENT_FOLDER_ROOT_FIRST_3_LETTERS%


rem DEBUG: echo DEBUG: %_CWd %mp3official CURRENT_FOLDER_ROOT_FIRST_3_LETTERS=%CURRENT_FOLDER_ROOT_FIRST_3_LETTERS


iff "MP3" == "%NATURE%" then
        call tag-mp3s.bat
else        
        call advice "Did you mean tag-pictures.bat?"
endiff        

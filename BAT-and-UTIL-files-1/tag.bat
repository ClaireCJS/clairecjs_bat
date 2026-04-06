@Echo OFF
 echo.

 
:DESCRIPTION: 2024/12/22: Renamed existing tag.bat to tag-pictures.bat because these days picture tagging is not our primary tagging activity! 
:DESCRIPTION:  Instead want a more dynamic tag.bat that reacts to what folder we are in


rem Determine the nature of the folder that we are in:
        set         CURRENT_FOLDER_ROOT_FIRST_3_LETTERS=%@RIGHT[3,%@LEFT[6,%_CWD]]
        set NATURE=%CURRENT_FOLDER_ROOT_FIRST_3_LETTERS%

        if "1" == "%@REGEX[NEWPICS,%@UPPER[%_CWD]]" set NATURE=PICS
        if "1" == "%@REGEX[WWWPICS,%@UPPER[%_CWD]]" set NATURE=PICS
        rem DEBUG: echo DEBUG: %_CWd %mp3official CURRENT_FOLDER_ROOT_FIRST_3_LETTERS=%CURRENT_FOLDER_ROOT_FIRST_3_LETTERS


rem Present a menu of which ways to tag, unless we have determined a nature that we have custom behavior for:
        iff      "MP3"  == "%NATURE%" then
                call tag-mp3s.bat
        else iff "PICS" == "%NATURE%" then
                call tag-pictures.bat
        else        
                call AskYN "Did you mean tag-%ansi_color_bright_green%P%ansi_color_prompt%ictures or tag-%ansi_color_bright_green%M%ansi_color_prompt%usic/%ansi_color_bright_green%N%ansi_color_prompt%either/%ansi_color_bright_green%Q%ansi_color_prompt%uit?" 0 0 PMNQ P:tag-pictures,M:tag-music,N:neither,Q:quit
                if  "P" == "%ANSWER%" call tag-pictures
                if  "M" == "%ANSWER%" call tag-mp3s
                rem "N" == pass
                rem "Q" == pass
        endiff        


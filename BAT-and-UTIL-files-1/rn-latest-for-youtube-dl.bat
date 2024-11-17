@Echo OFF

set YOUTUBE_ID_LENGTH=10

::::: MAKE SURE THE FILE WE WANT TO RENAME ACTUALLY EXISTS:
	set LATEST_FILENAME="%@EXECSTR[d/odt/b|:u8grep -v \.description|:u8tail -1]"
	call validate-environment-variable LATEST_FILENAME


::::: SUCK OUT THE YOUTUBE ID AND FIX IT UP THE WAY WE WANT:
	set BASE_NAME=%@NAME[%LATEST_FILENAME%]
	set BASE_NAME_LENGTH=%@LEN[%BASE_NAME%]
	set TEXT_DESCRIPTION_FILE_NAME=%BASE_NAME%.description
	set JSON_DESCRIPTION_FILE_NAME=%BASE_NAME%.json
	set START_POS=%@EVAL[%BASE_NAME_LENGTH% - %YOUTUBE_ID_LENGTH% - 1]
	set YOUTUBE_ID=%@INSTR[%@EVAL[%START_POS% - 1],%@EVAL[%YOUTUBE_ID_LENGTH% + 1],%BASE_NAME%]
	set FIXED_BASENAME=%@REPLACE[ [%YOUTUBE_ID%], (youtube-rip) (%YOUTUBE_ID),%BASE_NAME]
	set FIXED_FILENAME="%FIXED_BASENAME%.%@EXT[%LATEST_FILENAME]"

::::: DEBUG:
	%COLOR_DEBUG%
    echo * base name length is....%BASE_NAME_LENGTH%
    echo * start position is......%START_POS%
    echo * YouTube id is..........%YOUTUBE_ID%
    echo * fixed basename is......%FIXED_BASENAME%
    echo * fixed filename is......%FIXED_FILENAME%
    echos * TEXT description filename is......%TEXT_DESCRIPTION_FILE_NAME%
        color yellow on black %+ echos ...
        if     exist "%TEXT_DESCRIPTION_FILE_NAME%" (%COLOR_SUCCESS% %+ echo and exists!        )
        if not exist "%TEXT_DESCRIPTION_FILE_NAME%" (%COLOR_ERROR%   %+ echo and does not exist!)
    %COLOR_SUBTLE% 
    echos * JSON description filename is......%JSON_DESCRIPTION_FILE_NAME%
        echos ...
        if     exist "%JSON_DESCRIPTION_FILE_NAME%" (%COLOR_SUCCESS% %+ echo and exists!                                                                   )
        if not exist "%JSON_DESCRIPTION_FILE_NAME%" (%COLOR_SUCCESS% %+ echo and does not exist but that is okay because we don't fetch it until afterward!)

::::: RENAME THE FILE AND MAKED SURE WE WERE SUCCESSFUL:
	%COLOR_RUN%
	ren %LATEST_FILENAME% %FIXED_FILENAME%
	call validate-environment-variable FIXED_FILENAME

::::: LET THE USER FIX UP THE FILENAME EVEN MORE, IF WE AREN'T RUNNING IN UNATTENDED MODE:
    %COLOR_RUN%
	if "%UNATTENDED_YOUTUBE_DOWNLOADS%" eq "1" goto :Unattended        
		call rn %FIXED_FILENAME%
        :^this has a side-effect of setting %FILENAME_NEW% to the newest filename
        if exist "%JSON_DESCRIPTION_FILE_NAME%" (set JSON_DESCRIPTION_NAME_NEWEST=%@NAME[%FILENAME_NEW].json %+ %COLOR_SUBTLE% %+ ren "%JSON_DESCRIPTION_FILE_NAME%" "%JSON_DESCRIPTION_NAME_NEWEST%" %+ %COLOR_SUBTLE %+ echo "%JSON_DESCRIPTION_NAME_NEWEST%" saved %+ %COLOR_NORMAL% %+ echo.)
        if exist "%TEXT_DESCRIPTION_FILE_NAME%" (set TEXT_DESCRIPTION_NAME_NEWEST=%@NAME[%FILENAME_NEW].txt  %+ %COLOR_SUBTLE% %+ ren "%TEXT_DESCRIPTION_FILE_NAME%" "%TEXT_DESCRIPTION_NAME_NEWEST%" %+ %COLOR_SUBTLE %+ type "%TEXT_DESCRIPTION_NAME_NEWEST%"       %+ %COLOR_NORMAL% %+ echo.)
	:Unattended

:END
    %COLOR_NORMAL%
    
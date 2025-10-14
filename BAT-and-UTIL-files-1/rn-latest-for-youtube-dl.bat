@Echo OFF
@loadBTM ON
set filemask=%1
@on break cancel

rem CONFIGURATION:
        set YOUTUBE_ID_LENGTH=10
        set DEBUG_RNLATESTFORYOUTUBE=0

rem DEBUG:
        if "0" != "%DEBUG_RNLATESTFORYOUTUBE%" @echo %ansi_color_bright_green%-—━━━━━━━━━━━━━━━RN-LATEST-FOR-YOUTUBE.BAT: START: “rn-latest-for-youtube %1$” -—━━━━━━━━━━━━━━━ filemask=“%filemask%”%ansi_color_normal% %+ rem pause

rem VALIDATE ENVIRONMENT (once):
        iff "1" != "%validated_rnlatestforyoutubedl%" then
                call validate-in-path rn pause-for-x-seconds
                call validate-environment-variable ansi_color_has_been_set
                set  validated_rnlatestforyoutubedl=1
        endiff

rem MAKE SURE THE FILE WE WANT TO RENAME ACTUALLY EXISTS:
        unset /q LATEST_FILENAME_NOT_COUNTING_METADATA_FILES
	set LATEST_FILENAME_NOT_COUNTING_METADATA_FILES="%@EXECSTR[d/odt/b %FILEMASK%|:u8grep -v \.description|:u8grep -v \.webp|:u8grep -v \.json|:u8tail -1]"
        if "0" != "%DEBUG_RNLATESTFORYOUTUBE%" call debug   "LATEST_FILENAME_NOT_COUNTING_METADATA_FILES is “%LATEST_FILENAME_NOT_COUNTING_METADATA_FILES%”"
        rem pause
	call validate-environment-variable LATEST_FILENAME_NOT_COUNTING_METADATA_FILES


rem SUCK OUT THE YOUTUBE ID AND FIX IT UP THE WAY WE WANT:
	set BASE_NAME=%@NAME[%LATEST_FILENAME_NOT_COUNTING_METADATA_FILES%]
	set BASE_NAME_LENGTH=%@LEN[%BASE_NAME%]
	set TEXT_DESCRIPTION_FILE_NAME=%BASE_NAME%.description
	set JSON_DESCRIPTION_FILE_NAME=%BASE_NAME%.json
	set START_POS=%@EVAL[%BASE_NAME_LENGTH% - %YOUTUBE_ID_LENGTH% - 1]
	set YOUTUBE_ID=%@INSTR[%@EVAL[%START_POS% - 1],%@EVAL[%YOUTUBE_ID_LENGTH% + 1],%BASE_NAME%]
	set FIXED_BASENAME=%@REPLACE[ [%YOUTUBE_ID%], (youtube-rip) (%YOUTUBE_ID),%BASE_NAME]
	set FIXED_FILENAME="%FIXED_BASENAME%.%@EXT[%LATEST_FILENAME_NOT_COUNTING_METADATA_FILES]"

rem DEBUG:
        if "0" == "%DEBUG_RNLATESTFORYOUTUBE" goto :Skip_Debug
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
        :Skip_Debug

rem RENAME THE FILE AND MAKED SURE WE WERE SUCCESSFUL:
	%COLOR_RUN%
	if "0" != "%DEBUG_RNLATESTFORYOUTUBE%" echo %ANSI_COLOR_DEBUG%- DEBUG: We do this: “%faint_on%ren %LATEST_FILENAME_NOT_COUNTING_METADATA_FILES% %FIXED_FILENAME%%faint_off%”
	ren %LATEST_FILENAME_NOT_COUNTING_METADATA_FILES% %FIXED_FILENAME%
	if not exist %FIXED_FILENAME% call validate-environment-variable FIXED_FILENAME
	if "0" != "%DEBUG_RNLATESTFORYOUTUBE%" echo %ANSI_COLOR_DEBUG%- DEBUG: But maybe we also need to do this: “%faint_on%ren "%BASE_NAME%.*" "%FIXED_BASENAME%.*"%faint_off%”
        rem pause
        %color_run%
        if exist "%BASE_NAME%.*"  ren "%BASE_NAME%.*" "%FIXED_BASENAME%.*
        %color_normal%
        rem echo %Ansi_color_warning%%EMOJI_QUESTION_MARK% did it work? %ansi_color_normal% %+ call pause-for-x-seconds 5 %+ dir /odt %+ call pause-for-x-seconds 5


rem LET THE USER FIX UP THE FILENAME EVEN MORE, IF WE AREN'T RUNNING IN UNATTENDED MODE:
        %COLOR_RUN%
	if "%UNATTENDED_YOUTUBE_DOWNLOADS%" eq "1" goto :Unattended        
		call rn %FIXED_FILENAME%
                rem this has a side-effect of setting %FILENAME_NEW% to the newest filename
                if exist "%JSON_DESCRIPTION_FILE_NAME%" (set JSON_DESCRIPTION_NAME_NEWEST=%@NAME[%FILENAME_NEW].json %+ %COLOR_SUBTLE% %+ ren "%JSON_DESCRIPTION_FILE_NAME%" "%JSON_DESCRIPTION_NAME_NEWEST%" %+ %COLOR_SUBTLE %+ echo "%JSON_DESCRIPTION_NAME_NEWEST%" saved %+ %COLOR_NORMAL% %+ echo.)
                if exist "%TEXT_DESCRIPTION_FILE_NAME%" (set TEXT_DESCRIPTION_NAME_NEWEST=%@NAME[%FILENAME_NEW].txt  %+ %COLOR_SUBTLE% %+ ren "%TEXT_DESCRIPTION_FILE_NAME%" "%TEXT_DESCRIPTION_NAME_NEWEST%" %+ %COLOR_SUBTLE %+ type "%TEXT_DESCRIPTION_NAME_NEWEST%"       %+ %COLOR_NORMAL% %+ echo.)
	:Unattended

:END


   %COLOR_NORMAL%
    
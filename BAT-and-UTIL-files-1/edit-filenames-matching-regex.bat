@Echo Off
 on break cancel

:DESCRIPTION:    Open all files matching a regular expression in the default text editor
:USAGE:          %0 "someRegex"    *.txt  {defaults to *.bat if no file is specified}
:USAGE:      EX: %0 sleep.*[0-9]          {edits all BAT files with "sleep" followed by a digit}

rem USAGE:
        iff "%1" eq "" then
                @echo off
                %color_advice%
                echo DESCRIPTION: Open all files matching a regular expression in the default text editor
                echo USAGE:           %0   "someRegex"    *.txt  {defaults to *.bat if no file is specified}
                echo USAGE:       EX: %0   sleep.*[0-9]          {edits all BAT files with "sleep" followed by a digit}
                goto :END
        endiff

rem ENVIRONMENT VALIDATION:
        call validate-in-path               checkeditor grep fixtmp insert-before-each-line.pl echos editor-slow divider
        call                                checkeditor

rem CONFIGURATION:
        set FILESTOGREP_DEFAULT=*.bat
        set NOKEY=1
            rem ^^^Set NOKEY to 0 to     make user pause before running %0 script
            rem ^^^Set NOKEY to 1 to NOT make user pause before running %0 script

rem VALIDATE PARAMETERS & ENVIRONMENT:
        set  REGEX=%1
        if "%REGEX%" eq "" .or. "%1" eq "" (goto :ERROR_NoParameter1)
        set                     FILESTOGREP=%FILESTOGREP_DEFAULT%
        if "%2"      ne "" (set FILESTOGREP=%2)
        if "%2"      eq "" (call validate-environment-variables FILEMASK_CODE FILEMASK_TEXT)


rem SET UP INTERNAL VARIABLES AND FILENAMES:
        call fixtmp
        set FILELIST=%TMP%\delmeGrepEditFileList.txt
        set  BATFILE=%TMP%\delmeGrepEditFileList.bat


rem GREP FOR OUR LIST OF MATCHING FILES, WHICH ARE SAVED TO A FILELIST:
        call less_important "Searching files “%italics_on%%FILESTOGREP%%italics_off%” for regex “%italics_on%%REGEX%%italics_off%”"
                                          >:u8%FILELIST%
        grep -i -l %REGEX% %FilesToGrep% >>:u8%FILELIST% 



rem INITIALIZE OUTPUT SCRIPT:
        echo @Echo OFF   >:u8%BATFILE%

rem CONVERT THE FILELIST INTO A BAT FILE WHICH WILL TEXT-EDIT ALL THE MATCHED FILES:
        rem The OLD way calling %EDITOR% directly; the new way calls editor-slow.bat which delays between each file open:
        rem OLD: fore-each-line.pl "%%%%EDITOR%%%% "   <%FILELIST%    >>%BATFILE%
        insert-before-each-line.pl "call editor-slow " <%FILELIST% >>:u8%BATFILE%



rem PREVIEW THE GENERATED SCRIPT, SO USER CAN BE SURE THEY ACTUALLY WANT TO RUN IT:
        call less_important "About to run:
        call divider
        %color_run%
        type %BATFILE%	
        call divider
		echo.
        if "%NOKEY%" eq "1" goto :KEY_NO
		call pause-alias "Press any key to run above script..."
   	    :KEY_NO

rem THEN RUN IT!
	call %BATFILE%

rem WHEN DONE, COPY OUR REGEX TO THE CLIPBOARD SO WE CAN SEARCH IN THE FILES JUST OPENE:
	echos %REGEX%>:u8clip:	




:###########################################################################################################################################################################
goto :END

	:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
	:ERROR_NoParameter1
            call error "First parameter must be a regular expression to pass to grep!"
            gosub usage
	goto :END
	:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

	::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
	:ERROR_NoParameter2
            call error "Second parameter must be a wildcard to grep against!"
            gosub usage
	goto :END
	::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

	:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
	:usage
            %COLOR_ADVICE%
            echo USAGE: grepEdit someRegex [optional wildcard like *.java; default is “%FILESTOGREP_DEFAULT%”]
	return
	:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

:###########################################################################################################################################################################

:END

rem Whatever we are looking for, now is a time to have it in our clipboard, so that we
rem can do Ctrl-F, Ctrl-V to find it in the bat files, and not have to type it again:
    call fixclip
    echo %FILESTOGREP >:u8clip:

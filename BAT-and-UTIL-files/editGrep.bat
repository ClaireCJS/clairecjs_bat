@Echo On

::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::::: PURPOSE: Load into text editor all files that match a grep'ed regular expression ::::: 
:::::   USAGE: grepEdit someRegex *.txt                                                ::::: 
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

::::: ENVIRONMENT VALIDATION:
    call validate-environment-variables FILEMASK_CODE FILEMASK_TEXT

::::: CONFIGURATION:
	set FILESTOGREP=*.bat
	set NOKEY=1
		:^Set to 0 to     make user pause before running editgrep script
		:^Set to 1 to NOT make user pause before running editgrep script

::::: VALIDATE PARAMETERS & ENVIRONMENT:
	set  REGEX=%1
	if "%REGEX%" eq "" goto :ERROR_NoParameter1
	if "%1"      eq "" goto :ERROR_NoParameter1
	if "%2"      ne "" set FILESTOGREP=%2
	call checkeditor


::::: SET UP INTERNAL VARIABLES:
	call fixtmp
	set FILELIST=%TMP%\delmeGrepEditFileList.txt
	set  BATFILE=%TMP%\delmeGrepEditFileList.bat


::::: GREP FOR OUR LIST OF MATCHING FILES, WHICH ARE SAVED TO A FILELIST:
                                      >%FILELIST%
	grep -i -l %REGEX% %FilesToGrep% >>%FILELIST% 


::::: CONVERT THE FILELIST INTO A BAT FILE WHICH WILL TEXT-EDIT ALL THE MATCHED FILES:
	insert-before-each-line "%%%%EDITOR%%%% " <%FILELIST% >%BATFILE%

	:may have to splice a delay in between each file of editplus does that annoying multiple-instances-when-loading-too-many-files-at-once thig


::::: PREVIEW THE GENERATED SCRIPT, SO USER CAN BE SURE THEY ACTUALLY WANT TO RUN IT:
		echo.
		echo.
		echo.
	type %BATFILE%	
		echo.
	if "%NOKEY%" eq "1" goto :KEY_NO
		echo Press any key to run above script...
			pause>nul
	:KEY_NO

::::: THEN RUN IT!
	call %BATFILE%

::::: WHEN DONE, COPY OUR REGEX TO THE CLIPBOARD SO WE CAN SEARCH IN THE FILES JUST OPENE:
	echos %REGEX%>clip:	




:###########################################################################################################################################################################
goto :END

	:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
	:ERROR_NoParameter1
		echo ERROR: First parameter must be a regular expression to pass to grep!
		gosub usage
	goto :END
	:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

	::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
	:ERROR_NoParameter2
		echo ERROR: Second parameter must be a wildcard to grep against!
		gosub usage
	goto :END
	::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

	:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
	:usage
		echo USAGE: grepEdit someRegex [optional wildcard like *.java; default is '*']
	return
	:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

:###########################################################################################################################################################################

:END

::::: Whatever we are looking for, now is a time to have it in our clipboard, so that we
::::: can do Ctrl-F, Ctrl-V to find it in the bat files, and not have to type it again:
    call fixclip
    echo %FILESTOGREP >clip:

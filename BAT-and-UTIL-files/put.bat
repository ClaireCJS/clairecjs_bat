@Echo off

::::: CONFIGURATION:
	SET CONFIRM=1
    SET MOVE_FOLDER=move /a: /ds /g /h /e
    SET MOVE_FILE=  move /a:     /g /h

::::: SETUP:
	call fixclip


::::: ERROR CHECK:
    set SOURCE=%1
    SET TARGET=%2
    if     "" eq "%2" goto :NoArg2
    if not isdir  %2  goto :NoExistArg2
	if     isdir  %1  goto :isdir
	if     exist  %1  goto :isfile
		:undefined
            %COLOR_WARNING% %+ echo Behaviour for this parameter is undefined.
			                   echo So far, this only works on folders. So "%1" would have to be a folder.
		goto :END
        :NoArg2
            %COLOR_WARNING% %+ echo Must pass 2 arguments. 2nd must be destination folder.
        goto :END
        :NoExistArg2
            %COLOR_WARNING% %+ echo Destination folder of %2 must exist.
        goto :END



::::: DETERMINE THE NAME:
	:isdir
    %COLOR_DEBUG%
        echo.
        echo * %1 is a directory.
        echo.
        echo.
        echo.
    %COLOR_NORMAL%
    SET MOVE_COMMAND=%MOVE_FOLDER%
    goto :File_Or_Folder_Determination_DONE

    :isfile
        echo * %1 is a file.
        SET MOVE_COMMAND=%MOVE_FILE%
        goto :File_Or_Folder_Determination_DONE


    :File_Or_Folder_Determination_DONE
        SET TARGETDIR=%SOURCE%
        set TARGETDIRTEMP=%@EXECSTR[grab-helper.pl %SOURCE%]
        if "%TARGETDIRTEMP%" ne "" (set TARGETDIR=%TARGETDIRTEMP%)
        %COLOR_PROMPT%  %+echos  *** Edit target folder's name to your heart's content: *** ``
        %COLOR_SUCCESS% %+ echo.
        eset TARGETDIR  
        %COLOR_NORMAL%

::::: ENSURE TARGET DOESN'T ALREADY EXIST:
if isdir "%TARGET" goto :TargetExists_YES
                   goto :TargetExists_NO
	:TargetExists_NO
		echo. %+ echo. %+ echo. %+ %COLOR_NORMAL%
		dir "%TARGET"
        %COLOR_WARNING% %+ echo. %+ echo * Oops! Target %TARGET% does not exist! Not sure what to do.
		goto :END
	:TargetExists_YES

::::: MOVE IT:
	set TARGETNOQUOTES=%@STRIP[%=",%TARGET]
    set     UNDOCOMMAND=%MOVE_COMMAND% "%TARGETNOQUOTES%\%TARGETDIR%"  %SOURCE% 
    set     REDOCOMMAND=%MOVE_COMMAND%  %SOURCE%  "%TARGETNOQUOTES%\%TARGETDIR%"
    %COLOR_DEBUG% %+  echo. %+ echo. %+ echo * Ready to: %REDOCOMMAND% %+ %COLOR_NORMAL%
	if "%CONFIRM%" eq "1" .or. "%DEBUG%" eq "1" (%COLOR_IMPORTANT% %+ pause)
    %COLOR_SUCCESS%
	echo y|%REDOCOMMAND% | copy-move-post
    %COLOR_NORMAL%

::::: ENSURE ORIGINAL SOURCE IS GONE, IF NOT, TRY AGAIN AND/OR WARN:
    dir "%TARGETNOQUOTES%\%TARGETDIR%"
	if isdir %SOURCE (rmdir %SOURCE)
	if isdir %SOURCE (if exist "%SOURCENOQUOTES\Thumbs.db" (*del /z "%SOURCE\thumbs.db"))
	if isdir %SOURCE (rmdir %SOURCE)
	if isdir %SOURCE (%COLOR_WARNING% %+ echo WARNING: %1 still exists -- rmdir "%1" failed %+ %COLOR_NORMAL%)
	goto :END




:END
	unset /q CONFIRM
    %COLOR_NORMAL%
    dir "%TARGETNOQUOTES%\%TARGETDIR%" | highlight %TARGETDIR%


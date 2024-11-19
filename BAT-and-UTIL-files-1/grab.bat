@on break cancel
@Echo off

::::: SETUP:
	SET CONFIRM=1
	call fixclip


::::: ERROR CHECK:
	if isdir "%1" goto :isdir
	              goto :undefined
		:undefined
			echo Behaviour for this parameter is undefined.
			echo So far, this only works on folders. So "%1" would have to be a folder.
		goto :END


::::: DETERMINE THE NAME:
	:isdir
    %COLOR_DEBUG%
    echo.
    echo.
	echo * %1 is a directory.
    echo.
    echo.
    echo.
    echo.
	echo off
	set  TARGET=%@EXECSTR[grab-helper.pl %1]
    if "%TARGET%" eq "" set TARGET=.
    %COLOR_PROMPT%  %+ echos  *** Edit target folder's name to your heart's content: *** `` %+ %COLOR_NORMAL% %+ echo. 
    %COLOR_INPUT%   %+ eset TARGET
    %COLOR_NORMAL%

::::: ENSURE TARGET DOESN'T ALREADY EXIST:
if isdir "%TARGET" goto :TargetExists_YES
                   goto :TargetExists_NO
	:TargetExists_YES
		echo.
		echo.
		echo.
		dir "%TARGET"
		echo.
        %COLOR_WARNING%
		echo * Oops! Target %TARGET already exists (see above)! So let's NOT do this:
        %COLOR_ADVICE%
		echo move "%1" "%TARGET"
        %COLOR_NORMAL%
		goto :END
	:TargetExists_NO

::::: MOVE IT:
	set SOURCE=%1
	set SOURCENOQUOTES=%@STRIP[%=",%SOURCE]
    %COLOR_DEBUG%
    echo.
    set     UNDOCOMMAND=move /a: /ds /g /h /e "%TARGET" %SOURCE% 
    set     REDOCOMMAND=move /a: /ds /g /h /e %SOURCE% "%TARGET"
	echo * Ready to: %REDOCOMMAND%
    %COLOR_IMPORTANT%
	if "%CONFIRM"=="1" pause
    %COLOR_SUCCESS%
	echo y|%REDOCOMMAND%
    %COLOR_NORMAL%

::::: ENSURE ORIGINAL SOURCE IS GONE, IF NOT, TRY AGAIN AND/OR WARN:
	if isdir %SOURCE rmdir %SOURCE
	if isdir %SOURCE if exist "%SOURCENOQUOTES\Thumbs.db" (*del /z "%SOURCE\thumbs.db")
	if isdir %SOURCE rmdir %SOURCE
	if isdir %SOURCE echo WARNING: %1 still exists -- rmdir "%1" failed
	goto :END




:END
	unset /q CONFIRM
    dir |:u8 highlight %TARGET%

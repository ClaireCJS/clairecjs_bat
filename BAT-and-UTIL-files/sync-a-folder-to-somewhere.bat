@echo OFF
pushd


::: INVOCATION PATTERN:
	:@Echo OFF
	:set   SYNCSOURCE=%UTIL%
	:set   SYNCTARGET=%DROPBOX%\BACKUPS\UTIL
	:set   SYNCTRIGER="__ last synced to dropbox __"   (set to NONE to suppress this)
	:call  sync-a-folder-to-somewhere.bat test [ZIP] -- adding "ZIP" afterwards makes it a zip instead of a full copy, but the -FS option doesn't work as well as it should, sucks, and this is best for only very tiny things
	:rem   Remember to call this bat file from sync-dropbox.bat
	:if exist %BAT\%0% %EDITOR% %BAT\%0





:CheckForInvocationErrors
    ::::: VALIDATE INVOCATION GIVEN:
        if "%SYNCSOURCE%" eq "" goto :NoSyncSource
        if "%SYNCTARGET%" eq "" goto :NoSyncTarget
        if "%SYNCTRIGER%" eq "" goto :NoSyncTriger

    ::::: VALIDATE INVOCATION ACCURATE:
        if not isdir  %SYNCSOURCE% (call FATAL_ERROR "SYNCTARGET of '%italics_on%%syncsource%%italics_off%' must exist!" %+ goto :END) 
        if not isdir  %SYNCTARGET% (call FATAL_ERROR "SYNCTARGET of '%italics_on%%synctarget%%italics_off%' must exist!" %+ goto :END) 
        if not defined SYNCTRIGER  (call FATAL_ERROR "SYNCTRIGER (yes spelled that way) must be defined!"                %+ goto :END) 
        call validate-environment-variables SYNCSOURCE SYNCTARGET 

:CaptureParameters
    :ZippingOrNot
                                  set ZIP=0
        if "%@UPPER[%1]" eq "ZIP" set ZIP=1

    :: SUPPRESS ZIP FUNCTIONALITY BECAUSE INFOZIP SUCKS!
    :: WHAT DID I GET MYSELF INTO? IT DOESN'T WORK RIGHT!
    :SET ZIP=0

    :AdjustForTesting
                                 set    TESTING=0
        if "%1" eq  "test"       set    TESTING=1
        if "%1" eq  "testing"    set    TESTING=1
        if  "1" eq "%TESTING%"   set    TESTING=1
                               unset /q OPTIONS
        if  "1" eq "%TESTING%"   set    OPTIONS=/N



:Determine_Command_To_Use
    ::::: LOGGING:
        echo. %+ title %SYNCSOURCE% to %SYNCTARGET%
        set TARGETNAME=%@NAME[%SYNCTARGET%]

    ::::: DETERMINE COMMAND TO USE FOR COPY BACKUPS:
        :adding /e is controversial - no error messages!
        set REDOCOMMAND=*copy /e /w /u /s /r /a: /h /z /k /g /Nt %OPTIONS% %* "%@UNQUOTE[%SYNCSOURCE%]" "%@UNQUOTE[%SYNCTARGET%]"

    ::::: DETERMINE COMMAND TO USE FOR ZIP BACKUPS:
        if "0" eq "%ZIP%" goto :NotZipping
            :: get cygwin's zip.exe either from cygwin-install or Claire-install
                                    set ZIPPER=call zip.bat
                :f "%CYGWIN%" eq "" set ZIPPER=%UTIL%\infozip.exe
                if "%CYGWIN%" eq "" set ZIPPER=%UTIL%\wzzip.exe

            :: determine target zip base name
                set ZIPBASEDIR=%@UNQUOTE[%SYNCTARGET%]
                set ZIPBASENAME=%@name[%syncsource%]
                set ZIPFULLNAME=%@REPLACE[\\,\,%ZIPBASEDIR%\%ZIPBASENAME%.zip]
                set ZIPFULLNAMEBUG=%@REPLACE[\\,\,%ZIPBASEDIR%\1.zip]

            :: 7-zip stuff
                set ZIPPER=7z
                set ADD=a
                set UPDATE=u
                set RECURSE=-r
                set EXCLUDE=-x!

                ::::: 2010-2019
                :                              set REDOCOMMAND=%ZIPPER% "%ZIPFULLNAME%" -FS -r "%@UNQUOTE[%SYNCSOURCE%]\"
                :if not exist "%ZIPFULLNAME%" (set REDOCOMMAND=%ZIPPER% "%ZIPFULLNAME%"     -r "%@UNQUOTE[%SYNCSOURCE%]\")
                ::::: 202005
                set REDOCOMMAND=%ZIPPER% %UPDATE% "%ZIPFULLNAME%" %RECURSE% "%@UNQUOTE[%SYNCSOURCE%]\" 

                set LAST_REDOCOMMAND=%REDOCOMMAND%

            :: store it for diagnostic purposes
                set ZIP_COMMAND_%ZIPBASENAME=%REDOCOMMAND%
                set LAST_ZIP_COMMAND_%ZIPBASENAME=%[ZIP_COMMAND_%ZIPBASENAME%]

            :: debug
                %COLOR_DEBUG%
                echo SYNCSOURCE    =[%SYNCSOURCE%]  
                echo REDOCOMMAND   =[%REDOCOMMAND%]  
                echo ZIPBASEDIR    =[%ZIPBASEDIR%]  
                echo ZIPBASENAME   =[%ZIPBASENAME%] 
                echo ZIPFULLNAME   =[%ZIPFULLNAME%] 
                echo ZIPFULLNAMEBUG=[%ZIPFULLNAMEBUG%] 
                pause
        :NotZipping

:Let_user_know_what_we_are_going_to_do
                                 set NEWLINE_REPLACEMENT=0 %+ call important_less "%blink_on%Syncing:%blink_off% SOURCE = %italics_on%%SYNCSOURCE%%italics_off%"
                                 set NEWLINE_REPLACEMENT=0 %+ call important_less "%blink_on%Syncing:%blink_off% TARGET = %italics_on%%SYNCTARGET%%italics_off%"
    rem if "%TARGETNAME%" ne "" (set NEWLINE_REPLACEMENT=0 %+ call important_less "   Name: %italics_on%%TARGETNAME%%italics_off%") —— forget why I was displaying this, but it seems pointless now [2024/05/09]
                                 set NEWLINE_REPLACEMENT=0 %+ call important_less "Command: %italics_on%%REDOCOMMAND%%italics_off%"
    %COLOR_NORMAL%    
    echo.

:Do_It
    %COLOR_RUN%
    REM actually do the copy here! fast_cat is the fastest version of cat.exe {after testing}, which is used to fix ANSI rendering problems
    rem RIGHT WAY BUT ARGH: echo rayrayray |:u8 %REDOCOMMAND% |:u8 copy-move-post
    rem WRONG WAY BUT WORKS:
    rem echo rayrayray |:u8 *copy /e /w /u /s /r /a: /h /z /k /g /Nt "%@UNQUOTE[%SYNCSOURCE%]" "%@UNQUOTE[%SYNCTARGET%]" |:u8 copy-move-post
    (echo rayrayray | *copy /e /w /u /s /r /a: /h /z /k /g /Nt "%@UNQUOTE[%SYNCSOURCE%]" "%@UNQUOTE[%SYNCTARGET%]") |:u8 copy-move-post
    if exist "%ZIPFULLNAMEBUG%" (%COLOR_WARNING% %+ mv "%ZIPFULLNAMEBUG%" "%ZIPFULLNAME%")
    set LASTCOMMAND=%REDOCOMMAND%
    title Sync done.
    %COLOR_SUCCESS%  

:FlagLastSync
    if "%@UPPER[%SYNCTRIGER%]" eq "NONE" goto :NoFlag
        set TRIGGER="%@UNQUOTE[%SYNCSOURCE%\%SYNCTRIGER%]"
        %COLOR_DEBUG% %+ echo	     ``>%TRIGGER%
        %COLOR_NORMAL %+               >%TRIGGER%
        echo SYNC_SOURCE=%SYNCSOURCE% >>%TRIGGER%
        echo SYNC_TARGET=%SYNCTARGET% >>%TRIGGER%
        echo        TIME=%_DATETIME   >>%TRIGGER%

        set TRIGGER="%@UNQUOTE[%SYNCTARGET%\%SYNCTRIGER%]"
        %COLOR_DEBUG% %+ echo	     ``>%TRIGGER%
        %COLOR_NORMAL %+               >%TRIGGER%
        echo SYNC_SOURCE=%SYNCSOURCE% >>%TRIGGER%
        echo SYNC_TARGET=%SYNCTARGET% >>%TRIGGER%
        echo        TIME=%_DATETIME   >>%TRIGGER%
:NoFlag

    goto :END


::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
    ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
		:NoSyncSource   
			call fatal_error "SYNCSOURCE environment variable not defined"
		goto :END

		:NoSyncTarget   
			call fatal_error "SYNCTARGET environment variable not defined"
		goto :END

		:NoSyncTriger
			call fatal_error "SYNCTRIGER environment variable not defined. (Yes, one 'g' in 'TRIGER'. I have reasons.)"
		goto :END
    ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::





:END

popd
call display-free-space %SYNCTARGET%
rem set DISKFREE=%@COMMA[%@EVAL[%@DISKFREE[%SYNCTARGET%]/1024/1024/1024]]
rem call important "Free space now %DISKFREE%"

if %@DISKFREE[%SYNCTARGET%] lt 150000000 (set NEWLINE_REPLACEMENT=0 %+ repeat 3 (beep 60 25 %+ beep 800 3) %+ call WARNING "Not much free space left on %SYNCTARGET%!" %+ call pause-for-x-seconds 3000 )

unset /q ZIP
%COLOR_NORMAL%
echo.

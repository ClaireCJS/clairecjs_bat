@Echo Off
call checkeditor

set HANDLES=c:\recycler\handles-%_DATETIME-%PID.txt

if exist %1 goto :FilenameGiven

goto %OS

:95
:98
:ME
:NT
:2K
:XP

	(handle.exe | handles-post.pl) >%HANDLES%
	goto :EDIT

:7
:10
if "%_admin" == "0" goto :7NotAdmin
	:else:
		goto :XP

	:7NotAdmin
		if "%1" eq "" goto :Arg_NO
			      goto :Arg_YES
			:Arg_YES
				(runas /profile /user:%MACHINENAME\Administrator    handle.exe | handles-post.pl ) >%HANDLES%
				goto :DoneWith7
			:Arg_NO
				 runas /profile /user:%MACHINENAME\Administrator    handle.exe | handles-post.pl | gr %1
				goto :DoneWith7
		:DoneWith7
	goto :EDIT

    :EDIT
        %EDITOR     %HANDLES%
    goto :END

    :FilenameGiven
        for %1 in (%@FILELOCK[%1]) (%COLOR_WARNING% %+ echos kill /f %1       `` %+ echos %% %+ echos + %+ %COLOR_IMPORTANT% %+ echos    REM Process is:  `` %+ pg %1)
        if  "" eq "%@FILELOCK[%1]" (%COLOR_WARNING% %+ echo * No open filehandles for file %1 %+ %COLOR_NORMAL%)
    goto :END

:END
@Echo off

rem personal note: mchkold is a hard-coded 'mchk' of the pre-2002-crash filelist


:DESCRIPTION: This script checks for MP3s no matter where they might be, and it does so quickly, by looking through our generated index file
:USAGE:       run "mchk index" to regenerate the parts of the index file that can be regenerated quickly (i.e. new/download areas, but not main index)



::::: Define our index file, and the computer it lives on (MASTER):
	set INDEXFILE=%MP3CL%\master-audio-list-including-newstuff.txt
	set INDEXFILE_DROPBOX=%DROPBOX%\media\mp3\lists\everything.m3u
	::2022 REMOVING:: if not exist %INDEXFILE% if exist %INDEXFILE_DROPBOX% set INDEXFILE=%INDEXFILE_DROPBOX%

::::: Define the "everything.m3u" file location, used in step 1:
	set EVERYTHING=%MP3CL\LISTS\everything.m3u

::::: Verify proper steup:
	call validate-environment-variables DROPBOX NEWMP3 MP3CL WAVPROCESSING INDEXFILE EVERYTHING FILEMASK_AUDIO REVIEWDIR INDEXFILE_DROPBOX



:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::::: Generate the index file if asked, or if it doesn't exist, or if it's too old:
::::: But only do this if the EVERYTHING file exists
	if not exist "%EVERYTHING%"   goto :checkindexfile
	if %@EVAL[%@fileage["%INDEXFILE"]-%@fileage["%EVERYTHING"]] lt 0 goto :generateindexfile
	if /i "%1"==        "index"                                      goto :generateindexfile
	if /i "%1"=="generateindex"                                      goto :generateindexfile
	if /i exist "%INDEXFILE"                                         goto :checkindexfile
goto :generateindexfile
goto :theend
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:checkindexfile
	rem 2001-2009: if exist %HD80G2:\mp3-new\filelist.txt gr "%*" %HD80G2:\mp3-new\filelist.txt
    rem 2014:      *grep      -i "%*" "%INDEXFILE"|remap|sort|uniq
    rem 2015: removing remap becuase we now symlink c:\mp3\ and it should just be c:\mp3\ everywhere on a properly-vetted machine

	gr "%*" "%INDEXFILE"|sort -u|sed 's/\//\\\/ig'

goto :theend
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:generateindexfile
	:machineokay
        call important "Generating mchk index file %INDEXFILE"
		call advice    "If this filename isn't in the default mp3 collection then you may need to update mchk.bat"

    set NUM_STEPS=6

	:step1
		call important "Generating index file, Step 1 of %NUM_STEPS%. (everything.m3u/generate-audio-playlists.pl)"
        if not exist "%EVERYTHING" (call error "ERROR #1X!: '%MP3CL%\LISTS\everything.m3u' does not exist!")
        %COLOR_NORMAL%
		    grep -v _PROCESSING "%EVERYTHING%" >"%INDEXFILE"

	:step2
		if isdir %NEWMP3% (call important "Generating index file, Step 2 of %NUM_STEPS%. (%NEWMP3%)")
		if isdir %NEWMP3% (%COLOR_RUN%  %+ dir /b /s /a:-d-h %NEWMP3%\%FILEMASK_AUDIO% >>"%INDEXFILE")

	:::this step3 is no longer necessary because %WAVPROCESSING% has been moved to within %NEWMP3% so it's now automatically caught
	::	if isdir "%WAVPROCESSING%\" (call important "Generating index file, Step 3 of %NUM_STEPS%. (%WAVPROCESSING%)")
	::	if isdir "%WAVPROCESSING%\" dir /b /s /a:-d-h "%WAVPROCESSING%\*.mp3" >>"%INDEXFILE"
	::	if isdir "%WAVPROCESSING%\" dir /b /s /a:-d-h "%WAVPROCESSING%\*.wav" >>"%INDEXFILE"

    :step3
		if isdir "%NEWCL%\music\" (call important "Generating index file, Step 3 of %NUM_STEPS%. (%NEWCL%\music\)")
		if isdir "%NEWCL%\music\" (dir /b /s /a:-d-h %NEWCL%\music\%FILEMASK_AUDIO%  >>"%INDEXFILE")

    :step4
        :we don't use filemask_audio here because this includes downloaded music videos we might want to consider
		if isdir %reviewdir%\"TODO EXTRACT WAV THEN DELETE" (call important "Generating index file, Step 4 of %NUM_STEPS%. (%reviewdir%\"TODO EXTRACT WAV THEN DELETE")")
		if isdir %reviewdir%\"TODO EXTRACT WAV THEN DELETE" (dir /b /s /a:-d-h %reviewdir%\"TODO EXTRACT WAV THEN DELETE" >>"%INDEXFILE")

    :step5
        :we don't use filemask_audio here because this includes downloaded music videos we might want to consider
		if isdir %reviewdir%\"TODO EXTRACT WAV THEN KEEP"   (call important "Generating index file, Step 5 of %NUM_STEPS%. (%reviewdir%\"TODO EXTRACT WAV THEN KEEP")")
		if isdir %reviewdir%\"TODO EXTRACT WAV THEN KEEP"   (dir /b /s /a:-d-h %reviewdir%\"TODO EXTRACT WAV THEN KEEP" >>"%INDEXFILE")

    :step6
        rem in the past, we used to not use filemask_audio here because this includes downloaded music videos we might want to consider, but we changed our mind on that
		if isdir %dropdir%\oh    (call important "Generating index file, Step 6 of %NUM_STEPS%. (%dropdir%\oh\)")
		if isdir %dropdir%\oh    (dir /b /s /a:-d-h %dropdir%\oh\%FILEMASK_AUDIO%  >>"%INDEXFILE")

	:stepsDone
		:Publish_To_Cloud
			%COLOR_RUN% %+ echo yryryr | *copy /r "%EVERYTHING%" "%INDEXFILE_DROPBOX%"

goto :END
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::





::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:END
:theend
	:unset /Q INDEXFILE
    %COLOR_NORMAL%
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

@Echo off
 on break cancel

rem ::: - BACKGROUND: Often times, when we embedded album art into our mp3|flac files, we found ones 
rem :::         on the internet that are of much higher resolution than the cover|folder.jpg|gif|png 
rem :::         files currently residing in the album's folder folder
rem :::	 - So we need to extract these higher resolution versions embedded in the mp3|flac files and
rem :::         overwrite the originals with these, but only if these extracted one are larger in size
rem :::   - "eaa" is the command - extract album art 
rem :::         - this extracts the cover art and overwrites the existing ONLY IF it's a larger file
rem :::	- but when should we run it?
rem :::     - always makes sense to run in a folder that already has a cover|folder.jpg|gif|png 
rem :::	    - always makes sense to run in album folders (which always have filenames starting  w/a #)
rem :::	    - never  makes sense to run in MISC/ONEDIR/COVERS/TRIBUTES/COLLABORATIONS/etc type folders


rem Parameter processing:
        if "%1" ne "FORCE" .and. "%1" ne "TEST" (%COLOR_ERROR% %+ echo *** FATAL ERROR!!! First argument must be 'TEST' or 'FORCE'!! %+ goto :END)
   
rem Debug: 
        %COLOR_IMPORTANT% %+ echos * %_CWP ... %+ %COLOR_DEBUG%


rem Validate environment:
        call validate-environment-variable FILEMASK_AUDIO 
        call validate-in-path extract-cover_art-from-first-found-audio-file.bat run-eaa-in-appropriate-subfolders.bat eaa-if-appropriate-for-workflow.bat eaa.bat extract-cover_art-from-first-found-audio-file.bat fix-wrong-image-extensions wait.bat

rem Figure out when we need to skip the current folder:
                                                                                        set DELFOLDER=0
        if not exist %FILEMASK_AUDIO%                                   (echos  1... %+ set DELFOLDER=1 %+ goto :Do_NOT_DoIt)
        if %@REGEX[\\ALTERNATE-VERSIONS,%_CWD]                eq 1      (echos  2... %+ set DELFOLDER=1 %+ goto :Do_NOT_DoIt)
        if %@REGEX[\\ARCHIVAL-VERSIONS,%_CWD]                 eq 1      (echos  3... %+ set DELFOLDER=1 %+ goto :Do_NOT_DoIt)
        if %@REGEX[\\UNMERGED-VERSIONS,%_CWD]                 eq 1      (echos  4... %+ set DELFOLDER=1 %+ goto :Do_NOT_DoIt)
        if %@REGEX[\\ORIGINAL-UNMERGED-VERSIONS,%_CWD]        eq 1      (echos  5... %+ set DELFOLDER=1 %+ goto :Do_NOT_DoIt)
        if %@REGEX[\\ORIGINAL-VERSIONS,%_CWD]                 eq 1      (echos  6... %+ set DELFOLDER=1 %+ goto :Do_NOT_DoIt)
        if %@REGEX[\\UNPROCESSED-NOISIER-ORIGINALS,%_CWD]     eq 1      (echos  7... %+ set DELFOLDER=1 %+ goto :Do_NOT_DoIt)
        if %@REGEX[\\ONEDIR$,%_CWD]                           eq 1      (echos  8... %+ set DELFOLDER=0 %+ goto :Do_NOT_DoIt)
        if %@REGEX[\\ONEDIR\\,%_CWD]                          eq 1      (echos  9... %+ set DELFOLDER=0 %+ goto :Do_NOT_DoIt)
        if exist "__ this folder is for archival purposes, and has been flagged for exclusion from common playlists __" (echos 10... %+ set DELFOLDER=0 %+ goto :Do_NOT_DoIt)

        if exist  cover.jpg .or. exist  cover.gif .or. exist  cover.png (echos A... %+ goto :DoIt       )
        :f exist folder.jpg .or. exist folder.gif .or. exist folder.png (echos B... %+ goto :DoIt       ) %+ REM changed our mind about folder.jpg as it's slightly different meaning from cover.jpg
        if exist %@REPLACE[*,[0-9]_*,%FILEMASK_AUDIO%]                  (echos C... %+ goto :DoIt       )
        if exist %@REPLACE[*,[0-9][0-9]_*,%FILEMASK_AUDIO%]             (echos D... %+ goto :DoIt       )
        if exist %@REPLACE[*,[0-9][0-9][0-9]_*,%FILEMASK_AUDIO%]        (echos E... %+ goto :DoIt       )
        if %@REGEX[\\MISC\\,%_CWD]                            eq 1      (echos F... %+ goto :Do_NOT_DoIt)
        if %@REGEX[\\MISC$,%_CWD]                             eq 1      (echos G... %+ goto :Do_NOT_DoIt)
        if %@REGEX[\\COVERS\\,%_CWD]                          eq 1      (echos H... %+ goto :Do_NOT_DoIt)
        if %@REGEX[\\COVERS$,%_CWD]                           eq 1      (echos I... %+ goto :Do_NOT_DoIt)
        if %@REGEX[\\TRIBUTES\\,%_CWD]                        eq 1      (echos J... %+ goto :Do_NOT_DoIt)
        if %@REGEX[\\TRIBUTES$,%_CWD]                         eq 1      (echos K... %+ goto :Do_NOT_DoIt)
        if %@REGEX[\\COLLABORATIONS\\,%_CWD]                  eq 1      (echos L... %+ goto :Do_NOT_DoIt)
        if %@REGEX[\\COLLABORATIONS,%_CWD]                    eq 1      (echos M... %+ goto :Do_NOT_DoIt)
        if %@REGEX[\\[12][90][0-9][0-9] \- ,%_CWD]            eq 1      (echos Z... %+ goto :DoIt       ) %+ REM catch-all for albums that have songs without track numbers in the filenames, a rare download situation

rem Then react accordingly:
        :Do_NOT_DoIt
                echos %ANSI_COLOR_ALARM%NOT doing it!%ANSI_RESET%
                if %DELFOLDER% == 1 .and. exist folder.jpg (%COLOR_NORMAL% %+ echo. %+ del /p folder.jpg) 
        goto :END

        :DoIt
                %COLOR_GREP%  %+ echos Doing it!
                %COLOR_REMOVAL%
                if exist folder.jpg .and. not exist cover.jpg (echo %OVERSTRIKE_ON%%ITALICS_ON% %+ ren folder.jpg cover.jpg %+ echo %OVERSTRIKE_OFF%%ITALICS_OFF%)
                if exist folder.gif .and. not exist cover.gif (echo %OVERSTRIKE_ON%%ITALICS_ON% %+ ren folder.gif cover.gif %+ echo %OVERSTRIKE_OFF%%ITALICS_OFF%)
                if exist folder.png .and. not exist cover.png (echo %OVERSTRIKE_ON%%ITALICS_ON% %+ ren folder.png cover.png %+ echo %OVERSTRIKE_OFF%%ITALICS_OFF%)
                if "%1" eq "TEST"                             (                        echo. %+ echo %ANSI_COLOR_WARNING_SOFT%NOT DOING: call extract-cover_art-from-first-found-audio-file%ANSI_RESET% %+ %COLOR_NORMAL% %+ echo. %+ echo. %+ echo %ANSI_RESET% %+ )
                if "%1" ne "TEST"                             (%COLOR_RUN%          %+ echo. %+                                          call extract-cover_art-from-first-found-audio-file             %+ %COLOR_NORMAL% %+ echo. %+ echo. %+ echo %ANSI_RESET% %+ )
        goto :END

:END


rem Also fix the image extension(s), because sometimes it's wrong:
        if "%1" ne "TEST" .and. exist %FILEMASK_IMAGE% (
                repeat 3 echo.
                rem call success "Done! Fixing incorrect image extensions in 15 seconds..."
                rem sleep                                                    15
                call fix-wrong-image-extensions /s
                call wait 1 "Done! Fixing incorrect image extensions in {seconds} seconds..."
        )

rem Finish up:
        echo.
        echo.
        call sleep 2



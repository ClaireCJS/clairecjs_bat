@Echo OFF
 Echo ON

:goto :CheckPoint1
:goto :LumixContinueDebug1

:::::::::::::::: HOW-TO:   1) Configure the "PRIMARY SETUP CONFIGURATION" section in this script, or run "sync-pictures setup" on a new picture storage device 
::::::::::::::::                                                   (usb stick for digital picture frame export, NOT camera for taken-photo import)
:::::::::::::::: HOW-TO:   2) Drop option files on your devices / memory cards. (See below.)
:::::::::::::::: HOW-TO:      At a minimum, you need a MANDATORY IDENTIFICATION file.
:::::::::::::::: HOW-TO:      For dashcams, the first word of the drive label gets inserted into the filename.
:::::::::::::::: HOW-TO:      At a maximum, you can override everything, making each memory card a different playlist(s).
:::::::::::::::: HOW-TO:   3) Run "sync-pictures" to check every drive or "sync-pictures X" if you just want to do drive X:

                           :: todo, if called for:
:::::::::::::::: HOW-TO:           OPTIONAL: set SYNCONLY=X  to only sync X:           (completely redundant interface that doesn't really have to exist)
:::::::::::::::: HOW-TO:           OPTIONAL: set    QUICK=1 for quickest possible run (basically sets NO_WIPE and NOCLEAN)
:::::::::::::::: HOW-TO:           OPTIONAL: set  NO_WIPE=1  to suppress wiping regardless of option file
:::::::::::::::: HOW-TO:           OPTIONAL: set  NOCLEAN=1  to suppress the partial wipe of things like BAK files (as well as WAV files, which we assume are short-term, i.e. you haven't convered it to mp3 yet but were too impatient to wait before listening to it)



::::::::::::::::: OPTION FILES EXPLANATION: FILENAMES YOU CAN DROP IN THE ROOT FOLDER OF A DEVICE, TO CONTROL SYNC OPTIONS: :::::::::::::::::
:: MANDATORY IDENTIFICATION OPTIONS:
:: "__ photo holder __"     (make 'PICS' dir!)      - The bare minimum to make a storage device be picked up by this script. 
:: "__ photo holder - use resolution 480x243 __"    - use repository at this resolution (requires hard-coding for each resolution!)
::                                                        - supported resolutions: 480x243, 800x480, 800x600, 800x600NP (non-progressive JPGs), 1024x600
:: "__ photo holder - file limit - 8192 __"         - copy no more than these many files, randomly selected from the totality of files we are going to copy, so eventually you'll see them all over multiple syncs
::                                                        - supported limits: 8192





::::: ALLLOW FOR QUICK SETUP OF NEW MP3 DEVICES/USB DRIVES:
    if "%1" ne "SETUP"  goto :NotSettingUp
        %COLOR_WARNING% %+ echo WARNING: About to set up this device to sync pictures to. You sure you want to do this?!?!?!?! %+ %COLOR_NORMAL% %+ pause %+ pause %+ pause %+ pause %+ pause %+ pause %+ pause %+ pause %+ pause 
            cd \
            if not isdir PICS md PICS
            >"__ photo holder __"
            >"__ photo holder - use resolution 800x600 __"

        %COLOR_WARNING% %+ echo WARNING: Our photo repository at 800x600 resolution no longer fits on an 8G drive! %+ %COLOR_NORMAL% %+ pause
            call rn __*
            dir

        %COLOR_SUCCESS% %+ echo All done! %+ %COLOR_NORMAL%
        goto :END
    :NotSettingUp
    if "%1" eq "HELP"  (goto :Help_YES)
    if "%1" eq "USAGE" (goto :Help_YES)
    if "%1" eq "?"     (goto :Help_YES)
    if "%1" eq "/?"    (goto :Help_YES)
    if "%1" eq "/-"    (goto :Help_YES)
                        goto :Help_NO
        :Help_YES
            %COLOR_ADVICE%
                            echo.
                            echo USAGE:
                            echo.
                            echo "sync-pictures"       - syncs all pictures to all picture storage devices connected
                            echo "sync-pictures E"     - syncs all pictures to the picture storage device  connected on drive E: only
                            echo "sync-pictures setup" - sets up new empty thumbdrive/storage device
            %COLOR_NORMAL%
            goto :END
        :Help_NO





::::: SPIEL:
    if "%BLURB_DISPLAYED%" eq "1" goto :AlrightAlready
    set  BLURB_DISPLAYED=1
        %COLOR_WARNING%
        call validate-environment-variables NEWPICTURES
        Echo NOTE: The Canon SD400 imports directly to %NEWNEWPICTURES% thanks to one-time manual configuration by Carolyn for her 2010 XP install, so this should have happened / be happening already, and is not compensated for in this script.
        Echo. %+ %COLOR_ADVICE%
        Echo CAMERAS     COVERED: GE A1230, Fuji Finepix 2800.
        Echo CAMERAS NOT COVERED: Canon cameras - but this still works if you put the card into a card reader.
        echo. %+ %COLOR_DEBUG%
        set WAIT=2 
        rem echo - waiting %WAIT% seconds %+ %COLOR_NORMAL% 
        call wait %WAIT%
    :AlrightAlready

::::: ENVIRONMENT VALIDATION:
    call validate-environment-variables FILEMASK_IMAGE FILEMASK_VIDEO THE_ALPHABET NEWPICS


::::: DETERMINE TARGET & OTHER SETUP:
    set CURRENT_PICTURES_TARGET=%NEWPICS%
    set ALTERNATE_TARGET=0
    :if "%@UPPER[%MACHINENAME%]" eq "GOLIATH" .or. "%@UPPER[%MACHINENAME%]" eq "MAGIC" .or. "%@UPPER[%MACHINENAME%]" eq "CHAOS" (set CURRENT_PICTURES_TARGET=%NEWNEWPICS% %+ set ALTERNATE_TARGET=1)
    set PULLED_FROM_CAMERA=0

::::: DETERMINE FILEMASKS:
    :et VIDEO_FILEMASK=*.avi;*.mov;*.mpg
    :et IMAGE_FILEMASK=*.jpg;*.png;*.gif
    set VIDEO_FILEMASK=%FILEMASK_VIDEO%
    set IMAGE_FILEMASK=%FILEMASK_IMAGE%

::::: COMMAND-LINE PARAMETER BRANCHING:
    for %%letter in (%THE_ALPHABET%) do if "%@UPPER[%1]" eq "%letter%" (gosub DealWithDriveLetter %letter% %+ goto :Finish_Up)
    :Otherwise, we fall through to below, where we do "all"

::::: ACTUALLY DO THE SYNCING/GRABBING:
    :Order here is mostly historic based on moving things to the top while testing
    for %DriveLetter in (%THE_ALPHABET_BY_DRIVE_PRIORITY%) gosub DealWithDriveLetter %DriveLetter%

::::: THIS VAR NEEDS TO BE GLOBAL:
    set DASHCAM_VIDEO_TEMP=UNDEFINED

goto :Finish_Up


::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:DealWithDriveLetter [Letter]

    ::::: If the drive isn't ready, return from this:
        %COLOR_GREP %+ echos ***** Checking drive %Letter% for pictures ***** %+ %COLOR_NORMAL% %+ echo.
        if "%@READY[%Letter%]" eq "0" (%COLOR_WARNING% %+ echo * Drive %Letter% is not ready! %+ %COLOR_NORMAL% %+ goto :returnFromThisOne)

    ::::: We don't sync C: drives: [added in 201610 because of Carolyn providing false information; untested]
        if "%@UPPER[%Letter%]" eq "C" (%COLOR_WARNING% %+ echos * We do not sync to C drives! Sorry!!!!!!!!!!!!!!!!!!!!!!!!!!!!! %+ %COLOR_NORMAL% %+ echo. %+ goto :returnFromThisOne)
        for %computer in (%ALL_COMPUTERS_UP%) if "%@UPPER[%[%Letter%]]" eq "%@UPPER[%[%[DRIVE_C_%computer%]]]" .and. "" ne "%[%Letter%]" .and. "" ne "%[DRIVE_C_%computer%]" (%COLOR_WARNING% %+ echos * We do not sync to C drives, and %Letter% is %computer%'s C drive! Sorry! %+ %COLOR_NORMAL% %+ echo. %+ goto :ReturnAlready)

    ::::: LEGACY CAMERAS, PROBABLY IMPLEMENTED STUPIDLY:    
                    ::::: That stupid $100 GE camera that died so fast and made Christian so butt-hurt because he recommended it and his didn't die:
                        :f isdir %Letter%:\DCIM\100GEDSC goto :grabGEA1230
                        if isdir %Letter%:\DCIM\101GEDSC goto :grabGEA1230
                                                         goto :NoGEA1230
                            :grabGEA1230
                                echo. %+ %COLOR_SUCCESS% %+ echo *** GE A1230 pictures found! %+ pause %+ set PULLED_FROM_CAMERA=1
                                if isdir %Letter%:\DCIM\100GEDSC mv/ds %Letter%:\DCIM\100GEDSC "%CURRENT_PICTURES_TARGET%"
                                if isdir %Letter%:\DCIM\101GEDSC mv/ds %Letter%:\DCIM\101GEDSC "%CURRENT_PICTURES_TARGET%"
                            :NoGEA1230
                    ::::: That $5 yardsale camera:
                        if not isdir %Letter%:\DCIM\100_FUJI (goto :NoFujiFinepix2800)
                                    echo. %+ %COLOR_SUCCESS% %+ echo Fuji Finepix 2800 pictures found! %+ pause  %+ set PULLED_FROM_CAMERA=1
                                    mv/ds %Letter%:\DCIM\100_FUJI "%CURRENT_PICTURES_TARGET%"
                         :NoFujiFinepix2800
                    ::::: At first, this always worked for Canon memory cards:
                        if not isdir %Letter%:\DCIM\100CANON (goto :NoCanon100)
                            echo. %+ echo Canon pictures found! %+ pause %+ set PULLED_FROM_CAMERA=1 %+ mv/ds %Letter%:\DCIM\100CANON "%CURRENT_PICTURES_TARGET%"
                        :NoCanon100
                    ::::: Then I installed CHKD, and this started to exist:
                        if not isdir %Letter%:\DCIM\129CANON (goto :NoCanon129)
                            echo. %+ echo Canon pictures found! %+ pause %+ set PULLED_FROM_CAMERA=1 %+ mv/ds %Letter%:\DCIM\129CANON "%CURRENT_PICTURES_TARGET%"
                        :NoCanon129

    ::::: PROPER CAMERAS, DEFINITELY IMPLEMENTED SMARTLY:

            ::::: Cases for: 1) Dashcam 2) generic picture holder (digital picture frame):
                if exist "%Letter%:\__ Z5 dashcam __"   (gosub Z5Dashcam            %Letter% %+ goto :returnFromThisOne)
                if exist "%Letter%:\__ A8 dashcam __"   (gosub Z5Dashcam            %Letter% %+ goto :returnFromThisOne)
                if exist "%Letter%:\__ photo holder __" (gosub GenericPictureHolder %Letter% %+ goto :returnFromThisOne)
                ::::::::::::::::::::::::: NEW CASES GO HERE :::::::::::::::::::::::::

    ::::: CATCH-ALLS THAT SHOULDN'T HAPPEN, MOSTLY TO FORCE US TO REACT TO A MIS-CONFIGURATION THAT WOULD CAUSE US TO END UP HERE IN THE FIRST PLACE:
                        ::::: Super-general catch-all case:
                            if not exist %Letter%:\DCIM\???CANON goto :NoCanonXXX
                                    echo. %+ echo Canon pictures found! But without formalizing a specific case in %0, they will not be processed properly. They will still be procesesd, however you will have to notice what happens and maybe clean up the mess and run the post-processing (allfiles exif and such) manually. %+ pause
                                        mv/ds %Letter%:\DCIM\ "%CURRENT_PICTURES_TARGET%"
                                        set PULLED_FROM_CAMERA=1
                                    pause %+ echo Remember, you must post-process manually. Now may be the time to fire another window up and do that. %+ pause %+ pause %+ pause %+ pause %+ pause 
                                :NoCanonXXX
                        ::::: 2020: Lumix camera use case
                            if not exist %Letter%:\DCIM\???_PANA (goto :NoLumix)
                                     set PROCESSING_FOLDER=%CURRENT_PICTURES_TARGET%\IMPORTING-Lumix
				     if not isdir "%PROCESSING_FOLDER%" (mkdir /s  "%PROCESSING_FOLDER%")
				     if not isdir "%PROCESSING_FOLDER%" (echo UH OH SPAGHETTIOS %+ pause)
                                     :echo. %+ echo Lumix pictures found! But without formalizing a specific case in %0, they will not be processed properly. They will still be processed, however you will have to notice what happens and maybe clean up the mess and run the post-processing (allfiles exif and such) manually. %+ pause
                                      echo. %+ echo Lumix pictures found!  %+ pause
                                        :echo * About to: mv/ds %Letter%:\DCIM\ "%CURRENT_PICTURES_TARGET%"
                                        :                 mv/ds %Letter%:\DCIM\ "%CURRENT_PICTURES_TARGET%"
                                         echo * About to: %Letter%:\DCIM\ %%+ sweep mv %FILEMASK_IMAGE%;%FILEMASK_VIDEO% "%PROCESSING_FOLDER%"
                                                          %Letter%:\DCIM\  %+ sweep mv %FILEMASK_IMAGE%;%FILEMASK_VIDEO% "%PROCESSING_FOLDER%"
                                         %COLOR_WARNING% %+ echo * If there were any errors (ERRORLEVEL=%ERRORLEVEL%), you should Ctrl-Break now!!!
				                                      pause
                                         set PULLED_FROM_CAMERA=1
					 if exist %Letter%:\DCIM\100_PANA (set GRABDIR=%Letter%:\DCIM\100_PANA)
					 if exist %Letter%:\DCIM\101_PANA (set GRABDIR=%Letter%:\DCIM\101_PANA)
					 echo Letter is %Letter% - goat
                                    :pause %+ echo Remember????, you must??????????? post-process manually. Now????? may??????????? be the time to fire another window up and do?????????????? that. %+ pause %+ pause %+ pause %+ pause %+ pause 
                                     pause %+ %COLOR_WARNING% %+ echo * About to postprocess.... %+ pause %+ pause %+ pause %+ pause %+ pause 
                                     call validate-environment-variable PROCESSING_FOLDER
                                     "%PROCESSING_FOLDER%\"
                                     echo are we in the processing folder of %processing_folder yet? CWP=%_CWP %+ pause
                                     call allfiles exif time
				                                     pause
                                     dir
                                     %COLOR_SUCCESS% %+ echo Seems successful for images!  Was it?  Hit any key if it was... (Ctrl-Break if not)
								     pause
								     pause
								     pause
								     pause
                                     :LumixContinueDebug1
                                     :update 2 to 3 when year 3000 rolls along  #IWillNeverDie - appears again below!!!!!!!!!!!
                                     :mv 2* ..
				     echo grabdir=%GRABDIR%
				     %GRABDIR%\
				     set LUMIX_FILEMASK_TEMP=2*;P???????.*
                                     mv %LUMIX_FILEMASK_TEMP% ..
								     pause
								     pause
								     pause
                                     echo * Now let's see if there are some videos to rename too....
								     pause
                                     dir %FILEMASK_VIDEO%
								     pause
                                     echo * Are there videos left?  Then we will run allfiles filedate time.  It's okay to run this if no videos exist.
								     pause
								     pause
								     pause
								     pause
								     pause
                                     call allfiles filedate time
								     pause
                                     echo Did that work?
                                     dir
                                     echo Did that work? Yes?  Let's continue then...
								     pause
								     pause
								     pause
								     pause
                                     mv 2%LUMIX_FILEMASK_TEMP% ..
                                     cls
                                     dir
                                     echo * We really should have no files left, right?
								     pause
								     pause
								     pause
								     pause
				     goto :Lumix_Done
                                
				:NoLumix
					echo NOT a lumix! %+ pause
				:Lumix_Done

                        ::::: 2015: dashcam sdcard use case
                            if not exist %Letter%:\DCIM\ (goto :NoDCIM)
                                    %COLOR_WARNING%   %+ echo Well, it's a camera. We know that. Somehow. But there's a DCIM folder.
                                    %COLOR_IMPORTANT% %+ echo But I guess it's not a Canon camera, or at least not one that's known, or has a DCIM\???CANON folder that could be deteced.
                                pause
                                    %COLOR_PROMPT%    %+ echo If this is a Z5 dashcam, issue the command: %+ echo %=>"%Letter%:\__ Z5 dashcam __"
                                    %COLOR_ADVICE%    %+ echo Then this script will know how to process it.
                                pause
                                    %COLOR_ALARM%     %+ echo You should probably ctrl-break and fix that now. %+ beep
                                pause
                            :NoDCIM

    %COLOR_REMOVAL% %+ echo             ... No pictures found on drive %letter% %+ %COLOR_NORMAL%

:returnFromThisOne
return
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

        :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        :GenericPictureHolder [DriveLetter]
            :: debug
                %COLOR_DEBUG% %+ echo - calling generic picture handler %+ %COLOR_NORMAL%
            :: initialize variables
                if defined FILE_LIMIT unset /q FILE_LIMIT
                set SOURCE_REPOSITORY=%PICTURES%
            :: check for option files limiting our resolution
                if exist "%DriveLetter%:\__ photo holder - use resolution 480x243 __"   (call validate-environment-variable PICTURES480x243   %+ set SOURCE_REPOSITORY=%PICTURES480X243%   %+ %COLOR_IMPORTANT_LESS% %+ echo - Option file changed source repository to: %SOURCE_REPOSITORY% %+ call update-pictures-480x243-repository)
                if exist "%DriveLetter%:\__ photo holder - use resolution 800x480 __"   (call validate-environment-variable PICTURES800x480   %+ set SOURCE_REPOSITORY=%PICTURES800x480%   %+ %COLOR_IMPORTANT_LESS% %+ echo - Option file changed source repository to: %SOURCE_REPOSITORY% %+ call update-pictures-800x480-repository)
                if exist "%DriveLetter%:\__ photo holder - use resolution 800x600 __"   (call validate-environment-variable PICTURES800x600   %+ set SOURCE_REPOSITORY=%PICTURES800x600%   %+ %COLOR_IMPORTANT_LESS% %+ echo - Option file changed source repository to: %SOURCE_REPOSITORY% %+ call update-pictures-800x600-repository)
                if exist "%DriveLetter%:\__ photo holder - use resolution 800x600NP __" (call validate-environment-variable PICTURES800x600NP %+ set SOURCE_REPOSITORY=%PICTURES800x600NP% %+ %COLOR_IMPORTANT_LESS% %+ echo - Option file changed source repository to: %SOURCE_REPOSITORY% %+ call update-pictures-800x600-NP-repository)
                if exist "%DriveLetter%:\__ photo holder - use resolution 1024x600 __"  (call validate-environment-variable PICTURES1024x600  %+ set SOURCE_REPOSITORY=%PICTURES1024x600%  %+ %COLOR_IMPORTANT_LESS% %+ echo - Option file changed source repository to: %SOURCE_REPOSITORY% %+ call update-pictures-1024x600-repository)
                    :: add new digital picture frames here

            :: check for option files limiting the number of files we copy
                if exist "%DriveLetter%:\__ photo holder - file limit - 8192 __"  (set FILE_LIMIT=8192 %+ %COLOR_IMPORTANT_LESS% %+ echo - Option file changed file limit to: %FILE_LIMIT%)
                    :: add new file limit thresholds here

            :: if we are copying all files, use the pre-existing sync-a-folder-to-somewhere tool
            :: but if we are copying a limited number of files randomly, that is not sufficient

                if defined FILE_LIMIT goto :Copy_Some
                    :Copy_All
                        :: use sync-a-folder-to-somewhere to sync the folders - it has this invocation pattern:
                            set  SYNCSOURCE=%SOURCE_REPOSITORY%
                            set  SYNCTARGET=%DriveLetter%:\PICS
                            set  SYNCTRIGER=__ last synced to this picture holder __
                            call sync-a-folder-to-somewhere.bat 
                            goto :Copy_Done
                    :Copy_Some
                        :: devices that have file limits, well... that means we can't fully use them. 
                        :: each time we sync, we will simply take a different random selection from 
                        :: what we have.  Therefore, wiping the device is implicit:
                            %COLOR_IMPORTANT% %+ echo * NOTE: Only copying %FILE_LIMIT% files due to configuration...[will wipe previously-copied files] %+ %COLOR_NORMAL%
                            gosub :WipeImagesOffOfDevice %DriveLetter%
                        :: create a filelist of the randomly-selected subset of files that we will be copying:
                            call setTmpFile %+ set TMP1=%TMPFILE% %+ dir /a:-d /bs "%@UNQUOTE[%SOURCE_REPOSITORY%]"    >"%TMP1%" 
                            call setTmpFile %+ set TMP2=%TMPFILE% %+ select-random-lines-from.pl %FILE_LIMIT% "%TMP1%" >"%TMP2%"
                        :: with pinache (random-colors, countdown in same place on screen), copy these files with *GUARANTEED UNIQUE* target names:
                            %COLOR_DEBUG% %+ timer /2 on
                                set i=%FILE_LIMIT% 
                                for /f "tokens=1-9999" %f in (@%TMP2) (call randfg %+ cls %+ echos * Remaining: `` %+ set /a i-=1 %+ echo %i %+ echo. %+ cp /md  "%f" "%DriveLetter%:\PICS\%@NAME[%f]-%_DATETIME.%i.%@EXT[%f]")
                            %COLOR_DEBUG% %+ timer /2 off
                    :Copy_Done
        return
        ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
            ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
            :WipeImagesOffOfDevice [DriveLetter]
                %COLOR_ALARM%   %+ if "%driveletter%" eq "" (call alarm-beep %+ echo FATAL ERROR#0923402843 %+ call cancelll)
                %COLOR_DEBUG%   %+ timer /1 on
                %COLOR_WARNING% %+ echo * Wiping all images off of %DriveLetter%
                :COLOR_DEBUG%   %+ echo del/s%DriveLetter%:\PICS\%FILEMASK_IMAGE% %+ pause %+ REM debug
                %COLOR_REMOVAL% %+ *del   /s %DriveLetter%:\PICS\%FILEMASK_IMAGE%
                %COLOR_RUN%     %+ pushd. %+ %DriveLetter%:\PICS\ %+ sweep rd * %+ sweep rd * %+ popd
                %COLOR_SUCCESS  %+ echo * Device wipe complete.
                %COLOR_DEBUG%   %+ timer /1 off
            return
            ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

::::::::::::::::::::::::::::::::::::::::::::::::::::::
:DealWithDropbox
	echo.
	echo.
	echo.
	echo Be careful with these dropbox ones. You may not want to overwrite because they can get corrupted.
	pause
        %COLOR_WARNING%
        echo in 2015 this was deprecated! harmful! BAT-overwriting!!
        echo probably don't want to do this anymore!
        pause
        pause
        pause
        pause
        pause

	if isdir %DROPBOX% goto :Dropbox_Found_YES
	                   goto :Dropbox_Found_NO

		:Dropbox_Found_Yes
			cd %DROPBOX%
			ECHO ABOUT TO: mv/ds . ..
            pause
			mv/ds . ..
			cd ..
			goto :Dropbox_Done
		:Dropbox_Found_NO
			echo Can't find dropbox folder! It should be junctioned so it's NEWPICS\DROPBOX, which should point to dropbox\Camera Uploads
			goto :Dropbox_Done
		:Dropbox_Done
return
::::::::::::::::::::::::::::::::::::::::::::::::::::::

::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:Z5Dashcam [driveLetter]
    ::::: BLURB:
        %COLOR_IMPORTANT%
            echo * This appears to be a Z5 dashcam.
            echo * We will process it as "generic folder of badly named videos".
            if "%DEBUG%" eq "1" pause
        %COLOR_NORMAL%

    ::::: LOOK AT DRIVE LABEL:
        set driveLabel=%@label[%DriveLetter%]
        call print-if-debug * driveLabel = %driveLabel%

    ::::: COMPUTE TEMP-DIR AND SET FINAL TARGET:
        :: ensure dashcam vid main dir
            set DASHCAM_VIDEO_FINAL_TARGET=%NEWPICS%\dashcam-videos
            call validate-environment-variable DASHCAM_VIDEO_FINAL_TARGET
            %COLOR_DEBUG% %+ echo DASHCAM_VIDEO_FINAL_TARGET is %DASHCAM_VIDEO_FINAL_TARGET% %+ %COLOR_NORMAL%
        :: ensure dashcam vid temp dir
            set DASHCAM_VIDEO_TEMP=%NEWPICS%\dashcam-videos\sync.temp.%_DATETIME%.%_PID
            if not isdir "%DASHCAM_VIDEO_TEMP%" md "%DASHCAM_VIDEO_TEMP%"
            call validate-environment-variable DASHCAM_VIDEO_TEMP
            %COLOR_DEBUG% %+ echo DASHCAM_VIDEO_TEMP         is %DASHCAM_VIDEO_TEMP% %+ %COLOR_NORMAL%

    :::: RENAME EVERYTHING TO PREVENT FILENAME COLLSIONS, PRIOR TO BRINGING IT HOME:
        gosub DealWithGenericFolderOfBadlyNamedVideos "%driveLetter%:\DCIM" "%DASHCAM_VIDEO_TEMP%" %driveLabel%

    :::: MOVE THEM HOME:
        %COLOR_RUN%
        mv/ds "%DASHCAM_VIDEO_TEMP%" "%DASHCAM_VIDEO_FINAL_TARGET%"
        :20200112: trying to fix that stupid dashcam bug bullshit:
            cd "%DASHCAM_VIDEO_FINAL_TARGET%"
        %COLOR_NORMAL%

return
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:DealWithGenericFolderOfBadlyNamedVideos [source target additionalDescriptor]
    if "%DEBUG%" eq "1" .or. %username% eq "carolyn" (%COLOR_DEBUG% %+ echo - DealWithGenericFolderOfBadlyNamedVideos %source% %TARGET% %+ %COLOR_NORMAL%)
    if not isdir %TARGET%  md /s %TARGET%
    if not isdir %TARGET% (echo target of %TARGET% must exist! %+ beep %+ pause %+ quit)
    if not isdir %source% (echo source of %source% must exist! %+ beep %+ pause %+ quit)

    pushd .
        %source%\
            set SWEEPING=1
                set ADDITIONAL_FILENAME_DESCRIPTOR=%additionalDescriptor%
                                        echo there's a bug (29FF34) where we accidentally run allfiles filedate time in the newpics dir and rename attrib.lst
                                        echo and everything. it's horrible. so.. are we in the right folder right now? 
                                        echo * The following folder should NOT be newpics, and perhaps something like a DCIM
                                        echo * CWP = %_CWP ... CWD = %_CWD
                                        pause
                                        pause
                                        pause
                sweep call allfiles filedate time
            set SWEEPING=0
        %source%\

        %COLOR_DEBUG%   %+ echo * CWD=%_CWD %+ %COLOR_NORMAL%
        %COLOR_DEBUG%   %+ echo * global /i if exist %VIDEO_FILEMASK% (mv %VIDEO_FILEMASK% %target% %+ echo. %+ free %target%)
                                  Y:
                                  global /i if exist %VIDEO_FILEMASK% (mv %VIDEO_FILEMASK% %target% %+ echo. %+ free %target%)
        %COLOR_REMOVAL% %+        global /i rd *
                                  global /i rd *
                                  global /i rd *
    popd 
return
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::



:(Should Not Be Here)
    %COLOR_ALARM% %+ echo * FLOW CONTROL ERROR -- WHY ARE WE HERE?!?! %+ beep %+ pause
































::::: CLEAN-UP / POST-PROCESSING:
    ::::: STORE OUR ORGINAL FOLDER AND MOVE TO OUR TARGET FOLDER SO WE CAN RUN SCRIPTS THERE:
        :Finish_Up
        if "%DEBUG%" eq "1" (echo * All done, about to finish up. %+ echo * CWD = %_CWD %+ pause)        
        pushd .
        "%CURRENT_PICTURES_TARGET%\"


    ::::: THINGS WE DO ONLY IF WE STILL HAVE IMAGES HERE:
        if not exist %FILEMASK_IMAGE% goto :Skip_Image_Postprocessing

            
            :: Rename them based on EXIF information:
                                        echo there's a bug where we accidentally run allfiles filedate time in the newpics dir and rename attrib.lst (2)
                                        echo and everything. it's horrible. so.. are we in the right folder right now? CWP = %_CWP ... CWD = %_CWD
                                        echo * That folder should NOT be newpics in the case of dashcam video import, but perhaps something like newpics\dashcam-videos
                                        pause
                                        pause
                                        pause
                :CheckPoint1
                md hold
                cd hold
                mv ..\%FILEMASK_IMAGE%
                call allfiles exif %+ REM maybe use autoname here?
                mv * ..
                cd ..
                rd hold
                    echo ** Wait for allfiles exif to finish before hitting a key 3 times... If it always makes sense here, we might want to turn SWEEPING ON and make this automatic.
                        pause>nul %+ pause>nul %+ pause>nul
            :: Sort them into folder based on the newly-renamed name:
                call sort-pictures-into-folders
        :Skip_Image_Postprocessing


::    20170301: BUG WHERE FILES GET ALLFILES-FILEDATE-TIME-AND-SHOULD-NOT:
::    SOLUTION: COMMENT IT OUT:
::
::    ::::: THINGS WE DO ONLY IF WE STILL HAVE FILES HERE:        
::        if not exist %VIDEO_FILEMASK% goto :Skip_Filedate_Processing
::            :: Rename them based on FILE DATE:
::                SET SWEEPING=1
::                call allfiles filedate time
::                SET SWEEPING=0
::                    echo ** Wait for allfiles filedate to finish before hitting a key 3 times...
::                        pause>nul %+ pause>nul %+ pause>nul
::::::20170301: NOT SURE IF WE SHOULD COMMENT THIS OUT AS WELL, THOUGH:
::            :: Sort them into folder based on the newly-renamed name:
::                call sort-pictures-into-folders
::        :Skip_Filedate_Processing

    ::::: IF WE AREN'T DOING THIS IN THE NORMAL PLACE, MOVE OUR STUFF TO THE NORMAL PLACE:
        if "%ALTERNATE_TARGET%" ne "1" goto :donotassimilate
            echo Now we will assimilate them to %NEWPICS%... %+ pause>nul %+ pause>nul %+ pause>nul
            call assimilate.bat
        :donotassimilate

    ::::: POP BACK INTO OUR ORIGINAL FOLDER:
        :END
        :Finish_Up_For_RealReal
        popd >nul >&>nul

@REM                              Edit this one only in c:\bat\
@Echo ON
 on break cancel

echo caller to %0 in %_CWD: %_PBATCHNAME %+ pause


:DESCRIPTION:  Used to package BAT/UTIL/helper files from a personal environment into a development project folder for public deployment
:DESCRIPTION:  Copies specific files to "BAT" folder, in a zip
:USAGE:        SET MANIFEST_FILES=ingest_youtube_album.py download-youtube-album.bat or SET MANIFEST_FILES=NONE
:USAGE:        set SECONDARY_BAT_FILES=%MANIFEST_FILES% validate-in-path.bat delete-largest-file.bat add-ReplayGain-tags.bat add-ReplayGain-tags-to-all-FLACs.bat add-ReplayGain-tags-to-all-MP3s.bat change-into-temp-folder.bat set-latestfilename.bat 
:USAGE:        set SECONDARY_BAT_FILES_2=(in case your list of files is longer than 8192, use additional variables)
:USAGE:        set SECONDARY_UTIL_FILES=metamp3.exe metaflac.exe yt-dlp.exe
:USAGE:        call update-from-BAT-via-manifest.bat set-colors.bat
:DEPENDENCIES: insert-before-each-line.bat





REM     I actually do all my development for this in my personal live command line environment,
REM     so for me, these files actually "live" in "c:\bat\" and just need to be refreshed to my 
REM     local GIT repo beore doing anything significant.  Or really, before doing anything ever.

rem Must have parameter!
        set which_file=
        if "%1" eq "" (call fatal_error "%0 must have 1ˢᵗ parameter of target folder for example BAT-and-UTIL-files-1")
        iff "%2" ne "" then
                set  which_file=%@UNQUOTE[%2]
                rem if "%1" 

        endiff

rem VALIDATION & SETUP:
        set SOURCE_DIR=%BAT%
        set PROJECT_DIR=%_CWD
        set PROJECT_NAME=%@NAME[%PROJECT_DIR]
        set   COPY=*copy /E /Ns /R /Z
        set   COPY=*copy /E /Ns /R /U
        set   COPY=*copy /E /Ns    /U
        set   COPY=*copy    /Ns    /U
        set   COPY=*copy    /Ns /R /U
        set UPDATE=*copy /q /Ns    /U
        set DELETE=*del /z /q
        rem Some stuff we only need to validate once per command-line sessoin:
        iff %VALIDATED_UPDATEFROMBATVIAMANIFEST_ENV_ALREADY ne 1 then
            call validate-environment-variables BAT COPY
            call validate-in-path important_less success errorlevel insert-before-each-line
            set  VALIDATED_UPDATEFROMBATVIAMANIFEST_ENV_ALREADY=1
        endiff
        rem Some stuff we need to validate each and every run:
        call validate-environment-variables MANIFEST_FILES SOURCE_DIR 

rem Cosmetic kludge:
        rem no this actually tended to break it! call set-ansi force

rem TELL USER:
        cls
        echo.
        call important "Updating: '%PROJECT_NAME%' files: " 
              echo %ANSI_COLOR_IMPORTANT%                 To: %[PROJECT_DIR]%ANSI_COLOR_IMPORTANT_LESS%
              rem too big!          Manifest Files: %MANIFEST_FILES%




rem DO COPIES OF PRIMARY FILES TO PRIMARY PROJECT FOLDER:
        if "%MANIFEST_FILES%" eq "NONE" (goto :Manifest_File_Update_Complete)               
                for %myFileFull in (%MANIFEST_FILES%) (
                    set myFile=%@UNQUOTE[%myFileFull]
                    rem echo %blink_on%[LOOP] myFileFull is currently=%myFileFull%%blink_off%
                    echos %@RANDFG[]*
                    if not exist "%SOURCE_DIR%\%myFile%" (call error "Uh oh! Project source file '%italics_on%%myFile%%italics_off%' doesn't seem to exist in %SOURCE_DIR%")
                    rem  Taking this out for a speedup: if exist %myFileFull% (%COLOR_WARNING %+ attrib -r  %myFile% >nul %+ %DELETE% %myFile%)
                    rem color bright black on black
                    (%COPY% /u %SOURCE_DIR%\%myFile% . )            
                )
                rem call debug "setting files to +r in %_CWD"               
        :Manifest_File_Update_Complete


rem DO SECONDARY FILES, OR SKIP THEM IF WE SAID TO:
        if "%1" eq "skip" .or. "%1" eq "fast" .or. "%1" eq "quick" (shift %+ goto :Skip)
        if "%2" eq "skip" .or. "%2" eq "fast" .or. "%2" eq "quick" (         goto :Skip)

                    rem SHARE REQUIRED BAT, UTIL FILES THAT WE USE, FOR FURTHER SUPPORT, TO SECONDARY PROJECT FOLDER:
                            set SECONDARY_SUBFOLDER_FOLDERNAME=%1
                            for %shared_type in (BAT UTIL) do (gosub process_type %shared_type)

        :Skip


goto :END_OF_SUBROUTINES

        :process_type [shared_type]
            call print-if-debug "Doing shared_type='%shared_type%'"
            if not defined SECONDARY_%shared_type%_FILES goto :No_Files_Of_This_Type
                set                                SOURCE_DIR=c:\%shared_type\
                call validate-environment-variable SOURCE_DIR
                set    OUR_FILELIST=%[SECONDARY_%shared_type%_FILES]
                set  OUR_FILELIST_2=%[SECONDARY_%shared_type%_FILES_2]
                set  OUR_FILELIST_3=%[SECONDARY_%shared_type%_FILES_3]
                set  OUR_FILELIST_4=%[SECONDARY_%shared_type%_FILES_4]
                set  OUR_FILELIST_5=%[SECONDARY_%shared_type%_FILES_5]
                set  OUR_FILELIST_6=%[SECONDARY_%shared_type%_FILES_6]
                set  OUR_FILELIST_7=%[SECONDARY_%shared_type%_FILES_7]
                set  OUR_FILELIST_8=%[SECONDARY_%shared_type%_FILES_8]
                set  OUR_FILELIST_9=%[SECONDARY_%shared_type%_FILES_9]
                set OUR_FILELIST_10=%[SECONDARY_%shared_type%_FILES_10]
                iff "" ne "%which_file%" then
                        set OUR_FILELIST=%which_file%
                        set OUR_FILELIST_2=
                        set OUR_FILELIST_3=
                        set OUR_FILELIST_4=
                        set OUR_FILELIST_5=
                        set OUR_FILELIST_6=
                        set OUR_FILELIST_7=
                        set OUR_FILELIST_8=
                        set OUR_FILELIST_9=
                        set OUR_FILELIST_10=
                        
                        if "%which_file%" eq "docs" (set OUR_FILELIST=docs\*.md docs\outtakes\*
                endiff


                REM Create individual distribution files of our BATs, UTILs, as needed
                        REM Change into source folder to copy our files
                                pushd.
                                    %SOURCE_DIR%\
                        REM make target folder
                                    rem call print-if-debug "need to make individual distribution of OUR_FILELIST='%OUR_FILELIST%'"
                                    set TARGET_DIR=%PROJECT_DIR%\%SECONDARY_SUBFOLDER_FOLDERNAME%
                                    if not exist %TARGET_DIR% mkdir /s %TARGET_DIR%
                                    call validate-environment-variable  TARGET_DIR
                                    echos                  ``
                        REM copy each file
                                    rem echo %ansi_color_warning%our_filelist is %our_filelist%%ansi_color_normal% 🐮
                                    rem set remark=echos %newline%%tab%%arrow%Checking file '%file%'
                                    for %file in (%OUR_FILELIST%  %OUR_FILELIST_2%  %OUR_FILELIST_3%  %OUR_FILELIST_4%  %OUR_FILELIST_5%  %OUR_FILELIST_6%  %OUR_FILELIST_7%  %OUR_FILELIST_8%  %OUR_FILELIST_9%  %OUR_FILELIST_10%) do (
                                                if     exist %file% (
                                                        echos %@random_cursor_color[]%@randfg[].
                                                        %UPDATE%   %file%  %TARGET_DIR%\%file%
                                                ) else (
                                                        call error "file doesn't exist: %file%"
                                                )
                                    )
                                popd

                REM Create zip distribution files of our BATs, UTILs, as needed
                        rem Only do the zip SOME of the time:
                                if %@RANDOM[0,10] ne 0 (goto :not_this_time)
                        
                        REM make zip folder
                                set           ZIP_FOLDER=%PROJECT_DIR%\%SECONDARY_SUBFOLDER_FOLDERNAME%\zipped
                                if not isdir %ZIP_FOLDER% mkdir /s %ZIP_FOLDER%
                                call validate-environment-variable  ZIP_FOLDER "%0 couldn't ake zip folder of '%ZIP_FOLDER%'"
                        REM make zip+zip manifest filenames
                                set OUR_ZIP=%ZIP_FOLDER\personal-%shared_type%-files-used-in-this-project.zip
                                set OUR_TXT=%ZIP_FOLDER\personal-%shared_type%-files-used--------filelist.txt
                        REM delete zip and/or manifest if already there, if we want (i don't)
                                rem if exist %OUR_ZIP% %DELETE% %OUR_ZIP% 
                                rem if exist %OUR_TXT% %DELETE% %OUR_TXT% 
                                pushd
                        REM Change into source folder to create our zip
                                %SOURCE_DIR%\
                        REM freshen if existing zip, otherwise add to new zip
                                set ZIP_OPTIONS=/P /F /U
                                if not exist %OUR_ZIP% set ZIP_OPTIONS=/A
                                set ZIP_COMMAND=*zip %ZIP_OPTIONS% %OUR_ZIP% %OUR_FILELIST% %OUR_FILELIST_2% %OUR_FILELIST_3% %OUR_FILELIST_4% %OUR_FILELIST_5% %OUR_FILELIST_6% %OUR_FILELIST_7% %OUR_FILELIST_8% %OUR_FILELIST_9% %OUR_FILELIST_10% 
                        REM suppress stdout, any output now would be stderr so color it as such
                                echos %@ANSI_MOVE_TO_COL[1]%ANSI_EOL%
                                echo.
                                call important_less "Zipping associated %shared_type% files..."
                                rem call unimportant    "    zip command: %ZIP_COMMAND%"
                                rem call unimportant    "            CWD: %_CWD%"
                        REM choose your zip output strategy:
                            REM %COLOR_ERRROR% %+ %ZIP_COMMAND% >nul
                                %COLOR_SUCCESS 
                                rem echo %blink_on%DEBUG: %ZIP_COMMAND% `>`:u8 zip.out %blink_off%🐐
                                %ZIP_COMMAND% >:u8 zip.out 
                                call errorlevel "Zipping our associated %shared_type% filfailed?!"
                                type zip.out |:u8 insert-before-each-line "           "
                        REM ensure zip generated
                                if exist zip.out (%COLOR_REMOVAL% %+ echo ray|del /q /r zip.out%>nul)
                                echo.>& nul
                                REM moved later for speedup:
                                rem call validate-environment-variable OUR_ZIP
                        REM create manifest file of what's in the ZIP and make sure it exists
                                REM set UNZIP_COMMAND=*unzip /v %OUR_ZIP%  
                                REM call print-if-debug "Unzip command is: %UNZIP_COMMAND ... and will redirect to target: '%OUR_TXT%'"
                                REM sort it (cygwin sort.exe) 
                                REM echo *unzip /v %OUR_ZIP% `|`    call cygsort --ignore-case -k5 `>`"%OUR_TXT"
                                REM      *unzip /v %OUR_ZIP%  |     call cygsort --ignore-case -k5  > "%OUR_TXT"  until 20241107
                                         *unzip /v %OUR_ZIP%  |:u8  call cygsort --ignore-case -k5  > "%OUR_TXT"
                                call errorlevel "Unzipping our associated %shared_type% file failed?!"
                                call validate-environment-variable OUR_ZIP OUR_TXT
                        rem Finish up by returning from whence we came:
                                popd

                        rem Place we jump to if we didn't ZIP anything this time:
                                :not_this_time
                                
                        REM make sure we add everything to the repo
                                set SKIP_GIT_ADD_VALIDATION_OLD=%SKIP_GIT_ADD_VALIDATION%
                                set SKIP_GIT_ADD_VALIDATION=1
                                echo.
                                echo.
                                call print-if-debug "git add %PROJECT_DIR%\%SECONDARY_SUBFOLDER_FOLDERNAME%\*.*"
                                                     git add %PROJECT_DIR%\%SECONDARY_SUBFOLDER_FOLDERNAME%\*.* 
                                set SKIP_GIT_ADD_VALIDATION=%SKIP_GIT_ADD_VALIDATION_OLD%
                                
                :No_Files_Of_This_Type                
        return
        
:END_OF_SUBROUTINES







rem reset our values so they don't accidentally get re-used, and CELEBRATE:
        set  MANIFEST_FILES=
        set  SECONDARY_BAT_FILES=
        set  SECONDARY_UTIL_FILES=
        call success "Successfully updated from personal to '%ITALICS%%PROJECT_NAME%%ITALICS_OFF%'"
        echo.
        %PROJECT_DIR%\




echo %ansi_color_removal%👻 leaving %0 in %_CWD tha was called by %_PBATCHNAME%ansi_color_normal% %+ pause

@Echo OFF


:DESCRIPTION: This creates 2-3 backup of files in \BACKUPS\IMPORTANT_FILES.%MACHINENAME\
:DESCRIPTION:    1)          current copy (same  name) [i.e. c:\backups\important_files.Demona\addressbook.txt]
:DESCRIPTION:    2)           dated  copy (dated name) [i.e. c:\backups\important_files.Demona\addressbook.txt.2024-03-18]
:DESCRIPTION:    3) OPTIONAL dropbox copy (same  name) [i.e. c:\dropbox\important_files\addressbook.txt]
:DESCRIPTION: 
:DESCRIPTION: ...and then updates the entire \BACKUPS\IMPORTANT_FILES.%MACHINENAME%\ folder to every ready drive that has a \BACKUPS\ folder in it
:DESCRIPTION:               Why yes! If you had 26 drives connected to each drive letter, this would mean 26*2==54 backups made
:DESCRIPTION:                             A bit ridiculous, but the idea is that if a house fire happens that is so bad that only 
:DESCRIPTION:                             a single harddrive survives, you would still retain a dated copy of your important file.
:DESCRIPTION: 
:DESCRIPTION: Of course it goes without saying that we should be using DropBox to backup important files, 
:DESCRIPTION:                                    but time, space, connectivity, and access can be issues.


rem Configuration & environment validation
        set SPACER=           ``
        set BACKUP_TARGET=c:\BACKUPS\IMPORTANT_FILES.%MACHINENAME%
        set BACKUP_TARGET_DROPBOX=%DROPBOX%\BACKUPS\IMPORTANT_FILES.%MACHINENAME%

rem Let user know what we're doing 
        cls %+ echo. %+ call important "Backing up important files" %+ echo. %+ rem might want to move the CLS to the 'backing backups up to every available backup drive' section


rem Ensure backup target folders exists — auto-create the local one it if it does not
rem ...But do NOT auto-create the dropbox one (that's too intrusive to do automatically)
        if not isdir %BACKUP_TARGET (mkdir /s %BACKUP_TARGET%)
        call validate-environment-variables DROPBOX BACKUP_TARGET_DROPBOX CONTACTS ABOUTTOBEBURNED PREBURN_DVD_CATALOG PREBURN_BDR_CATALOG
        call validate-in-path important less_important success error fatal_error


rem **********************************************************************************************************************************************
rem **********************************************************************************************************************************************
rem ********************************************************************************************************************************************** MAIN: BEGIN
rem **********************************************************************************************************************************************
rem **********************************************************************************************************************************************

rem Define any yet-undefined important files we're about to back up:
        set EYEBARCAPS=%HD1T3%:\beta\browser-extension\eyebarCaptions.txt

rem Make sure they are there:
        call validate-environment-variables EYEBARCAPS


rem Back up each important file:

        gosub backup_file dropbox_Y "Windows Terminal settings"    %LOCALAPPDATA%\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json
        gosub backup_file dropbox_Y "### file"                     %CONTACTS%
        gosub backup_file dropbox_N "Adobe Audition settings"      %APPDATA%\Adobe\Audition\12.0\ApplicationSettings.xml 
        gosub backup_file dropbox_N "DVD catalog offline fragment" %PREBURN_DVD_CATALOG%
        gosub backup_file dropbox_N "BDR catalog offline fragment" %PREBURN_BDR_CATALOG%
        gosub backup_file dropbox_N "eyebar captions"              %EYEBARCAPS%

rem **********************************************************************************************************************************************
rem **********************************************************************************************************************************************
rem ********************************************************************************************************************************************** MAIN: END
rem **********************************************************************************************************************************************
rem **********************************************************************************************************************************************


echo.
call success "Done!"
echo.
echo.
call less_important "Backing backups up to every available backup drive...%FAINT_ON%"
echo.
rem Sync important files folder
    for %letter in (%THE_ALPHABET Done!) (
        echos %ANSI_SAVE_POSITION%
        if "%@LEN[%letter]" == "1" (echo  %@ANSI_MOVE_TO_COL[1]%ANSI_COLOR_WARNING%[%letter%:]%ANSI_RESET%%ANSI_EOL%)
        echos %@ANSI_MOVE_TO_COL[5]%ANSI_MOVE_UP_1%%ANSI_GREY%
        if 1 eq %@READY[%letter%] .and. isdir %letter%:\backups (
            set BACKUP_TARGET_TMP=%letter%:\backups\IMPORTANT_FILES.%MACHINENAME%
            echos %ANSI_COLOR_ALARM%%BLINK_ON%%ITALICS_ON%
            *copy /e /w /u /s /a: /h /z /k /g /u /Nts %BACKUP_TARGET% %BACKUP_TARGET_TMP% |:u8 convert-each-line-to-a-randomly-colored-dot.pl |:u8 fast_cat
            call errorlevel
        )
    )
    rem echos %BLINK_OFF%%FAINT_OFF%%ANSI_EOL%%@ANSI_MOVE_TO_COL[1]
    rem echos %ANSI_COLOR_BRIGHT_GREEN%%CHECKBOX% All done! %+ echo.
    echo.
    call success "%italics_on%%underline_on%All%italics_off%%underline_off% important files backed up to all relevant drives!"


goto :END

    :backup_file [dropbox_YN desc filepath]
        echo.
        call less_important "%ANSI_COLOR_CYAN%Backing up %italics_on%%double_underline_on%%ANSI_COLOR_BRIGHT_CYAN%%@UNQUOTE[%desc%]%italics_off%%double_underline_off% %ANSI_COLOR_BRIGHT_BLUE%(%filepath%):"
        if not exist %filepath% (call error "file '%filename%' doesn't exist when trying to back up %desc%")
        echos %@RANDFG[]

        set filename=%@NAME[%filepath].%@EXT[%filepath]
        set TARGET_FILENAME=%BACKUP_TARGET%\%filename%
        set TARGET_FILENAME_DROPBOX=%BACKUP_TARGET_DROPBOX%\%filename%
        set TARGET_FILENAME_DATED=%TARGET_FILENAME%.%_ISODATE
   
    
        rem Always copy it to dropbox if instructed
            if "%dropbox_YN%" eq "dropbox_Y" (
                set SAME=0
                if exist %target_filename_dropbox (set SAME=%@COMPARE[%filepath,%target_filename_dropbox]) 
                if %SAME eq 0 (
                    echos %SPACER%``
                    *copy /a: /G /H /J /K /Z /u /Ns %filepath% %TARGET_FILENAME_DROPBOX% |:u8 insert-before-each-line %SPACER%
                )
            )


        rem Check if it's the same as the local backup
            if exist %TARGET_FILENAME% (set SAME=%@COMPARE[%filepath,%target_filename]) else (set SAME=0)
            if %SAME eq 1 (echo %SPACER%%CHECK% %ANSI_GREEN%%@UNQUOTE[%desc%] (%italics_on%%filename%%italics_off%) already backed up %+ return)

        rem Do the local backup if it's not the same:
            echos %SPACER%`` %+ *copy /a: /G /H /J /K /Z /u /Ns %filepath% %TARGET_FILENAME%         |:u8 insert-before-each-line %SPACER%
            echos %SPACER%`` %+ *copy /a: /G /H /J /K /Z /u /Ns %filepath% %TARGET_FILENAME_DATED%   |:u8 insert-before-each-line %SPACER%
    return


:END

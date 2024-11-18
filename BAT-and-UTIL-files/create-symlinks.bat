@Echo off

::::: PARAMETERS:
    if "%@UPPER[%1]" eq "TEST" goto :Test
    if "%@UPPER[%2]" eq "TEST" goto :Test

::::: PRE-VALIDATION:
    call checkmappings nopause
    if "%ALREADY_VALIDATED_CREATE_SYMLINKS_PREVAL%" eq "1" goto :NoPreVal
        call environm validate >nul
        set ALREADY_VALIDATED_CREATE_SYMLINKS_PREVAL=1
    :NoPreVal
    :Test

::::: MANAGE ALL OF OUR SYMBOLIC LINKS: SETUP: 
    set LINK_DIR=%ALL_COLLECTIONS%
    if "%OS%" eq "2K" .or. "%OS%" eq "XP" quit
    if "%@UPPER[%1]" eq "BYLETTERONLY" (gosub :CreateAutomaticSymlinks %+ goto :END)
    if not isdir c:\media (md c:\MEDIA)

::::: MANAGE ALL OF OUR SYMBOLIC LINKS: DO IT:
     gosub CreateLink %LINK_DIR%\about-to-be-burned_dvd ABOUTTOBEBURNED1             ABOUTTOBEBURNED1DRIVE
     gosub CreateLink %LINK_DIR%\about-to-be-burned_bdr ABOUTTOBEBURNED2             ABOUTTOBEBURNED2DRIVE
     gosub CreateLink %LINK_DIR%\ANIME                  ANIME                                   ANIMEDRIVE
     gosub CreateLink %LINK_DIR%\ANSI                   ANSI                                     ANSIDRIVE 
     gosub CreateLink %LINK_DIR%\BOOKS                  BOOKS                                   BOOKSDRIVE
     gosub CreateLink %LINK_DIR%\CELEBRITIES            CELEBRITIES                       CELEBRITIESDRIVE
     gosub CreateLink %LINK_DIR%\check4norm             MP3PREPROCESSING             MP3PREPROCESSINGDRIVE c:\check4norm
     gosub CreateLink %LINK_DIR%\COMEDY                 COMEDY                                 COMEDYDRIVE
     gosub CreateLink %LINK_DIR%\COMICS                 COMICS                                 COMICSDRIVE c:\comics\
     gosub CreateLink %LINK_DIR%\data_dvd               DATA1                                   DATA1DRIVE c:\data-dvd
     gosub CreateLink %LINK_DIR%\data_bdr               DATA2                                   DATA2DRIVE c:\data-bdr
     gosub CreateLink %LINK_DIR%\DELETE-AFTER-WATCHING  DELETEAFTERWATCHING       DELETEAFTERWATCHINGDRIVE C:\DELETE-AFTER-WATCHING
     gosub CreateLink %LINK_DIR%\Dropbox                DROPBOX                               DROPBOXDRIVE C:\DROPBOX
     gosub CreateLink %LINK_DIR%\dropdir                DROPDIR                               DROPDIRDRIVE C:\DO_LATERRRRRRRR
     gosub CreateLink %LINK_DIR%\EMULATION              EMULATION                           EMULATIONDRIVE
     gosub CreateLink %LINK_DIR%\EXTRAS                 EXTRAS                                 EXTRASDRIVE c:\extras
     gosub CreateLink %LINK_DIR%\EYE-CANDY              EYECANDY                             EYECANDYDRIVE c:\EYE-CANDY
     gosub CreateLink %LINK_DIR%\TO-OTHER-PEOPLE        MEDIA_FOR_OTHER_PEOPLE MEDIA_FOR_OTHER_PEOPLEDRIVE c:\DELETE-AFTER-WATCHING\HANGOUT\MEDIA-TO-GIVE-TO-GUESTS
     gosub CreateLink %LINK_DIR%\for-review             REVIEWDIR                           REVIEWDIRDRIVE C:\FOR-REVIEW
     gosub CreateLink %LINK_DIR%\GAMES                  GAMES                                   GAMESDRIVE c:\GAMES
     gosub CreateLink %LINK_DIR%\GROSS                  GROSS                                   GROSSDRIVE
     gosub CreateLink %LINK_DIR%\IMAGES                 IMAGES                                 IMAGESDRIVE c:\images
     gosub CreateLink %LINK_DIR%\ICONS                  ICONS                                   ICONSDRIVE c:\icons
     gosub CreateLink %LINK_DIR%\INSTALL-FILES          INSTALLFILES                     INSTALLFILESDRIVE C:\INSTALL-FILES
     gosub CreateLink %LINK_DIR%\MISC-DATA              MISCDATA                             MISCDATADRIVE c:\misc-data
     gosub CreateLink %LINK_DIR%\movies                 MOVIESMAINWATCHING         MOVIESMAINWATCHINGDRIVE         
     gosub CreateLink %LINK_DIR%\MIDI                   MIDI                                     MIDIDRIVE C:\MIDI
     gosub CreateLink %LINK_DIR%\MP3                    MP3OFFICIAL                       MP3OFFICIALDRIVE C:\MP3
     gosub CreateLink %LINK_DIR%\mp3-testing            MP3TESTING                         MP3TESTINGDRIVE c:\testing
     gosub CreateLink %LINK_DIR%\MUSIC-VIDEOS           MUSICVIDEOS                       MUSICVIDEOSDRIVE c:\music-videos
     gosub CreateLink %LINK_DIR%\newCL                  NEWCL                                   NEWCLDRIVE c:\newCL
     gosub CreateLink %LINK_DIR%\newCAS                 NEWCAS                                 NEWCASDRIVE c:\newCAS
     gosub CreateLink %LINK_DIR%\new                    NEW                                       NEWDRIVE c:\new
     gosub CreateLink %LINK_DIR%\newmp3                 NEWMP3                                 NEWMP3DRIVE c:\newmp3
     gosub CreateLink %LINK_DIR%\newPics                NEWPICS                               NEWPICSDRIVE c:\newPics
:    gosub CreateLink %LINK_DIR%\newNEWPICS             NEWNEWPICS                         NEWNEWPICSDRIVE c:\newNewPics     ##### DEPRECATED
     gosub CreateLink %LINK_DIR%\PICTURES               PICTURES                             PICTURESDRIVE c:\PICTURES
     gosub CreateLink %LINK_DIR%\POSTCARDS              POSTCARDS                           POSTCARDSDRIVE c:\POSTCARDS
     gosub CreateLink %LINK_DIR%\PROGRAMMING            PROGRAMMING                       PROGRAMMINGDRIVE c:\PROGRAMMING
     gosub CreateLink %LINK_DIR%\pubCL                  PUBCL                                   PUBCLDRIVE c:\pubCL
     gosub CreateLink %LINK_DIR%\pubCAS                 PUBCAS                                 PUBCASDRIVE c:\pubCAS
     gosub CreateLink %LINK_DIR%\pub                    PUB                                       PUBDRIVE c:\pub
     gosub CreateLink %LINK_DIR%\ready-for-tagging      MP3TAGGING                         MP3TAGGINGDRIVE c:\tagging
     gosub CreateLink %LINK_DIR%\ready-to-delete_DVD    READYTODELETE1                 READYTODELETE1DRIVE c:\ready-to-delete-dvd
     gosub CreateLink %LINK_DIR%\ready-to-delete_BDR    READYTODELETE2                 READYTODELETE2DRIVE c:\ready-to-delete-bdr
     gosub CreateLink %LINK_DIR%\SHORTS                 SHORTS                                 SHORTSDRIVE
     gosub CreateLink %LINK_DIR%\SPECIALS               SPECIALS                             SPECIALSDRIVE C:\SPECIALS
     gosub CreateLink %LINK_DIR%\DOCUMENTARIES          DOCUMENTARIES                   DOCUMENTARIESDRIVE C:\DOCUMENTARIES 
     gosub CreateLink %LINK_DIR%\TEXT                   TXT                                       TXTDRIVE
     if "%FIRE_DOWN%" eq "1" goto :FireDown
         gosub CreateLink %LINK_DIR%\torrent_fire_temp      TORRENT_FIRE_TEMP           TORRENT_FIRE_TEMPDRIVE
         gosub CreateLink %LINK_DIR%\torrent_fire_seeding   TORRENT_FIRE_SEEDING     TORRENT_FIRE_SEEDINGDRIVE
     :FireDown
     gosub CreateLink %LINK_DIR%\torrent_goliath        TORRENT_GOLIATH               TORRENT_GOLIATHDRIVE
     gosub CreateLink %LINK_DIR%\VCR                    VCR                                       VCRDRIVE c:\vcr
     gosub CreateLink %LINK_DIR%\wav-processing         WAVPROCESSING                   WAVPROCESSINGDRIVE c:\wav-processing
     gosub CreateLink %LINK_DIR%\wwwCL                  WWWCL                                   WWWCLDRIVE c:\wwwCL
     gosub CreateLink %LINK_DIR%\wwwCAS                 WWWCAS                                 WWWCASDRIVE c:\wwwCAS
     gosub CreateLink %LINK_DIR%\www                    WWW                                       WWWDRIVE c:\www
     gosub CreateLink %LINK_DIR%\wwwPics                PICTURES                             PICTURESDRIVE c:\wwwPics
     gosub CreateAutomaticSymlinks
goto :END


return
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::




    ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
    :CreateLink [LINK_SOURCE LINK_TARGET_VARNAME LINK_TARGET_DRIVE_VARNAME ADDITIONAL_JUNCTION_1]
        :DEBUG: 
        echo - CreateLink [%LINK_SOURCE% %LINK_TARGET_VARNAME% %LINK_TARGET_DRIVE_VARNAME% %ADDITIONAL_JUNCTION_1%]

        ::::: TEST ASSUMPTIONS AND DEREFERENCE PARAMETERS (optimized harder-to-read order):
            if "%LINK_SOURCE%"       eq "" (call alarm-beep FATAL ERROR: CreateLink cannot be called with an empty LINK_TARGET       %+ quit)
            set LINK_TARGET=%[%LINK_TARGET_VARNAME%]             %+ if "%DEBUG%" eq "1" echo [DEBUG] LINK_TARGET       for %LINK_TARGET_VARNAME%       is %LINK_TARGET%
            set LINK_TARGET_DRIVE=%[%LINK_TARGET_DRIVE_VARNAME%] %+ if "%DEBUG%" eq "1" echo [DEBUG] LINK_TARGET_DRIVE for %LINK_TARGET_DRIVE_VARNAME% is %LINK_TARGET_DRIVE%
            if "%LINK_TARGET%"       eq "" (call alarm-beep FATAL ERROR: CreateLink cannot be called with an empty LINK_TARGET       %+ quit)
            if "%LINK_TARGET_DRIVE%" eq "" (call alarm-beep FATAL ERROR: CreateLink cannot be called with an empty LINK_TARGET_DRIVE %+ quit)

        ::::: IS THE DRIVE EVEN READY?
            set READY=%@READY[%LINK_TARGET_DRIVE%]                          %+ rem  If the drive isn't ready, nothing we can do about it.
            if "%READY%" eq "0" set COLOR=red
            if "%READY%" eq "1" set COLOR=green 
            :DEBUG: echo ready=%READY%, color=%color%

        ::::: LET USER KNOW WHAT WE'RE DOING.
                                             echo.
            *color         yellow on black %+ echos *** %+ if "%READY%" eq "0" (color bright %COLOR% on black %+ echos  NOT)
            *color        %COLOR% on black %+ echos  Maintaining symbolic link for
            *color bright %COLOR% on black %+ echos  %LINK_TARGET_VARNAME%
            *color bright  yellow on black %+ echos  ( %+ REM
            *color         yellow on black %+ echos %LINK_TARGET%
            *color bright  yellow on black %+ echos )
            *color        %COLOR% on black %+ echo ...                
            *color         white  on black

        ::::: AND IF IT TURNS OUT THAT THE DRIVE WASN'T EVEN READY, WE'RE DONE:
            if "%READY%" eq "0" return

        ::::: CREATE THE LINK:
            gosub RemoveBadSimlinks %LINK_SOURCE% "%LINK_TARGET%" %LINK_TARGET_VARNAME% %ADDITIONAL_JUNCTION_1%  %+ rem  Remove current link(s) if bad
            if isdir         %LINK_SOURCE%        return                                  %+ rem  If the link still exists, it's good & tested, and we're done!
:DEBUG      if isdir         %LINK_DIR%     echo  mklink /d %LINK_SOURCE% "%LINK_TARGET%" %+ rem  And then create the link
            if isdir         %LINK_DIR%           mklink /d %LINK_SOURCE% "%LINK_TARGET%" %+ rem  And then create the link
            gosub alertIfDNE %LINK_SOURCE% %LINK_TARGET_VARNAME%                          %+ rem  And then double check that it happened

        ::::: CREATE ADDITIONAL JUNCTION IF PASSED:
            if    ""   eq    "%ADDITIONAL_JUNCTION_1%" return
            if    not  isdir  %ADDITIONAL_JUNCTION_1%  junction %ADDITIONAL_JUNCTION_1% %LINK_SOURCE%     %+ rem  Yes, link SOURCE. We want to point to the official local junction, not to the actual repo. 2 junctions deep so half the maintenance.
            gosub alertIfDNE  %ADDITIONAL_JUNCTION_1%  %LINK_TARGET_VARNAME%

    return
    ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
    :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
    :RemoveBadSimlinks [link_source link_target LINK_TARGET_VARNAME additional_junction_1]
        :: DEBUG
            :: echo * GOSUB RemoveBadSimlinks [%link_source% %link_target% %additional_junction_1%]
            :: echo * link_source = %link_source% = truename[%link_source]: %@TRUENAME[%link_source%]
            :: echo * link_target = %link_target% = truename[%link_target]: %@TRUENAME[%link_target%]
            :: echo * addtl_junct = %additional_junction_1% = truename[%additional_junction_1%]: %@TRUENAME[%additional_junction_1%]

        :: if we are only checking for one link, and it doesn't exist, we can't possibly remove it:
            if not isdir %link_source% .and. "" eq "%ADDITIONAL_JUNCTION_1%" (if "%DEBUG%" eq "1" echo [debug] reason 1 %+ return)

        :: if we are only checking for more one link, and none of them exist, we can't possibly remove anything:
            if not isdir %link_source% .and. not isdir %ADDITIONAL_JUNCTION_1% (if "%DEBUG%" eq "1" echo [debug] reason 2 %+ return)

        :: if the proper target we want is not where the primary junction is currently pointing, then it's an expired location. Remove it.
            if "%@UPPER[%@TRUENAME[%link_target%]]" ne "%@UPPER[%@TRUENAME[%link_source%]]" (if "%DEBUG%" eq "1" echo [debug] reason 3 %+ goto :Remove_YES)

        :: if there are no additional junctions to evaluate, everything is good! We're done!
            if "%ADDITIONAL_JUNCTION_1" eq "" (if "%DEBUG%" eq "1" echo [debug] reason4 %+ return)

        :: if there ARE additional junctions to evaluate, we need to see if those match the target as well:
            if "%@UPPER[%@TRUENAME[%link_target%]]" ne "%@UPPER[%@TRUENAME[%@TRUENAME[%additional_junction_1%]]]" (if "%DEBUG%" eq "1" echo [debug] reason 5 %+ goto :Remove_YES)

        :: if we got to here, everything is hunky-dory fine:
            return

        :: but if anything went wrong, we'd be directed here:
            :Remove_Yes
            %COLOR_WARNING%        %+  echos    * Symlink for %LINK_TARGET_VARNAME% seems invalid... 
            %COLOR_ADVICE%         %+  echo  ...You may want to: rd %link_source%
            if "%additional_junction_1%" ne "" .and. isdir  %additional_junction_1% (rd %additional_junction_1%)
            if isdir  %link_source%            (rd %link_source% >nul)
           :if isdir  %link_source%            (echo * FATAL ERROR: Could not RemoveBadSimlink [%link_source%]!!!!! %+ pause %+ pause %+ pause %+ quit)
            if "" eq "%additional_junction_1%" (return)
           :if isdir  %additional_junction_1%  (echo * ERROR: Could not RemoveBadSimlink [%additional_junction_1%]! %+ pause %+ pause) %+ rem we won't quit just yet - the secondary junction failing is a "nice to have", not a show-stopper
    return
    :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
	::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
	:alertIfDNE [dir link_target_varname]
		if isdir %dir% return
		echo * ERROR!: %dir% (%LINK_TARGET_VARNAME%) does not exist! %+ call white-noise 1 %+ pause
	return
	::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::



    :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
    :CreateAutomaticSymlinks
        :: it is most pleasing to the appearance to do ones present on more drives later
      		gosub MapSomethingByAllLetters %ALL_COLLECTIONS_DRIVE% %ALL_COLLECTIONS_BY_DRIVE%\LOGS         logs
      		gosub MapSomethingByAllLetters %ALL_COLLECTIONS_DRIVE% %ALL_COLLECTIONS_BY_DRIVE%\HARDWARE     hardware
      		gosub MapSomethingByAllLetters %ALL_COLLECTIONS_DRIVE% %ALL_COLLECTIONS_BY_DRIVE%\BACKUPS      backups
      		gosub MapSomethingByAllLetters %ALL_COLLECTIONS_DRIVE% %ALL_COLLECTIONS_BY_DRIVE%\MEDIA        media
		    gosub MapSomethingByAllLetters %ALL_COLLECTIONS_DRIVE% %ALL_COLLECTIONS_BY_DRIVE%\MOVIES       media\movies
		    gosub MapSomethingByAllLetters %ALL_COLLECTIONS_DRIVE% %ALL_COLLECTIONS_BY_DRIVE%\LIVE-SHOWS   media\live-shows
		    gosub MapSomethingByAllLetters %ALL_COLLECTIONS_DRIVE% %ALL_COLLECTIONS_BY_DRIVE%\CARTOONS     media\cartoons
            :::: these are to become our Plex library basis and easy way to get to things

    return
	:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
	:MapSomethingByAllLetters [basedrive base whattolookfor]
        :: Say what we're doing
            echo. %+ echo. %+ echo. %+ echo. 
            color bright magenta on black %+ Echo *** Generating links in for all %@UPPER[%whattolookfor] in the house into: %base% ***
            color bright   green on black

        :: then do it
    		:or %1 in (%THE_ALPHABET%) gosub MapSomethingByLetter %1 %ALL_COLLECTIONS_DRIVE% %ALL_MEDIA_BY_DRIVE%\%@UPPER[%WHATTOLOOKFOR%] %whattolookfor%
    		for %1 in (%THE_ALPHABET%) gosub MapSomethingByLetter %1 %letter% %basedrive% %base% %whattolookfor%
    return
	::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
	:MapSomethingByLetter [letter basedrive base whattolookfor]

        :: Check if drive ready
            if "%@READY[%letter%]" ne "1"  (color bright red on black %+ echo * Drive %letter%: NOT ready... %+ color bright green on black %+ goto :MapSomethingByLetterReturn)
            color bright green on black %+ echos * Drive %letter%:  is ready...
            :DEBUG: echo looking for %whattolookfor with base %base on drive %basedrive letter for %letter - i.e. %letter%:\%whattolookfor%\

        :: Don't link to self! That will create inifinte loops!
            :: 1) Say we are building c:\%whattolookfor%\by-letter\ on all computers. 
            ::    We can't have c:\%whattolookfor%\by-letter\ point to a letter that is another computer's C: or it will become infinite
            :: 2) Say we are building c:\%whattolookfor%\ on this computer - we can't create a link to C: or it will become infinite
            :: 3) Say we are building c:\%whattolookfor%\ on this computer - we can't create a link to P: if P: maps to C:  and is actually C:, or it will become infinite
                for %computer in (%ALL_COMPUTERS%) if "%@UPPER[%[%letter]]" eq "%@UPPER[%[%[DRIVE_C_%computer%]]]" (set SAME=%computer% %+ goto :SameDriveAnotherComputer_YES)
                if "%@UPPER[%BASEDRIVE%]" eq     "%@UPPER[%letter%]"   goto :SameDrive_YES
                if "%@UPPER[%BASEDRIVE%]" eq "%[%[%@UPPER[%letter%]]]" goto :SameDrive_YES
                                                                       goto :SameDrive_NO    %+rem  At this point, it's a safe drive to link to:
                            :SameDrive_YES
                                echos and %+ color bright yellow on black %+ echos  NOT %+ color bright green on black %+ echo  linked, because it's the same drive as %BASEDRIVE%:.            %+ return
                            :SameDriveAnotherComputer_YES
                                echos and %+ color bright yellow on black %+ echos  NOT %+ color bright green on black %+ echo  linked, because it's the same drive as %BASEDRIVE%: on %SAME%.  %+ return
                            :SameDrive_NO

        :: Make the base folder if it doesn't exist
            if not isdir "%BASE%" md "%BASE%"

        :: Continue
            if not isdir %letter%:\%whattolookfor%\ if isdir "%BASE%"\%letter% rd "%BASE%"\%letter%
            if not isdir %letter%:\%whattolookfor%\ if isdir "%BASE%"\%letter% rd "%BASE%"\%letter%
            if     isdir %letter%:\%whattolookfor%\ goto :Recreate_Yes
                                                    goto :Recreate_No
                :Recreate_Yes
                    if isdir "%BASE%"\%letter%  rd "%BASE%"\%letter%
             :echo  mklink   "%BASE%"\%letter%              %letter%:\%whattolookfor%\ 
                    mklink   "%BASE%"\%letter%              %letter%:\%whattolookfor%\ >nul
                    color bright green on black %+ echo and was linked. %+ color green on black                                
                    goto :MapSomethingByLetterReturn
                :Recreate_NO
                    color bright green  on black %+ echos and 
                    color bright yellow on black %+ echos  NOT 
                    color bright green  on black %+ echos  linked 
                    color        green  on black %+ echos  (no %whattolookfor%)
                    color bright green  on black %+ echo .
                    color        green  on black                                
                    goto :MapSomethingByLetterReturn

	:MapSomethingByLetterReturn
	return
	::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
	::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:::	:MapMediaByLetterOLD [letter]
:::        :: Local variable names
:::            set BASEDRIVE=%ALL_COLLECTIONS_DRIVE%
:::            set BASE=%ALL_MEDIA_BY_DRIVE%
:::
:::        :: Check if drive ready
:::            if "%@READY[%letter%]" ne "1"  (color bright red on black %+ echo * Drive %letter% is NOT ready... %+ color bright green on :::black %+ goto :MapMediaByLetterReturn)
:::            color bright green on black %+ echos * Drive %letter% is ready...
:::
:::        :: Don't link to self! That will create inifinte loops!
:::            :: Say we are building c:\media\by-letter\ on all computers. 
:::            :: We can't have c:\media\by-letter\ point to a letter that is another computer's C: or it will become infinite
:::                for %computer in (%ALL_COMPUTERS%) if "%@UPPER[%[%letter]]" eq "%@UPPER[%[%[DRIVE_C_%computer%]]]" (set SAME=%computer% %+ :::goto :SameDriveAnotherComputer_YES)
:::            :: Say we are building c:\media\ on this computer - we can't create a link to C: or it will become infinite
:::                if "%@UPPER[%BASEDRIVE%]" eq     "%@UPPER[%letter%]"   goto :SameDrive_YES
:::
:::            :: Say we are building c:\media\ on this computer - we can't create a link to P: if P: maps to C:  and is actually C:, or it :::will become infinite
:::                if "%@UPPER[%BASEDRIVE%]" eq "%[%[%@UPPER[%letter%]]]" goto :SameDrive_YES
:::
:::            :: At this point, it's a safe drive to link to:
:::                goto :SameDrive_NO
:::
:::            :: React accordingly:
:::                    :SameDrive_YES
:::                        echos and %+ color bright yellow on black %+ echos  NOT %+ color bright green on black %+ echo  linked because :::it's the same drive as %BASEDRIVE%:. 
:::                        return
:::                    :SameDriveAnotherComputer_YES
:::                        echos and %+ color bright yellow on black %+ echos  NOT %+ color bright green on black %+ echo  linked because :::it's the same drive as %BASEDRIVE%: on %SAME%.
:::                        return
:::                    :SameDrive_NO
:::
:::        :: Make the base folder if it doesn't exist
:::            if not isdir "%BASE%" md "%BASE%"
:::
:::        :: Continue
:::            if not isdir %letter%:\media\ if isdir "%BASE%"\%letter% rd "%BASE%"\%letter%
:::            if not isdir %letter%:\media\ if isdir "%BASE%"\%letter% rd "%BASE%"\%letter%
:::            if     isdir %letter%:\media\ goto :Recreate_Yes
:::                                          goto :Recreate_No
:::                :Recreate_Yes
:::                    if isdir "%BASE%"\%letter%  rd "%BASE%"\%letter%
                       REM Actually create the symlink here:
:::                    mklink   "%BASE%"\%letter%              %letter%:\media\ >nul
:::                    color bright green on black %+ echo and was linked. %+ color green on black                                
:::                    goto :MapMediaByLetterReturn
:::                :Recreate_NO
:::                    color bright green  on black %+ echos and 
:::                    color bright yellow on black %+ echos  NOT 
:::                    color bright green  on black %+ echos  linked 
:::                    color        green  on black %+ echos  (no media)
:::                    color bright green  on black %+ echo .
:::                    color        green  on black                                
:::                    goto :MapMediaByLetterReturn
:::
:::	:MapMediaByLetterReturn
:::	return
:::	::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::




:END


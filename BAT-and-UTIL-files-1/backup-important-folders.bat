@loadbtm on
@Echo OFF
 on break cancel


rem SETUP:
        cls                                             
        call validate-in-path important divider randfg


rem START BANNER:
        call  important     "%BIG_TOP%Backing up important folders"   
        call  important     "%BIG_BOT%Backing up important folders" 
        echo.
        call  divider
        rem echo.
        echos  ``


rem MAIN:
        gosub backup_script  backup-Rogue_Legacy_2  "Rogue Legacy savegame"
        gosub backup_script  backup-Xenia           "Xenia emulator savegames"
        iff "%username%" eq "claire" then
                gosub backup_script  backup-clairecjs_utils "Python utility functions"
                gosub backup_script  backup-perl-libraries  "Perl %italics_on%site/lib%italics_off% libraries"
        endiff                
        rem b backup_script  backup-Rocksmith       "RockSmith savegame"      not implemented yet because Rocksmith is not created on DEMONA yet [get savegame from old 2019 backup when we do, THEN figure out this situation]



rem END BANNER:
    echo %@ANSI_MOVE_TO_COL[0]
    call  celebration   "Backups of important folders complete"
    call advice "RockSmith savegame backup not in use yet%DASH%use 'after RockSmith' command for one-off backing up of RockSmith saves"





goto :END
            :backup_script [script_name arg1]
                set BANNER_TEXT=%ANSI_COLOR_BRIGHT_YELLOW%Backing up %emphasis%%@REPLACE[_, ,%@REPLACE[backup-,,%script_name]]%deemphasis%...
                echos %@ANSI_MOVE_TO_COL[0]
                echo.
                echo %STAR% %BIG_TOP%%BANNER_TEXT%
                echo %STAR% %BIG_BOT%%BANNER_TEXT%
                echo.
                call validate-in-path %script_name%
                call                  %script_name% 
                call bigecho %CHECK%%CHECK%%CHECK% %BLINK_ON%%ANSI_COLOR_SUCCESS%%italics_on%%arg1%%italics_off% backup complete!%BLINK_OFF% %CHECK%%CHECK%%CHECK%
                echo.
                call randfg
                call divider
                echos  ``
                rem echo.
            return
:END

        
@Echo OFF


rem SETUP:
        cls                                             
        call validate-in-path important divider randfg


rem START:
        call  important     "%BIG_TOP%Backing up important folders"   
        call  important     "%BIG_BOT%Backing up important folders" 
        echo.
        call  divider


rem MAIN:
        gosub backup_script  backup-Rogue_Legacy_2  "Rogue Legacy savegame"
        gosub backup_script  backup-Xenia           "Xenia emulator savegames"


rem END:
    echo.
    call  celebration   "Backups of important folders complete"





goto :END
            :backup_script [script_name arg1]
                echo.
                call validate-in-path %script_name%
                call                  %script_name% 
                call bigecho %CHECK%%CHECK%%CHECK% %BLINK_ON%%ANSI_COLOR_SUCCESS%%italics_on%%arg1%%italics_off% backup complete!%BLINK_OFF% %CHECK%%CHECK%%CHECK%
                echo.
                call randfg
                call divider
            return
:END

        
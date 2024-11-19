@Echo Off
@on break cancel

:DESCRIPTION: sets various environment variables to the current day/moment in time


                     call yyyymmdd
                     call yyyymmdd(dow)
                     call yyyymmddhhmmss
                     call yyyymmdddow
if "%1" ne "noclip" (call yyyymmddclip) %+ rem Must fix clipboard prior to clopying things to it:
                     call mmddhhmmss



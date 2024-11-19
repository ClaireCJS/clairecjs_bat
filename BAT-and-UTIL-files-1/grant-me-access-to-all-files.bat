@on break cancel
@Echo oFF


echo About to do all the trick we know of to gain total ownershp and full access to all files and folders in %_CWD...

                        takeown /F .
for /a:d %1 in (*.*) do takeown /f "%1"
                        icacls    . /T /C /grant administrators:F System:F everyone:F
for /r   %f in (*.*) do SetACL -on "%f" -ot file -actn clear -clr dacl,sacl
                        takeown /F * /R /D  Y
                        icacls   *.* /T /C /grant %_winuser%:(D,WDAC)
                        icacls    .  /T /C /grant administrators:F System:F everyone:F



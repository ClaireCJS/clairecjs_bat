
:this one is mostly for the root folder:

                        takeown /F  .
for /a:d %1 in (*.*) do takeown /f "%1"
icacls                              .  /T /C /grant administrators:F System:F everyone:F

for /r %f in (*.*) do SetACL -on "%f" -ot file -actn clear -clr dacl,sacl
takeown /F * /R /D  Y
icacls   *.* /T /C /grant %_winuser%:(D,WDAC)
icacls    .  /T /C /grant administrators:F System:F everyone:F


@Echo OFF

                                                                                                  set SNIPPING_TOOL=C:\Windows\System32\SnippingTool.exe
if not exist "%SNIPPING_TOOL%" .and. exist %LOCALAPPDATA%\Microsoft\WindowsApps\SnippingTool.exe (set SNIPPING_TOOL=%LOCALAPPDATA%\Microsoft\WindowsApps\SnippingTool.exe)
                                                                   call validate-environment-variable SNIPPING_TOOL
                                                                                              start "%SNIPPING_TOOL%"


@Echo OFF

                                                          set SNIPPING_TOOL=C:\Windows\System32\SnippingTool.exe
if not exist "%SNIPPING_TOOL%" .and. exist something.exe (set SNIPPING_TOOL=??????????????)
                           call validate-environment-variable SNIPPING_TOOL
                                                       start %SNIPPING_TOOL%


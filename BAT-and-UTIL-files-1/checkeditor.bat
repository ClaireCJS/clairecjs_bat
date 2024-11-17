@Echo off
@on break cancel

:DESCRIPTION: validates whether %EDITOR% environment variable is set.  Basically the same as "call validate-environment-variable EDITOR" but with some special behavior

:start
        if "%EDITOR"=="" goto :uhoh1
        goto :were_fine

                :uhoh1
                        if exist "%ProgramFiles\EditPlus 2\editplus.exe" .and. exist "%ProgramFiles\EditPlus 2\editplus.exe" .and. exist "%BAT%\editplus.bat" set EDITOR=call editplus
                        if "%EDITOR"=="" goto :uhoh2
                        goto :were_fine

                :uhoh2
                        if exist "%UTIL\editpad.exe" set editor "%UTIL\editpad.exe"
                        if "%EDITOR"=="" goto :uhoh3
                        goto :were_fine

                :uhoh3
                        if exist "%UTIL\e\e.exe" set editor "%UTIL\e\e.exe"
                        if exist "%UTIL\e\e.exe" if exist "%BAT\e.bat" set editor "%BAT\e.bat"
                        if "%EDITOR"=="" goto :uhoh4
                        goto :were_fine

                :uhoh4
                        call warning "An editor must be defined!! Typically in c:\bat\environm.btm"
                        call warning "Let's hand-edit EDITOR temporarily in case you're in the middle of a script that you want to continue"
                        callw arning "But let's give you a chance to exit, first"
                        call exit-maybe
                        eset EDITOR
                        goto :start


:were_fine
:end

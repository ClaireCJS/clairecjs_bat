@Echo on

REM py2exe.bat is now a catch-all for the intent of EXE compling, which branches in
REM such a way that if we don't remember how to do things, they should still work

set FILE=%@UNQUOTE[%1]
set  EXT=%@EXT[%FILE]

call validate-environment-variable FILE

if "%EXT%" eq "spec" (
     REM call debug call "py.spec2exe.bat  %FILE%"
                    call  py.spec2exe.bat "%FILE%"
)

if "%EXT%" eq  "py"  (
    set SPEC=%@NAME[%FILE].spec
    if not exist "%SPEC%" call py2spec.bat     "%FILE%"
    if     exist "%SPEC%" call py.spec2exe.bat "%SPEC%"

)

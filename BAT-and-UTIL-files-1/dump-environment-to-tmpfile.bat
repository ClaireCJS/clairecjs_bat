@Echo OFF
@on break cancel

rem Validate environment:
        if %VALIDATED_DUMPENVTOTMPFILE ne 1 (
            call validate-in-path cut timer important set-tmp-file 
            set VALIDATED_DUMPENVTOTMPFILE=1
        )

unset /q TMPFILE_OLD
if defined TMPFILE set TMPFILE_OLD=%TMPFILE%

rem Get temporary filename:
        rem if not defined TMPFILE (call set-tmp-file)
        call set-tmp-file
        set env_dump_tmpfile=%tmpfile%

rem If it doesn't exist, or if we are forcing a re-dump, then do it:
        if not exist %env_dump_tmpfile% .or. "%2" eq "force" (
            call important "Dumping environment variables to %%env_dump_tmpfile%%..."
            rem timer /4 on
                
                rem 2.2 seconds: set|sed "s/=.*$//ig" >"%env_dump_tmpfile%" 👈👈👈🏻 If you uncomment this, don't forget to add sed to the list in validate-in-path above
                rem 0.0 seconds:
                set|:u8cut -d "=" -f1 >:u8"%env_dump_tmpfile%"

            rem timer /4 off
        )

if defined TMPFILE_OLD set TMPFILE=%TMPFILE_OLD%


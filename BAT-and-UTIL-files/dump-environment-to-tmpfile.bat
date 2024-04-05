@Echo OFF

rem Validate environment:
        if %VALIDATED_DUMPENVTOTMPFILE ne 1 (
            call validate-in-path cut timer important set-tmp-file 
            set VALIDATED_DUMPENVTOTMPFILE=1
        )

rem Get temporary filename:
        if not defined TMPFILE (call set-tmp-file)

rem If it doesn't exist, or if we are forcing a re-dump, then do it:
        if not exist %TMPFILE% .or. "%2" eq "force" (
            call important "Dumping environment variables to %%tmpfile%%..."
            rem timer /4 on
                
                rem 2.2 seconds: set|sed "s/=.*$//ig" >"%TMPFILE%" 👈👈👈🏻 If you uncomment this, don't forget to add sed to the list in validate-in-path above
                rem 0.0 seconds:
                set|cut -d "=" -f1 >"%TMPFILE%"

            rem timer /4 off
        )


@Echo OFF

REM     I actually do all my development for this in my personal live command line environment,
REM     so for me, these files actually "live" in "c:\bat\" and just need to be refreshed to my 
REM     local GIT repo beore doing anything significant.  Or really, before doing anything ever.


rem CONFIGURATION:
        rem SET MANIFEST_FILES=ingest_ics.py
        rem SET SECONDARY_BAT_FILES=ics-ingest.bat update-from-BAT-via-manifest.bat  advice.bat print-message.bat validate-in-path.bat validate-environment-variables.bat validate-environment-variable.bat validate-env-var.bat white-noise.bat car.bat nocar.bat important.bat important_less.bat warning.bat error.bat fatalerror.bat errorlevel.bat randcolor.bat success.bat celebration.bat debug.bat randfg.bat randbg.bat py2exe.bat

        SET MANIFEST_FILES=install-common-programs-with-winget.bat
        
        set SECONDARY_UTIL_FILES=


call update-from-BAT-via-manifest


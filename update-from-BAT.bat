@Echo OFF

REM     I actually do all my development for this in my personal live command line environment,
REM     so for me, these files actually "live" in "c:\bat\" and just need to be refreshed to my 
REM     local GIT repo beore doing anything significant.  Or really, before doing anything ever.


rem CONFIGURATION:

        SET MANIFEST_FILES=
        
        set SECONDARY_BAT_FILES=install-common-programs-with-winget.bat set-colors.bat bigecho.bat print-message.bat advice.bat celebration.bat debug.bat download-youtube-album.bat error.bat errorlevel.bat fatalerror.bat important.bat important_less.bat less_important.bat logging.bat none.bat print-if-debug.bat print-message.bat removal.bat set-randomfile.bat subtle.bat success.bat unimportant.bat warning.bat warning_soft.bat validate-in-path.bat validate-environment-variables.bat validate-environment-variable.bat validate-env-var.bat update-from-BAT-via-manifest.bat white-noise.bat randcolor.bat randfg.bat randbg.bat emoji-search.bat emoji.env set-emojis.bat



call c:\bat\update-from-BAT-via-manifest
call git add *.bat



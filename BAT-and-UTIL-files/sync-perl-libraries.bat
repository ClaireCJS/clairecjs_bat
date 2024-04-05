@Echo OFF

rem Validate the environment
        call validate-environment-variables PERL_OFFICIAL_SITELIB_ALL PERL_OFFICIAL_SITELIB_ALL_PATH 


rem Sync our libraries to every drive letter that has them:
        set OPTION_SKIP_SAME_C=1
        set OPTION_ECHO_RAYRAY=1
        call all-ready-drives "if exist DRIVE_LETTER:%PERL_OFFICIAL_SITELIB_ALL_PATH% copy /e /w /u /s /a: /[!.git *.bak] /h /z /k /g %PERL_OFFICIAL_SITELIB_ALL% DRIVE_LETTER:%PERL_OFFICIAL_SITELIB_ALL_PATH%"


rem Commit them to any GIT library that may exist, while handling our convention of suppressing-pauses-by-environment-variable, since our git-commit wrapper has pauses for interactive uses:
        set NOPAUSE_OLD=%NOPAUSE%
            set NOPAUSE=1
                call git-commit %*
            set NOPAUSE=0
        set NOPAUSE=%NOPAUSE_OLD%


rem Backup libraries to cloud:
        rem Let's stop using our shell account: call wzzip -r -p -u %WWWCL\private\perlsitelib.zip c:\perl\site\lib\  %+ echo asdf | call auto-ftp nopause
        rem And start using our dropbox account:
                rem OLD: call wzzip -r -p -u %DROPBOX\BACKUPS\PERL\perlsitelib.zip c:\perl\site\lib\ 
                call sync-perlsitelib-to-dropbox

rem Exit if told to:
        call exit-after %* 


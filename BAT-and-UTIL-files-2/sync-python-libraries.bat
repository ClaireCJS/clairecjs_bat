@Echo OFF
@on break cancel

rem Validate the environment
        call validate-environment-variables PYTHON_OFFICIAL_PATH PYTHON_OFFICIAL_SITELIB_ALL PYTHON_OFFICIAL_SITELIB_CLAIRE PYTHON_OFFICIAL_SITELIB_CLAIRE_PATH


call important "%italics_on%Synchronizing %underline_on%Python%underline_off% libraries%italics_off% to all prepared harddrives %DASH% and then to %italics_on%Dropbox%italics_off%"


rem Sync our libraries to every drive letter that has them:
        set OPTION_SKIP_SAME_C=1
        set OPTION_ECHO_RAYRAY=1
        call all-ready-drives "if exist DRIVE_LETTER:%PYTHON_OFFICIAL_PATH% *copy /e /w /u /s /a: /[!.git *.bak] /h /z /k /g %PYTHON_OFFICIAL_SITELIB_CLAIRE% DRIVE_LETTER:%PYTHON_OFFICIAL_SITELIB_CLAIRE_PATH%"
        rem gotta use *copy and not copy because my copy post process runs python which locks some of the very library files we try to sync 😂


rem Commit them to any GIT library that may exist, while handling our convention of suppressing-pauses-by-environment-variable, since our git-commit wrapper has pauses for interactive uses:
        echo.
        call divider big
        if "%1" eq "nogit" .or. "%MACHINENAME%" ne "%MACHINENAME_SCRIPT_AND_DROPBOX_AUTHORITY=%" (goto :nogit)
        set NOPAUSE_OLD=%NOPAUSE%
            set NOPAUSE=1
                call git-commit %*
            set NOPAUSE=0
        set NOPAUSE=%NOPAUSE_OLD%
        echo.
        call divider big
        :nogit


rem Backup libraries to cloud: For Python——unlike perl——we only back up our PERSONAL libraries, not the whole site-lib:
        call sync-python-personal-libaries-to-dropbox

rem Exit if told to:
        call exit-after %* 


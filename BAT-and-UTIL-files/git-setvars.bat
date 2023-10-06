@Echo OFF

if %1                        eq "force" goto :MAIN
if %GIT_SETVARS_DONE_ALREADY eq    1    goto :END


:MAIN

        unset /q GIT_OPTIONS_TEMP

        set GITHUB_USERNAME=clairecjs


        set                                 GIT_SSL_CAINFO=%UTIL2%\git\mingw64\etc\ssl\certs\ca-bundle.crt
        call validate-environment-variables GIT_SSL_CAINFO UTIL MP3 MP3VERSIONING GITHUB_USERNAME

        :::: OPTIONS-BY-FOLDER:
            if "%_CWD"              eq "%UTIL%" (SET GIT_OPTIONS_TEMP=--git-dir=C:\UTIL-git-repo --work-tree=c:\UTIL)
            if "%_CWD"              eq "%MP3%"  (SET GIT_OPTIONS_TEMP=--git-dir=%MP3VERSIONING%  --work-tree=%MP3%)
            if "%_CWP"              eq "\mp3"   (SET GIT_OPTIONS_TEMP=--git-dir=%MP3VERSIONING%  --work-tree=%MP3%)

        :::: LET USER SEE WHAT OPTIONS WERE SET:
            if "%GIT_OPTIONS_TEMP%" ne ""       (%COLOR_DEBUG% %+ echo * Added additional GIT options: "%GIT_OPTIONS_TEMP%" %+ %COLOR_NORMAL%)


        set GIT_SETVARS_DONE_ALREADY=1

:END
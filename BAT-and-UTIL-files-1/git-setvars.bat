@on break cancel
@Echo OFF

rem CONSTANTS:
        set GITHUB_USERNAME=clairecjs


rem SET OPTIONS BY WHAT FOLDER WE'RE IN:
        unset /q GIT_OPTIONS_TEMP
        if "%_CWD"              eq "%UTIL%" (SET GIT_OPTIONS_TEMP=--git-dir=C:\UTIL-git-repo --work-tree=c:\UTIL)
        if "%_CWD"              eq "%MP3%"  (SET GIT_OPTIONS_TEMP=--git-dir=%MP3VERSIONING%  --work-tree=%MP3%  )
        if "%_CWP"              eq "\mp3"   (SET GIT_OPTIONS_TEMP=--git-dir=%MP3VERSIONING%  --work-tree=%MP3%  )
        if "%GIT_OPTIONS_TEMP%" ne   ""     (call debug "Added additional GIT options: '%italics_on%%GIT_OPTIONS_TEMP%%italics_off%'")


rem VALIDATE ENVIRONMENT VARIABLES, BUT ONLY ONCE PER CONSOLE SESSION (BECAUSE IT TAKES TIME):
        if %1 eq "force"                   (goto :force)
        if  1 eq %GIT_SETVARS_DONE_ALREADY (goto :END  )
        :force
                set                                 GIT_SSL_CAINFO=%UTIL2%\git\mingw64\etc\ssl\certs\ca-bundle.crt
                call validate-environment-variables GIT_SSL_CAINFO GITHUB_USERNAME UTIL MP3 MP3VERSIONING 
                set GIT_SETVARS_DONE_ALREADY=1
        :END


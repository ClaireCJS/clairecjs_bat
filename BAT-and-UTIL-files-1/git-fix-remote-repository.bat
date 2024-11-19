@on break cancel
@Echo OFF

set THIS_DIR=%@NAME[%_CWD]
call validate-environment-variables GITHUB_USERNAME THIS_DIR
call validate-in-path git

rem  git remote set-url origin https://github.com/%GITHUB_USERNAME%/%THIS_DIR%.git
call git remote set-url origin https://github.com/%GITHUB_USERNAME%/%THIS_DIR%

           %color_success%
echos %ANSI_COLOR_SUCCESS%
call git remote -v 

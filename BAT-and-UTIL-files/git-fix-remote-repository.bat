@Echo OFF

set THIS_DIR=%@NAME[%_CWD]
call validate-environment-variables GITHUB_USERNAME THIS_DIR
call validate-in-path git

git remote set-url origin https://github.com/%GITHUB_USERNAME%/%THIS_DIR%.git

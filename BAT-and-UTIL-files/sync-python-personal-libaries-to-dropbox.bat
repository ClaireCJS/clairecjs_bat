@Echo OFF                                       

::::: VALIDATE ENVIRONMENT:
    call validate-environment-variable DROPBOX PYTHON_OFFICIAL_SITELIB_CLAIRE


::::: INVOCATION PATTERN FOR OUR FOLDERSYNC SCRIPT:
    set   SYNCSOURCE=%PYTHON_OFFICIAL_SITELIB_CLAIRE%
    set   SYNCTARGET=%DROPBOX%\BACKUPS\PROGRAMMING\Python\clairecjs_util\
    set   SYNCTRIGER=__ Python personal libraries last backed up to dropbox __
    call  sync-a-folder-to-somewhere.bat /[!.git *.bak]            



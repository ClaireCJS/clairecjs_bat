@Echo OFF                                       
@on break cancel

::::: VALIDATE ENVIRONMENT:
    call validate-environment-variables DROPBOX_CLAIRE PYTHON_OFFICIAL_SITELIB_CLAIRE


::::: INVOCATION PATTERN FOR OUR FOLDERSYNC SCRIPT:
    set   SYNCSOURCE=%PYTHON_OFFICIAL_SITELIB_CLAIRE%
    set   SYNCTARGET=%DROPBOX_CLAIRE%\BACKUPS\PROGRAMMING\Python\clairecjs_util\
    set   SYNCTRIGER=__ Python personal libraries last backed up to DROPBOX_CLAIRE __
    call  sync-a-folder-to-somewhere.bat /[!.git *.bak]            



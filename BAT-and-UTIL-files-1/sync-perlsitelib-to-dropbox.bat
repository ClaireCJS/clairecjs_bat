@Echo OFF                                       

::::: VALIDATE ENVIRONMENT:
        call validate-environment-variableS DROPBOX_CLAIRE PERL_OFFICIAL_SITELIB_ALL


::::: INVOCATION PATTERN FOR OUR FOLDERSYNC SCRIPT:
        set   SYNCSOURCE=%PERL_OFFICIAL_SITELIB_ALL%
        set   SYNCTARGET=%DROPBOX_CLAIRE%\BACKUPS\PROGRAMMING\Perl\site\
        set   SYNCTRIGER=__ Perl last backed up to DROPBOX_CLAIRE __
        call  sync-a-folder-to-somewhere.bat /[!.git *.bak]            



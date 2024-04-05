@Echo OFF                                       

::::: VALIDATE ENVIRONMENT:
    call validate-environment-variable DROPBOX PERL_OFFICIAL_SITELIB_ALL


::::: INVOCATION PATTERN FOR OUR FOLDERSYNC SCRIPT:
    set   SYNCSOURCE=%PERL_OFFICIAL_SITELIB_ALL%
    set   SYNCTARGET=%DROPBOX%\BACKUPS\PROGRAMMING\Perl\site\
    set   SYNCTRIGER=__ Perl last backed up to dropbox __
    call  sync-a-folder-to-somewhere.bat /[!.git *.bak]            



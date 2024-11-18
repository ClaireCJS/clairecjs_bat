@Echo OFF

::::: VALIDATE ENVIRONMENT:
        call validate-environment-variables PUBCL WINDIR DROPBOX 
        call validate-in-path               clean-dropbox warning sync-bat-to-dropbox sync-util-to-dropbox sync-TCC-to-dropbox sync-pub_journal-to-dropbox.bat sync-winamp-playlists-to-dropbox.bat

::::: WARN USER, AND PAUSE IF CHOSEN TO:
        call warning "This calls all the various sync-WHATEVER-to-dropbox type scripts."
        if "%AUTOEXEC%" ne "1" .and. "%1" ne "NOPAUSE" (pause)

::::: SYNC INDIVIDUAL FILES:
        if exist %PUBCL%\Jobs\references.txt         (echo r | *copy /u /r %PUBCL%\Jobs\references.txt         %DROPBOX%\BACKUPS\references.txt)
        if exist %windir%\system32\drivers\etc\hosts (echo r | *copy /u /r %windir%\system32\drivers\etc\hosts %DROPBOX%\BACKUPS\hosts.txt)

::::: SYNC FOLDERS:
        call sync-bat-to-dropbox.bat
        call sync-util-to-dropbox.bat
        call sync-TCC-to-dropbox.bat
        call sync-pub_journal-to-dropbox.bat
        call sync-perlsitelib-to-dropbox.bat
        :all sync-winamp-program-to-dropbox.bat         ::got unwieldy when the 50,000 milkdrop presets in 2020/05 brought this up to 1G
        :all sync-winamp-program-to-burn-workflow.bat   ::we stopped doing this when winamp moved into UTIL2 and became mega-backed-up by default
        call sync-winamp-playlists-to-dropbox.bat


::::: CLEAN DROPBOX:
        call clean-dropbox
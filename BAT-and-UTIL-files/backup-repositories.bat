@Echo Off


::::: PARAMETERS:
    unset /q BACKUPREPOSTARTER
    if "%1" eq "simultaneous" .or. "%1" eq "parallel" (set BACKUPREPOSTARTER=call startafter1secondpausewithexitafter %+ goto :Next_1)
    if "%1" ne "" (goto :%1)         %+ rem Quick way to pick up where we left off at a specific point
    :Next_1
    REM call print-if-debug "BackupRepoStarter is '%BACKUPREPOSTARTER%'"



::::: PRE-CLEAN:
    :call environm validate                                                                                %+ REM tempting, but let's not cause 1 fail to fail all
    call set-task "Running backups..."
    timer
    if "%BACKUP_REPO_PRECLEAN%" eq "1" (goto :PreCleaned_Already)
        call askyn "Run hitomi-assmilate?" no 10
        if %DO_IT eq 1 (
            call after hitomi                                                                                  %+ REM grab loose autodownloaded prn before backing up prn
            set BACKUP_REPO_PRECLEAN=1
        )
    :PreCleaned_Already


::::: BACKUP ALL KNOWN REPOSITORIES:                                                                       %+ REM to backup BAK files, you will need to edit backup-repository.bat
set BACKING_UP_MULTIPLE_REPOSITORIES=1
%BACKUPREPOSTARTER% call backup-repository PROGRAMMING_SANDBOX       PROGRAMMING_SANDBOX_BACKUP
%BACKUPREPOSTARTER% call backup-repository PYTHON_CLAIRE                   PYTHON_CLAIRE_BACKUP
%BACKUPREPOSTARTER% call backup-repository PERL_CLAIRE                       PERL_CLAIRE_BACKUP
%BACKUPREPOSTARTER% call backup-repository PROGRAMMING                       PROGRAMMING_BACKUP
%BACKUPREPOSTARTER% call backup-repository NEWCL                                   NEWCL_BACKUP_1
%BACKUPREPOSTARTER% call backup-repository NEWCL                                   NEWCL_BACKUP_2
%BACKUPREPOSTARTER% call backup-repository NEWCAS                                 NEWCAS_BACKUP
%BACKUPREPOSTARTER% call backup-repository NEWPICTURES                        NEWPICTURESBACKUP
%BACKUPREPOSTARTER% call backup-repository REVIEWDIR                            REVIEWDIRBACKUP            %+ REM 2022/03/20 - 6.4TB nowhere big enough to copy it :/
%BACKUPREPOSTARTER% call backup-repository PREBURN_DVD                       PREBURN_DVD_BACKUP
%BACKUPREPOSTARTER% call backup-repository PREBURN_BDR                       PREBURN_BDR_BACKUP
%BACKUPREPOSTARTER% call backup-repository DELETEAFTERWATCHING        DELETEAFTERWATCHINGBACKUP
%BACKUPREPOSTARTER% call backup-repository LYRICS                                 LYRICS_BACKUP GIT
%BACKUPREPOSTARTER% call backup-repository LOGS                                     LOGS_BACKUP
%BACKUPREPOSTARTER% call backup-repository IRC                                        IRCBACKUP
%BACKUPREPOSTARTER% call backup-repository GROSS                                    GROSSBACKUP
%BACKUPREPOSTARTER% call backup-repository EYECANDY                              EYECANDYBACKUP            %+ REM wiped out in Andrea(R:)/S:/T: harddrive crashes... starting again in 2022 & it fucking sucks!
%BACKUPREPOSTARTER% call backup-repository PUBCL                                    PUBCLBACKUP
%BACKUPREPOSTARTER% call backup-repository PUBCAS                                  PUBCASBACKUP
%BACKUPREPOSTARTER% call backup-repository WWWCL                                   WWWCL_BACKUP
%BACKUPREPOSTARTER% call backup-repository WWWCAS                                 WWWCAS_BACKUP
%BACKUPREPOSTARTER% call backup-repository MP3OFFICIAL                                MP3BACKUP1
%BACKUPREPOSTARTER% call backup-repository MP3OFFICIAL                                MP3BACKUP2
%BACKUPREPOSTARTER% call backup-repository MP3OFFICIAL                                MP3BACKUP3
%BACKUPREPOSTARTER% call backup-repository MP3VERSIONING                    MP3VERSIONINGBACKUP
%BACKUPREPOSTARTER% call backup-repository MP3AUX                                  MP3AUXBACKUP
%BACKUPREPOSTARTER% call backup-repository MP3AUX                                  MP3AUXBACKUP
:games
%BACKUPREPOSTARTER% call backup-repository GAMES_DEMONA                     GAMES_DEMONA_BACKUP            %+ REM added 2023/09/18
%BACKUPREPOSTARTER% call backup-repository GAMES                                    GAMESBACKUP            %+ REM 2022/02/18 -  167G 
:pictures
%BACKUPREPOSTARTER% call backup-repository PICTURES                             PICTURES_BACKUP_1
%BACKUPREPOSTARTER% call backup-repository PICTURES                             PICTURES_BACKUP_2
%BACKUPREPOSTARTER% call backup-repository EMULATION                            EMULATIONBACKUP            %+ REM 2022/02/18 - ~850G 
%BACKUPREPOSTARTER% call backup-repository INSTALLFILES                      INSTALLFILESBACKUP
%BACKUPREPOSTARTER% call backup-repository COMICS                                 COMICS_BACKUP
%BACKUPREPOSTARTER% call backup-repository MUSICVIDEOS                        MUSICVIDEOSBACKUP
%BACKUPREPOSTARTER% call backup-repository HARDWARE_THAILOG             HARDWARE_THAILOG_BACKUP            %+ REM 2022/03/18 - this is the same as %HARDWARE_MAIN% / %HARDWARE%
:BACKUPREPOSTARTER% call backup-repository HARDWARE_GOLIATH             HARDWARE_GOLIATH_BACKUP            %+ REM 2022/03/18 - already contained in PUBCAS so unnecessary!
%BACKUPREPOSTARTER% call backup-repository EXTRAS                                 EXTRAS_BACKUP
%BACKUPREPOSTARTER% call backup-repository PRN1                                     PRN1_BACKUP            %+ REM 2022/03/17 - 2.2TB 
:BACKUPREPOSTARTER% call backup-repository PRN2                              [IS PART OF NEWCL]            %+ REM 2022/03/18 - no need to backup as it's part of %NEWCL%
:BACKUPREPOSTARTER% call backup-repository FTP                                       FTP_BACKUP            %+ REM 2024/03/19 - moved this to be part of PUBCL so no longer needs own backup job
%BACKUPREPOSTARTER% call backup-repository TEXT                                     TEXT_BACKUP 
%BACKUPREPOSTARTER% call backup-repository COMMERCIALS                       COMMERCIALS_BACKUP
%BACKUPREPOSTARTER% call backup-repository COMEDY                                 COMEDY_BACKUP
%BACKUPREPOSTARTER% call backup-repository IMAGES                                 IMAGES_BACKUP            %+ REM %ICONS% are a subset of images
%BACKUPREPOSTARTER% call backup-repository MISCDATA                             MISCDATA_BACKUP
%BACKUPREPOSTARTER% call backup-repository SHORTS                                 SHORTS_BACKUP
%BACKUPREPOSTARTER% call backup-repository SUBGENIUS                           SUBGENIUS_BACKUP
%BACKUPREPOSTARTER% call backup-repository CELEBRITIES                       CELEBRITIES_BACKUP
%BACKUPREPOSTARTER% call backup-repository MEDIA_FOR_OTHER_PEOPLE MEDIA_FOR_OTHER_PEOPLE_BACKUP
%BACKUPREPOSTARTER% call backup-repository DOCUMENTARIES                   DOCUMENTARIES_BACKUP            %+ REM %SPECIALS% and %DOCUMENTARIES% are the same repo

::::::these can always be re-generated, so is there really a point?: (could roll a die and do it 1 in 20 times)
:call backup-repository PICTURES480X243               PICTURES480X243_BACKUP           %+ REM 20220404: regenerating
:call backup-repository PICTURES800x480               PICTURES800x480_BACKUP           %+ REM 20220404:  ~6G
:call backup-repository PICTURES800x600               PICTURES800x600_BACKUP           %+ REM 2017xxxx:  ~8G
:call backup-repository PICTURES800x600NP           PICTURES800x600NP_BACKUP           %+ REM 2017xxxx:  ~7.6G
:call backup-repository PICTURES1024x600             PICTURES1024x600_BACKUP           %+ REM 2017xxxx:  ~8.9G
:call backup-repository PICTURES1024x768             PICTURES1024x768_BACKUP           %+ REM 2017xxxx: ~12G



::::::::: ADD ROCKSMITH? BUT IT'S DONE IN GAMES....
:::::::::::: ADD - torrent stuff from backup-utorrent
:::::::::::: backup-stuff.bat probably doesn't have much

:::::::::::::::::::: NOT SURE IF I WILL DO THIS ONES:
:::::                 set                  ANIME=%ANIMEDRIVE%:\MEDIA\ANIME

set BACKING_UP_MULTIPLE_REPOSITORIES=0
timer

call success



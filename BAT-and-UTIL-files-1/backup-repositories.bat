@Echo Off
 on break cancel

:DESCRIPTION: Backup management script to ensure that all repositories are properly backed up

:USAGE:      Three valid invocations:
:USAGE:
:USAGE:       1) backup-repositories ——————————— backs up all repositories  slowly, one at    a     time, in  one window
:USAGE:
:USAGE:       2) backup-repositories parallel —— backs up all repositories quickly, all at the same time, in many windows
:USAGE:
:USAGE:       3) backup-repositories {label}  —— attempts a 'goto' command to specified label within this script, which may or may not exist
:USAGE:                                       —— example: "backup-repositories mp3" jumps to the :mp3 label added right before backing up mp3s
:USAGE:                                       ——————— This feature is used for both impatience, and debugging ——————————





rem SETUP:
         unset /q BACKUPREPOSTARTER


rem VALIDATE ENVIRONMENT:
        call validate-in-path backup-repository success set-task askyn after startafter1secondpausewithexitafter
        rem this was a bad idea: `call environm validate` —— because it would cause all backups to fail if ust one repo was down


rem PARAMETER PROCESSING —— allow "simultaneous" or "parallel" to quickly do them all in the same window:
        set goto=Normal
        if "%1" ne "simultaneous" .and. "%1" ne "parallel" .and. "%1" ne "" (set goto=%1)
        if "%1" eq "simultaneous"  .or. "%1" eq "parallel" (  set    BACKUPREPOSTARTER=call startafter1secondpausewithexitafter %+ goto :%goto%)
        if "%1" ne "simultaneous" .and. "%1" ne "parallel" (unset /q BACKUPREPOSTARTER                                          %+ goto :%goto%)         
        rem              call print-if-debug "BACKUPREPOSTARTER is '%BACKUPREPOSTARTER%'"


        
rem START DOING THE BACKUP:
        :Normal
        call set-task "Running backups..."
        timer

rem INTERACTION WITH ANOTHER BACKUP SCRIPT:
        if "%BACKUP_REPO_PRECLEAN%" eq "1" (goto :PreCleaned_Already)
            call askyn "Run hitomi-assmilate?" no 10                                                           %+ REM ask if we want to run this other backup script, but proceed if no answer is given in 10 seconds
            if %DO_IT eq 1 (call after hitomi %+ set BACKUP_REPO_PRECLEAN=1)
        :PreCleaned_Already


rem —————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
rem BACKUP ALL KNOWN REPOSITORIES:           Note that .bak files will not be backed up due to the configuration of backup-repository.bat
set BACKING_UP_MULTIPLE_REPOSITORIES=1
%BACKUPREPOSTARTER% call backup-repository NEWCL                                   NEWCL_BACKUP_1
%BACKUPREPOSTARTER% call backup-repository NEWCL                                   NEWCL_BACKUP_2
%BACKUPREPOSTARTER% call backup-repository NEWCAS                                 NEWCAS_BACKUP
%BACKUPREPOSTARTER% call backup-repository NEWPICTURES                        NEWPICTURESBACKUP
%BACKUPREPOSTARTER% call backup-repository REVIEWDIR                            REVIEWDIRBACKUP            %+ REM 2022/03/20 - 6.4TB nowhere big enough to copy it :/
%BACKUPREPOSTARTER% call backup-repository PREBURN_DVD                       PREBURN_DVD_BACKUP
%BACKUPREPOSTARTER% call backup-repository PREBURN_BDR                       PREBURN_BDR_BACKUP
%BACKUPREPOSTARTER% call backup-repository DELETEAFTERWATCHING        DELETEAFTERWATCHINGBACKUP
%BACKUPREPOSTARTER% call backup-repository LYRICS                                 LYRICS_BACKUP GIT
:programming
%BACKUPREPOSTARTER% call backup-repository PROGRAMMING_SANDBOX       PROGRAMMING_SANDBOX_BACKUP
%BACKUPREPOSTARTER% call backup-repository PYTHON_CLAIRE                   PYTHON_CLAIRE_BACKUP
%BACKUPREPOSTARTER% call backup-repository PERL_CLAIRE                       PERL_CLAIRE_BACKUP
%BACKUPREPOSTARTER% call backup-repository PROGRAMMING                       PROGRAMMING_BACKUP
%BACKUPREPOSTARTER% call backup-repository LOGS                                     LOGS_BACKUP
%BACKUPREPOSTARTER% call backup-repository IRC                                        IRCBACKUP
%BACKUPREPOSTARTER% call backup-repository GROSS                                    GROSSBACKUP
%BACKUPREPOSTARTER% call backup-repository EYECANDY                              EYECANDYBACKUP            %+ REM wiped out in Andrea-related (R:)/S:/T: harddrive crashes... starting again in 2022 & it sucks!
%BACKUPREPOSTARTER% call backup-repository PUBCL                                    PUBCLBACKUP
%BACKUPREPOSTARTER% call backup-repository PUBCAS                                  PUBCASBACKUP
%BACKUPREPOSTARTER% call backup-repository WWWCL                                   WWWCL_BACKUP
%BACKUPREPOSTARTER% call backup-repository WWWCAS                                 WWWCAS_BACKUP
:mp3
:music
%BACKUPREPOSTARTER% call backup-repository MP3OFFICIAL                                MP3BACKUP1
%BACKUPREPOSTARTER% call backup-repository MP3OFFICIAL                                MP3BACKUP2
%BACKUPREPOSTARTER% call backup-repository MP3OFFICIAL                                MP3BACKUP3
%BACKUPREPOSTARTER% call backup-repository MP3VERSIONING                    MP3VERSIONINGBACKUP
%BACKUPREPOSTARTER% call backup-repository MP3AUX                                  MP3AUXBACKUP
%BACKUPREPOSTARTER% call backup-repository MP3AUX                                  MP3AUXBACKUP
:games
%BACKUPREPOSTARTER% call backup-repository GAMES_DEMONA                     GAMES_DEMONA_BACKUP            %+ REM 2023/09/18 — added
%BACKUPREPOSTARTER% call backup-repository GAMES                                    GAMESBACKUP            %+ REM 2022/02/18 —  167G 
:pictures
%BACKUPREPOSTARTER% call backup-repository PICTURES                             PICTURES_BACKUP_1
%BACKUPREPOSTARTER% call backup-repository PICTURES                             PICTURES_BACKUP_2
%BACKUPREPOSTARTER% call backup-repository EMULATION                            EMULATIONBACKUP            %+ REM 2022/02/18 - ~850G, 2024/05/21 - 4.6TB
%BACKUPREPOSTARTER% call backup-repository INSTALLFILES                      INSTALLFILESBACKUP
%BACKUPREPOSTARTER% call backup-repository COMICS                                 COMICS_BACKUP
%BACKUPREPOSTARTER% call backup-repository MUSICVIDEOS                        MUSICVIDEOSBACKUP
:hardware
%BACKUPREPOSTARTER% call backup-repository HARDWARE_THAILOG             HARDWARE_THAILOG_BACKUP            %+ REM 2022/03/18 - currently, HARDWARE_MAIN == HARDWARE == HARDWARE_THAILOG
rem  UPREPOSTARTER% call backup-repository HARDWARE_GOLIATH             HARDWARE_GOLIATH_BACKUP            %+ REM 2022/03/18 - this repo is already contained in the PUBCAS repo, so this is unnecessary!
%BACKUPREPOSTARTER% call backup-repository EXTRAS                                 EXTRAS_BACKUP
%BACKUPREPOSTARTER% call backup-repository PRN1                                     PRN1_BACKUP            %+ REM 2022/03/17 - 2.2TB 
rem  UPREPOSTARTER% call backup-repository PRN2                              [IS PART OF NEWCL]            %+ REM 2022/03/18 - no need to backup as it's part of %NEWCL%
rem  UPREPOSTARTER% call backup-repository FTP                                       FTP_BACKUP            %+ REM 2024/03/19 - moved this to be within the PUBCL repo, so it no longer needs own backup job
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
rem KUPREPOSTARTER% call backup-repository ANIME                                   ANIME_BACKUP            %+ REM don't have the space for this
rem —————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
                     


rem —————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
rem These can always be re-generated, so is there really a point i backing them up? (could roll a die and do it 1 in 20 times):
        rem  UPREPOSTARTER% call backup-repository PICTURES480X243               PICTURES480X243_BACKUP           %+ REM 20220404: regenerating
        rem  UPREPOSTARTER% call backup-repository PICTURES800x480               PICTURES800x480_BACKUP           %+ REM 20220404:  ~6G
        rem  UPREPOSTARTER% call backup-repository PICTURES800x600               PICTURES800x600_BACKUP           %+ REM 2017xxxx:  ~8G
        rem  UPREPOSTARTER% call backup-repository PICTURES800x600NP           PICTURES800x600NP_BACKUP           %+ REM 2017xxxx:  ~7.6G
        rem  UPREPOSTARTER% call backup-repository PICTURES1024x600             PICTURES1024x600_BACKUP           %+ REM 2017xxxx:  ~8.9G
        rem  UPREPOSTARTER% call backup-repository PICTURES1024x768             PICTURES1024x768_BACKUP           %+ REM 2017xxxx: ~12G
rem —————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————



rem CLEAN/FINISH UP:
        set BACKING_UP_MULTIPLE_REPOSITORIES=0
        timer
        call success



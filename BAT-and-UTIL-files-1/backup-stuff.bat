@Echo on


call warning "DEPRECATED BACKUPS!"
call warning "DEPRECATED BACKUPS!"
call warning "DEPRECATED BACKUPS!"
call warning "DEPRECATED BACKUPS!"
call warning "DEPRECATED BACKUPS!"




::::: Make sure machine name is defined:
	call checkmachinename.bat
    title Backup stuff...

::::: Set variables:
	set MONTH=%_MONTH
	set BACKUPNODIR=BACKUP-%MACHINENAME-STUFF-%MONTH.zip
	set BACKUPDRIVE=c:
	set BACKUPDIR=backups
	set BACKUP=%BACKUPDRIVE\%BACKUPDIR\%BACKUPNODIR
	:20121015 added u to options for update instead:?
    :: wzzip pisses me off with its moneybegging        
        set ZIP=            call wzzip  -Pu -Jhrs         "%BACKUP"
        set ZIPRECURSE=     call wzzip -rPu -Jhrs         "%BACKUP"
        set ZIPRECURSENOAVI=call wzzip -rPu -Jhrs -x*.avi "%BACKUP"
        set ZIPRECURSENOLOG=call wzzip -rPu -Jhrs -x*.log "%BACKUP"
        set ZIPRECURSENOWAV=call wzzip -rPu -Jhrs -x*.wav "%BACKUP"
        set ALLFILES=*.*
    :: infozip
:       set             ZIP=infozip                    "%BACKUP"
:       set      ZIPRECURSE=infozip -r                 "%BACKUP"
:       set ZIPRECURSENOAVI=infozip -r --exclude *.avi "%BACKUP"
:       set ZIPRECURSENOLOG=infozip -r --exclude *.log "%BACKUP"
:       set ZIPRECURSENOWAV=infozip -r --exclude *.wav "%BACKUP"
:       set ALLFILES=*.*
    :: 7-zip
        set ZIPPER=7z
        set ADD=a
        set UPDATE=u
        set RECURSE=-r
        set EXCLUDE=-x!
        unset /q ALLFILES
        set             ZIP=%ZIPPER% %UPDATE% "%BACKUP"                         
        set      ZIPRECURSE=%ZIPPER% %UPDATE% "%BACKUP" %RECURSE%                
        set ZIPRECURSENOAVI=%ZIPPER% %UPDATE% "%BACKUP" %RECURSE% %EXCLUDE%*.avi 
        set ZIPRECURSENOLOG=%ZIPPER% %UPDATE% "%BACKUP" %RECURSE% %EXCLUDE%*.log 
        set ZIPRECURSENOWAV=%ZIPPER% %UPDATE% "%BACKUP" %RECURSE% %EXCLUDE%*.wav 

     
::::: Delete old backup:
	if exist "c:\recycled\%BACKUPNODIR" (*del /q "c:\recycled\%BACKUPNODIR" >nul)
	if exist "%BACKUP%"                 (*del /q "%BACKUP%"                 >nul)

:::: Make backup folder
	if isdir %BACKUPDIR% goto :dirExists
	%BACKUPDRIVE%
	if not exist \%BACKUPDIR% md \%BACKUPDIR%
	:dirExists

::::: Backup this stuff on all machines, then backup stuff specific to machine we're currently on:
	goto :backupCOMMON


    :pause

::::: Distribute backup file to other machines:
    if not exist %BACKUP% (echo * Uhoh, backup %BACKUP% does not exist %+ pause)
	:distribute
	c:
	cd \bat
	:call dist.bat %BACKUP noWAN
	::backup.bat is supposed to copy a file into \BACKUP\ on each and every computer:
	echos call backup.bat %BACKUP%...
          SET SEQUENTIAL_BACKUP=1
              call backup.bat %BACKUP%
          SET SEQUENTIAL_BACKUP=0
    echo ...done.

::::: Cleanup:
	unset /q BACKUP
	unset /q BACKUPNODIR
	unset /q ZIP
	unset /q ZIPRECURSE
	unset /q ZIPRECURSENOAVI
	unset /q ZIPRECURSENOLOG
	unset /q ZIPRECURSENOWAV
	goto :END

:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:backupCOMMON
	:for speed, it's best to arrange these in shortest to longest order 
	:(appending a short to a long takes longer than appending a long to a short)
	::too much ambiguity %ZIP% c:\*.txt c:\boot.ini c:\bat\%MACHINENAME\%ALLFILES% 
	if exist %SystemRoot\system32\inetsrv\MetaBase.bin %ZIP %SystemRoot\system32\inetsrv\MetaBase.bin
	if exist c:\4NT                          %ZIP               c:\4NT\%ALLFILES%
	if exist c:\TCMD                         %ZIP               c:\TCMD\%ALLFILES%
	if exist c:\MinGW                        %ZIP               c:\MinGW\%ALLFILES%
	if exist c:\WWW                          %ZIP               c:\WWW\%ALLFILES%
	if exist c:\WWW2                         %ZIP               c:\WWW2\%ALLFILES%
	if exist c:\girder                       %ZIP               c:\girder\%ALLFILES%
	if exist c:\ftp                          %ZIP               c:\ftp\%ALLFILES% 
    if exist "%ProgramFiles%\G6 FTP Server\" %ZIPRECURSENOAVI% "%ProgramFiles\G6 FTP Server\%ALLFILES%"
	if exist "%ProgramFiles%\EvilLyrics"     %ZIPRECURSE%      "%ProgramFiles\EvilLyrics\%ALLFILES%"   
	if exist "%ProgramFiles%"                %ZIPRECURSENOAVI% "%ProgramFiles\*.ini"  "%ProgramFiles\*.cfg"  "%ProgramFiles\*.ini" "C:\Users\oh\AppData\Local\Karen's Power Tools\Replicator\%ALLFILES%"
goto :backup%MACHINENAME
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:backupFIRE
	:(sites.dat=flashfxp settings,*.fqf=queue files)

	%ZIPRECURSENOAVI d:\www\*.pl d:\www\*.fmt d:\www\*.bat d:\www\*.txt d:\www\*.lst d:\www\*todo* d:\www\*.html d:\www\*.htm
	%ZIPRECURSENOAVI "d:\video\*.txt" "d:\video\*.msg" "d:\video\*.lst" "d:\video\*.bat" "%ProgramFiles\microsoft sql server\mssql\backup\%ALLFILES%"
	%ZIPRECURSENOLOG c:\mirc\ c:\mirc-gluttony\ c:\mirc-wrath\ c:\mirc-sloth\
goto :distribute
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:backupSTORM
	echo No STORM-specific backups are setup yet.
goto :distribute
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:backupHADES
	echo No HADES-specific backups are setup yet.
goto :distribute
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:backupDEMONA
	echo No DEMONA-specific backups are setup yet.
goto :distribute
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:backupWYVERN
	echo No WYVERN-specific backups are setup yet.
goto :distribute
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:backupHADES
	echo No HADES-specific backups are setup yet.
goto :distribute
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:backupTHAILOG
    :: TODO verify that these fucking attrib.lsts are actually backed up - maybe redo this whole damn thing.
    call validate-environment-variable MP3
	:removed 2020 or before:                              - %ZIPRECURSENOAVI %MP3\attrib.lst %MP3\*.m3u %MP3\_*
	:removed 20220218 as part of updating backup scripts - %ZIPRECURSE%     %MP3\attrib.lst 
goto :distribute
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:backupMIST
	%ZIPRECURSENOAVI  "c:\My Documents\layouts\%ALLFILES%" "c:\pda-backup\%ALLFILES%"
goto :distribute
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:backupHELL
	%ZIP c:\ftp\%ALLFILES% 
	%ZIPRECURSENOAVI "%ProgramFiles\sites.da*" "%ProgramFiles\*.fqf" c:\kaillera\%ALLFILES% "c:\inetpub\wwwroot\%ALLFILES%"
	%ZIPRECURSENOAVI c:\perl\site\lib\MP3 c:\perl\site\lib\Clio c:\perl\site\lib\Video c:\perl\site\lib\MPEG c:\perl\site\lib\RIFF c:\perl\site\lib\Image c:\perl\site\lib\DBD c:\perl\site\lib\DBI c:\perl\site\lib\RPC c:\perl\site\lib\bundle c:\perl\site\lib\auto 
	:don't have this existing here yet
	:%ZIPRECURSENOAVI d:\www\*.pl d:\www\*.fmt d:\www\*.bat d:\www\*.txt d:\www\*.lst d:\www\*todo* d:\www\*.html d:\www\*.htm
	:%ZIPRECURSENOAVI "d:\video\*.txt" "d:\video\*.msg" "d:\video\*.lst"  "%ProgramFiles\microsoft sql server\mssql\backup\%ALLFILES%"
	:storm now and it's just like c:\irc\ and i don't care as much %ZIPRECURSENOLOG c:\mirc\ c:\mirc-gluttony\ c:\mirc-wrath\ c:\mirc-sloth\
	%ZIPRECURSENOWAV c:\working\%ALLFILES% e:\working\%ALLFILES% f:\working\%ALLFILES%
	%ZIPRECURSENOAVI %WWW\%ALLFILES% c:\bat\short-stuff-to-encode.zip
	%ZIPRECURSENOAVI %PUB\class\%ALLFILES% %PUB\finance\%ALLFILES% %PUB\computing\%ALLFILES% %PUB\dreams\%ALLFILES% %PUB\connectivity\%ALLFILES% %PUB\pub\%ALLFILES% %PUB\cox\%ALLFILES% %PUB\cpp\%ALLFILES% %PUB\directions\%ALLFILES% %PUB\drugs\%ALLFILES% %PUB\finance\%ALLFILES% %PUB\holidays\%ALLFILES% %PUB\house\%ALLFILES% %PUB\icqsound\%ALLFILES% %PUB\insurance\%ALLFILES% %PUB\manuals\%ALLFILES% %PUB\people\%ALLFILES% %PUB\pub\%ALLFILES% %PUB\tests\%ALLFILES% %PUB\vehicles\%ALLFILES% %PUB\party %PUB\cpp %PUB\correspondence %PUB\journal %PUB\health %PUB\Games %PUB\Grandad %PUB\TV %PUB\Legal %PUB\Images %PUB\claims
	%ZIPRECURSENOAVI 
	%ZIP %MP3\*.lst c:\flashfxp\sites.dat c:\flashfxp\*.fqf c:\virtualdub\virtualdub.jobs %PUB\%ALLFILES% 
goto :distribute
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:END

call fix-window-title

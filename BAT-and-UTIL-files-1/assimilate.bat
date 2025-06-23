@Echo Off
 on break cancel

::::: CONFIGURATION:
    call validate-environment-variable MOVIE_WATCHED_OVERFLOW_DRIVE





::::: CONFIGURATION VALIDATION:
    call validate-environment-variable MOVIE_WATCHED_OVERFLOW_DRIVE

::::: Determine assimilate role:
        if "%@UPPER[%1]"    == "ALL"                                                             goto :ALL
	if "%@UPPER[%_CWP]" == "\DBCU" .or. "%1" == "dbcu"                                       goto :DropBoxCameraUploads
	if "%@UPPER[%_CWP]" == "\DROPBOX\CAMERA UPLOADS"                                         goto :DropBoxCameraUploads
	if "%@UPPER[%_CWP]" == "\NEW\P2P\BITTORRENT\OH"                                          goto :CompletedTorrentCopies
	if "%@UPPER[%_CWP]" ==         "\BITTORRENT\OH"                                          goto :CompletedTorrentCopies
	if "%@UPPER[%_CWP]" ==                "\INC\OH"                                          goto :CompletedTorrentCopies
	if "%@UPPER[%_CWD]" ==           "%DROPDIR%\OH"                                          goto :CompletedTorrentCopies
	if "%@UPPER[%_CWD]" == "%HD4000G6%:\MEDIA\FOR-REVIEW\DO_LATERRRRRRRRRRRRRRRRRRRRRRR\oh"  goto :CompletedTorrentCopies
	if "%@UPPER[%_CWD]" == "%NEWCL%"                                                         goto :NewCL
	if "%@UPPER[%_CWD]" == "%NEWPICS%"                                                       goto :NewPics
	if "%@UPPER[%_CWP]" == "\MEDIA\newpics" .or. "%@UPPER[%_CWP]" == "c:\newpics"            goto :NewPics
	if "%@UPPER[%_CWP]" == "\newpics"                                                        goto :NewPics
	if "%@UPPER[%_CWP]" == "\RSL\DONE"                                                       goto :RSLDone
	if "%@UPPER[%_CWP]" == "\RSL"                                                            goto :RSLDone
	if "%@UPPER[%_CWP]" == "\np"                                                             goto :NewPics
	if "%@UPPER[%_CWD]" == "%READYTODELETE%"                                                 goto :rtd1
	if "%@UPPER[%_CWD]" == "%HD2000G5%:\ABOUT-TO-BE-BURNED-DVD\READY-TO-DELETE"              goto :rtd1
	if "%@UPPER[%_CWD]" == "%READYTODELETE2ROOTALIAS%"                                       goto :AllBurned
	if "%@UPPER[%_CWD]" ==       "%HD250G%:\ABOUT-TO-BE-BURNED\DATA\READY-TO-DELETE"         goto :rtd2
	if "%@UPPER[%_CWD]" == "%HD2000G5%:\MEDIA\ABOUT-TO-BE-BURNED-DVD\READY-TO-BDR-BURN"	     goto :rtd2
	if "%@UPPER[%_CWD]" ==       "%HD2000G5%:\ABOUT-TO-BE-BURNED-DVD\READY-TO-BDR-BURN"	     goto :rtd2
	if "%@UPPER[%_CWD]" == "%HD2000G5%:\MEDIA\ABOUT-TO-BE-BURNED-DVD\DATA\READY-TO-BDR-BURN" goto :rtd2
	if "%@UPPER[%_CWD]" ==       "%HD2000G5%:\ABOUT-TO-BE-BURNED-DVD\DATA\READY-TO-BDR-BURN" goto :rtd2
	if "%@UPPER[%_CWD]" == "%READYTODELETEBDR%"                                              goto :rtd_vid_after_bluray_burn    %+ REM  ----- post bluray main video one ----
	if "%@UPPER[%_CWD]" ==       "%HD2000G5:\ABOUT-TO-BE-BURNED\DATA\READY-TO-DELETE"        goto :rtd_data_after_bluray_burn
	if "%@UPPER[%_CWD]" == "%HD2000G5:\MEDIA\ABOUT-TO-BE-BURNED\DATA\READY-TO-DELETE"        goto :rtd_data_after_bluray_burn
	if "%@UPPER[%_CWP]" == "\MEDIA\MOVIES"                                                   goto :mainMovieWatchingArea
	if "%@UPPER[%_CWD]" == "%HDG:\"                                                          goto :TEMPLATE

	goto :NoClueWhatToDo




::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:ALL
    :_incoming_stuffs
        call inc   %+ call assimilate
    :_new_cl
        call newcl %+ call assimilate
    :_dropbox camera uploads
        call dbcu  %+ call assimilate
    :_movie folders would not actually make sense because we need to space the _watched around
        :for %%d in (%THE_ALPHABET) echo if isdir %d%:\media\movies\ (pushd %+ %d%:\media\movies\ %+ call assimilate %+ popd)
           %HD10T1%:\media\movies\ %+ call assimilate %+ REM W:
           %HD10T2%:\media\movies\ %+ call assimilate %+ REM U:
           %HD18T1%:\media\movies\ %+ call assimilate %+ REM O:
        :%HD4000G6%:\media\movies\ %+ call assimilate %+ REM S: actually needs to hold on to a few of these
    :_newpics
        call newpics %+ call assimilate
    :_rtdVidAfterDVDBurn
        call rtd     %+ call assimilate
    :_rtdVidAfterBlurayBurn
        call rtd2    %+ call assimilate
goto :END
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


:::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:TEMPLATE
	gosub checkIfDir someFolderName
	:do something
goto :END
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::


:::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:RSLDone

set                                   SOURCE=c:\RSL\DONE
set                                   TARGET=%GAMES%\vr\Rookie PSVR
call validate-environment-variables   TARGET SOURCE
mv/ds %SOURCE%                      "%TARGET%"
if not isdir %SOURCE                  (md   %SOURCE%)

goto :END
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::


:::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:AllBurned
    call burned-assimilate
goto :END
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::

:::::::::::::::::::::::::::::::::::::::::
:NewCL
    call new-assimilate.bat %*
goto :END
:::::::::::::::::::::::::::::::::::::::::



::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:NewPics
        pushd .
                                 call dbcu
            %COLOR_IMPORTANT% %+ free
            %COLOR_REMOVAL%   %+ mv/ds *.dep %NEWPICS%
            %COLOR_IMPORTANT% %+ free
        popd
goto :END
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


:::::::::::::::::::::::::::::::::::
:rtd_vid_after_bluray_burn
    call burned-assimilate.bat %*
goto :END
:::::::::::::::::::::::::::::::::::

::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:mainMovieWatchingArea
	call checkmappings once
	set ERROR=0
	gosub checkIfDir _watched
	gosub checkIfDir  %MOVIE_WATCHED_OVERFLOW_DRIVE%:\MEDIA\MOVIES\_WATCHED\
	%COLOR_ALARM% %+ echo * ERROR is %ERROR %+ %COLOR_NORMAL%
	if "%ERROR" == "1" goto :END
	mv /ds _watched\* %MOVIE_WATCHED_OVERFLOW_DRIVE%:\MEDIA\MOVIES\_WATCHED\
	if not isdir _watched (md _watched)
	if isdir "3-D MOVIES" if exist "*3-D*" mv "*3-D*" "3-D MOVIES"
goto :END
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::



:::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:rtd1
	if exist catalog.txt     *del catalog.txt
	if exist catalog.txt.bak *del catalog.txt.bak
	call rtd-to-dbd2 %*
goto :END
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::

::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:rtd2
	if exist catalog.txt     *del catalog.txt
	if exist catalog.txt.bak *del catalog.txt.bak
	if not isdir %DATA2       goto :rtd2nodata2
	%COLOR_IMPORTANT%      %+ echo * Moving already-burned-to-dvd data to bluray-burn staging area.
	%COLOR_REMOVAL%        %+ mv/ds . %DATA2
	%COLOR_IMPORTANT%      %+ echo * Moved already-burned-to-dvd data to bluray-burn staging area.
    %COLOR_NORMAL%
	goto :END
			::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
			:rtd2nodata2
			%COLOR_ALARM% %+ echos %DATA2 must exist!
            %COLOR_NORMAL %+ echo.
			if "%@UPPER[%MACHINENAME%]" == "FIRE" (%COLOR_ADVICE% %+ echo Odds are this won't run on Fire. %+ %COLOR_NORMAL%)
			::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
goto :END
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::




::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:::: Incoming inc 
:CompletedTorrentCopies
	SET ANY_MOVED=0

    gosub CompletedTorrentCopies_HangoutShows %+ gosub CompletedTorrentCopies_ToWatchShows
    gosub CompletedTorrentCopies_HangoutShows %+ gosub CompletedTorrentCopies_ToWatchShows

    %COLOR_IMPORTANT%
    echo Show processing done....
    %COLOR_NORMAL%
    pause
 
    call r *
        pushd .
            call newcl
            call assimilate
        popd
goto :END
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
    ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
    :CompletedTorrentCopies_HangoutShows
	dir
        gosub CopyToDeleteAfterWatchingHangout  Adventure*time*
        gosub CopyToDeleteAfterWatchingHangout  Adult*swim*pilot*
        gosub CopyToDeleteAfterWatchingHangout  Adult*swim*infomercial*
        gosub CopyToDeleteAfterWatchingHangout  American*Dad*
        gosub CopyToDeleteAfterWatchingHangout  Aqua*teen*
        gosub CopyToDeleteAfterWatchingHangout  Assembly*line*yeah*
        gosub CopyToDeleteAfterWatchingHangout  Archer*
        gosub CopyToDeleteAfterWatchingHangout  Axe*Cop*
        gosub CopyToDeleteAfterWatchingHangout  black*dynamite*
        gosub CopyToDeleteAfterWatchingHangout  black*jesus*
        gosub CopyToDeleteAfterWatchingHangout  Bob*burgers*
        gosub CopyToDeleteAfterWatchingHangout  bojack*horseman*
        gosub CopyToDeleteAfterWatchingHangout *boondocks*
        gosub CopyToDeleteAfterWatchingHangout  bordertown*
        gosub CopyToDeleteAfterWatchingHangout  brickleberry*
        gosub CopyToDeleteAfterWatchingHangout  Check*it*out*
        gosub CopyToDeleteAfterWatchingHangout "children*hospital*"
        gosub CopyToDeleteAfterWatchingHangout "China,*IL - *"
        gosub CopyToDeleteAfterWatchingHangout  development?meeting*20*
        gosub CopyToDeleteAfterWatchingHangout  dream*corp*llc*
        gosub CopyToDeleteAfterWatchingHangout  drunk*history*
        gosub CopyToDeleteAfterWatchingHangout  Eagleheart*
        gosub CopyToDeleteAfterWatchingHangout *eric*andre*show*
        gosub CopyToDeleteAfterWatchingHangout  Family*guy*
        gosub CopyToDeleteAfterWatchingHangout  Fishcenter*live*
        gosub CopyToDeleteAfterWatchingHangout  Golan*insatiable*
        gosub CopyToDeleteAfterWatchingHangout  gravity*falls*
        gosub CopyToDeleteAfterWatchingHangout  king*star*king*
        gosub CopyToDeleteAfterWatchingHangout  lucas*bros*moving*company*
        gosub CopyToDeleteAfterWatchingHangout  MadTV*
        gosub CopyToDeleteAfterWatchingHangout *major*lazer*
        gosub CopyToDeleteAfterWatchingHangout  million*dollar*extreme*
        gosub CopyToDeleteAfterWatchingHangout  mike*tyson*mysteries*
        gosub CopyToDeleteAfterWatchingHangout  million*dollar*extreme*
        gosub CopyToDeleteAfterWatchingHangout  moonbeam*city*
        gosub CopyToDeleteAfterWatchingHangout  mr*pickles*
        gosub CopyToDeleteAfterWatchingHangout  newsreaders*
        gosub CopyToDeleteAfterWatchingHangout  off*the*air*
        gosub CopyToDeleteAfterWatchingHangout  rick*morty*
        gosub CopyToDeleteAfterWatchingHangout  robot*chicken*
        gosub CopyToDeleteAfterWatchingHangout  Samurai*Jack*
        gosub CopyToDeleteAfterWatchingHangout *Simpsons*
        gosub CopyToDeleteAfterWatchingHangout  son*of*zorn*
        gosub CopyToDeleteAfterWatchingHangout  superjail*
        gosub CopyToDeleteAfterWatchingHangout  squidbillies*
        gosub CopyToDeleteAfterWatchingHangout  south*park*
        gosub CopyToDeleteAfterWatchingHangout  the*awesomes*
        gosub CopyToDeleteAfterWatchingHangout  tim*and*eric*bed*time*stor*
        gosub CopyToDeleteAfterWatchingHangout  the*heart*she*holler*
        gosub CopyToDeleteAfterWatchingHangout  your*pretty*face*going*to*hell*
        gosub CopyToDeleteAfterWatchingHangout *venture*bros*
        gosub CopyToDeleteAfterWatchingHangout *powerpuff*girls*
        gosub CopyToDeleteAfterWatchingHangout  brad*neely*sclopio*
        gosub CopyToDeleteAfterWatchingHangout  Decker*Unclassified*
        :osub CopyToDeleteAfterWatchingHangout 
        :osub CopyToDeleteAfterWatchingHangout 
        :osub CopyToDeleteAfterWatchingHangout 
        :osub CopyToDeleteAfterWatchingHangout 
        :osub CopyToDeleteAfterWatchingHangout 
        :osub CopyToDeleteAfterWatchingHangout 
	echo.
	dir
	if "%ANY_MOVED%" == "1" goto :Moved_YES
	                        goto :Moved_NO
		:Moved_YES						
			 window restore
			 beep %+ beep
			 %COLOR_PROMPT% %+ echo. %+ echo Anything we missed for hangout? Ctrl-break now...

             %COLOR_NORMAL  %+ echo.
			 pause>nul
			 unset /q ANY_MOVED
		:Moved_NO
    return
    ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
    ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
    :CompletedTorrentCopies_ToWatchShows
        gosub CopyToDeleteAfterWatchingNormal   12*monkeys*S*E* 
        gosub CopyToDeleteAfterWatchingNormal  *avengers*assemble*
        gosub CopyToDeleteAfterWatchingNormal  *avengers*secret*wars*
        gosub CopyToDeleteAfterWatchingNormal  *avengers*ultron*revolution*
        gosub CopyToDeleteAfterWatchingNormal   ash*vs*evil*dead*
        gosub CopyToDeleteAfterWatchingNormal   beware*batman*
        gosub CopyToDeleteAfterWatchingNormal   better*call*saul*
        gosub CopyToDeleteAfterWatchingNormal   comic*book*men*
        gosub CopyToDeleteAfterWatchingNormal   crash*canyon*
        gosub CopyToDeleteAfterWatchingNormal   curb*enthusiasm*
        gosub CopyToDeleteAfterWatchingNormal  *doctor*who*s1[0-9]*
        gosub CopyToDeleteAfterWatchingNormal  *guardians*of*the*galaxy*
        gosub CopyToDeleteAfterWatchingNormal   heroes*reborn*
        gosub CopyToDeleteAfterWatchingNormal  *harmon*quest*
        gosub CopyToDeleteAfterWatchingNormal  *hulk*agents*of*s*m*a*s*h*
        gosub CopyToDeleteAfterWatchingNormal   john*glaser*loves*gear*
        gosub CopyToDeleteAfterWatchingNormal   jo*n*glaser*loves*gear*
        gosub CopyToDeleteAfterWatchingNormal   justice*league*action*
        gosub CopyToDeleteAfterWatchingNormal  *portlandia*
        gosub CopyToDeleteAfterWatchingNormal   Marvel*spider*man*
        gosub CopyToDeleteAfterWatchingNormal  *my*little*pony*                 %+ REM 20151019 Carolyn wants to know why quotes around this, so let's no quotes for awhile
        gosub CopyToDeleteAfterWatchingNormal   MLP*
        gosub CopyToDeleteAfterWatchingNormal   silicon*valley*
        gosub CopyToDeleteAfterWatchingNormal   space*dandy*
        gosub CopyToDeleteAfterWatchingNormal   star*wars*rebels*
        gosub CopyToDeleteAfterWatchingNormal   teenage*mutant*ninja*turtles*
        gosub CopyToDeleteAfterWatchingNormal   the*awesomes*
        gosub CopyToDeleteAfterWatchingNormal   the*muppets*
        gosub CopyToDeleteAfterWatchingNormal   trip*tank*
        gosub CopyToDeleteAfterWatchingNormal   tmnt*
        gosub CopyToDeleteAfterWatchingNormal  *ultimate*spider*man*
        gosub CopyToDeleteAfterWatchingNormal   w*bob*and*david*
        gosub CopyToDeleteAfterWatchingNormal   wander*yonder*
        gosub CopyToDeleteAfterWatchingNormal   *alking*dead*                          %+ REM The Walking Dead / The Talking Dead
        gosub CopyToDeleteAfterWatchingNormal   Z.Nation*
       :gosub CopyToDeleteAfterWatchingNormal  
       :gosub CopyToDeleteAfterWatchingNormal  
	echo.
	dir
		if "%ANY_MOVED%" == "1" goto :Moved_YES
		                        goto :Moved_NO
			:Moved_YES						
				 window restore
				 beep %+ beep
                 %COLOR_PROMPT%
                     echo.
                     echo Anything we missed for delete after watching? Ctrl-break now...
                     echo.
                     pause>nul
                 %COLOR_NORMAL%
				 unset /q ANY_MOVED
			:Moved_NO
    return
    ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::




:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:NoClueWhatToDo
	%COLOR_NORMAL% %+ echo. %+ echo.
    %COLOR_ALARM%  %+ echo I have no clue what to do right now in folder %_CWD               %+ echo.
    %COLOR_ADVICE% %+ echo %BAT\assimilate.bat needs to be edited with a CWD check for %_CWD %+ echo.
    %COLOR_NORMAL%
    pause
    pause
    pause
    pause
    pause
    pause
    pause
    pause
    pause
    pause
    pause
    pause
goto :END
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:CopyToDeleteAfterWatchingHangout [mask]
	set TARGET=%DELETEAFTERWATCHING%\HANGOUT
    %COLOR_IMPORTANT%
	gosub CopyIncomingVideoToTarget %mask% %target%
    %COLOR_NORMAL%
return
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:CopyToDeleteAfterWatchingNormal  [mask]
    if "%mask%" == "" goto :prereturn1
	set TARGET=%DELETEAFTERWATCHING%
    %COLOR_SUCCESS%
	gosub CopyIncomingVideoToTarget %mask% %target%
    %COLOR_NORMAL%
:prereturn1
return
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:CopyIncomingVideoToTarget [mask target]
	:OLD: if exist %MASK% cp %MASK% %TARGET%
	:OLD: if exist %MASK% mv %MASK% %DROPDIR%
	:NEW:
	:TODO: error out if not defined %TARGET%
    echos . 
	if not exist %MASK% return
    echo.

    set ANY_MOVED=1
    call yyyymmddhhmmss
    set  TMPDIR=%DROPDIR%\temp-%yyyymmddhhmmss%

                           :: stopped using as much color here so this could inherit different file-copying-colors from calling functions
                           if not isdir %TMPDIR% mkdir %TMPDIR%
                           mv       %MASK%    %TMPDIR%
    %COLOR_RUN%         %+ cp      %TMPDIR%   %TARGET%
    %COLOR_DEBUG%       %+ echo mv %TMPDIR%\* %DROPDIR%
    %COLOR_UNIMPORTANT% %+ mv      %TMPDIR%\* %DROPDIR%
    %COLOR_REMOVAL%     %+ *rd /Nt %TMPDIR%
    %COLOR_NORMAL%
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
return
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::::: data2 rtd
:rtd_data_after_bluray_burn
	call checkmappings once

    call validate-environment-variables MACHINENAME_SCRIPT_AND_DROPBOX_AUTHORITY_CDRIVE GROSS PUBCL COMICS COMEDY INSTALLFILES EMULATION IMAGES BOOKS TEXT HD750G

	if exist __* del /p __*
	if exist catalog.txt del catalog.txt

	if isdir BACKUPS *del /p BACKUPS\*.* /s
	if isdir BACKUPS  rd BACKUPS

	if exist *(PS2)*.iso    mv /ds *(PS2)*.iso   "%EMULATION%\Playstation 2"
	if isdir PS2            mv /ds PS2           "%EMULATION%\Playstation 2"
	if isdir PS3            mv /ds PS3           "%EMULATION%\Playstation 3"
	if isdir PS4            mv /ds PS4           "%EMULATION%\Playstation 4"
	if isdir WII            mv /ds WII           "%EMULATION%\Nintendo\Nintendo Wii"
	if isdir EMULATION      mv /ds EMULATION	  %EMULATION%
	if isdir IMAGES	        mv /ds IMAGES		  %IMAGES%
	if isdir BOOKS          mv /ds BOOKS		  %BOOKS%
	if isdir COMICS         mv /ds COMICS		  %COMICS%
	if isdir TXT            mv /ds TXT		      %TEXT%
	if isdir INSTALL-FILES  mv /ds INSTALL-FILES  %INSTALLFILES%
	if isdir ARTICLES       mv /ds ARTICLES       %TEXT%\ARTICLES

	if isdir 911          if isdir   %HD750G:\MEDIA\READY-TO-DELETE\SPECIALS-AND-DOCUMENTARIES\911 mv /ds 911            %HD750G:\MEDIA\READY-TO-DELETE\SPECIALS-AND-DOCUMENTARIES\911
	if isdir "EYE CANDY"  if isdir  "%HD750G:\MEDIA\READY-TO-DELETE\EYE CANDY"                     mv /ds "EYE CANDY"   "%HD750G:\MEDIA\READY-TO-DELETE\EYE CANDY"\
	if isdir DOCUMENTARY  if isdir  "%HD750G:\MEDIA\READY-TO-DELETE\SPECIALS-AND-DOCUMENTARIES"\   mv /ds DOCUMENTARY   "%HD750G:\MEDIA\READY-TO-DELETE\SPECIALS-AND-DOCUMENTARIES"\
	if isdir applications if isdir   %installfiles                                                 mv /ds applications   %INSTALLFILES%
	if isdir comedy       if isdir   %comedy                                                       mv /ds comedy         %COMEDY%
	if isdir subgenius    if isdir   %HD750g:\MEDIA\READY-TO-DELETE\SubGenius                      mv /ds subgenius      %HD750G:\MEDIA\READY-TO-DELETE\SubGenius
	if isdir comics       if isdir   %COMiCS%                                                      mv /ds comics         %COMICS%
	if isdir articles     if isdir   U:\media\txt\articles                                         mv /ds articles       U:\media\txt\articles
	if isdir PERSONAL     if isdir   "%PUBCL"                                                      mv /ds PERSONAL      "%PUBCL%"
	if isdir GROSS        if isdir   %GROSS%                                                       mv /ds GROSS          %GROSS%
	if isdir hardware     if isdir   %MACHINENAME_SCRIPT_AND_DROPBOX_AUTHORITY_CDRIVE%:\hardware\  mv /ds hardware       %MACHINENAME_SCRIPT_AND_DROPBOX_AUTHORITY_CDRIVE%:\hardware\
	if isdir "GAMES\BOARD GAMES" if isdir %GAMES% mv/ds "GAMES\BOARD GAMES" "%GAMES%\BOARD GAMES"
	if exist *.mobi                               mv    *.mobi               %BOOKS%
	if isdir Android                              mv/ds Android              %EMULATION%\Android

	if not isdir GAMES :Games_NO
        cd games
            if isdir "BOARD GAMES" if isdir %EMULATION%\"BOARD GAMES"          mv/ds "BOARD GAMES" %EMULATION%\"BOARD GAMES" 
            if isdir "Nintendo DS" if isdir %EMULATION%\Nintendo\"Nintendo DS" mv/ds "Nintendo DS" %EMULATION%\Nintendo\"Nintendo DS" 
            if exist xbox360*      if isdir %EMULATION%\"XBOX 360"             mv     xbox360*     %EMULATION%\"XBOX 360" 
        cd ..
    :Games_NO

	if exist MUSIC\*.zip *del /p MUSIC\*.zip
	if exist MUSIC\*.iso *del /p MUSIC\*.iso

	echo.
	echo.

	if isdir GAMES (%COLOR_WARNING% %+ echo %italics_on%GAMES%italics_off% folder requires individual dealing with - some stuff goes to %italics_on%\GAMES\%italics_off%, some to %italics_on%\INSTALL-FILES\GAMES\%italics_off%%ansi_color_normal% %+ %COLOR_NORMAL%)
goto :END
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::



::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:DropBoxCameraUploads
    call clean-dbcu

    :OLD: %COLOR_ADVICE% %+ echo * Dropbox Camera Uploads mode (also saves Google Drive space!) %+ %COLOR_NORMAL
    :OLD: 
    :OLD:     if not defined MEMES             (set             MEMES=%DROPBOX%\MEDIA\PICTURES\Memes )
    :OLD:     if not defined NEWPICSCREENSHOTS (set NEWPICSCREENSHOTS=%NEWPICS%\_SCREENSHOTS         )
    :OLD: 
    :OLD:     call validate-environment-variables PRN_NEW FILEMASK_PORN FILEMASK_VIDEO HARDWARE MEMES NEWPICSCREENSHOTS
    :OLD: 
    :OLD:     mv  p*;%FILEMASK_PORN% %PRN_NEW%
    :OLD:     mv _PORN\*             %PRN_NEW%
    :OLD:     mv _HARDWARE\*         %HARDWARE%
    :OLD:     mv _MEMES\*            %MEMES%
    :OLD:     mv _SCREENSHOTS\*      %NEWPICSCREENSHOTS%
    :OLD: 
    :OLD:     mv %FILEMASK_VIDEO%    %NEWPICS%
    :OLD: 
    :OLD:     if isdir dep (mv/ds dep c:\newpics)
    :OLD:  
    :OLD:     ::::: PERHAPS DO SOMETHING WITH PROCESSING THE LUMIX CAMERA PICTURES
    :OLD: 
    :OLD:     call sizes
goto :END
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

























	:######################################################################################### UTILITY FUNCTIONS - BEGIN
	::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
	:checkIfDir [dir]
		%COLOR_LOGGING% %+ echo * Checking if dir exists: %dir%
		if not isdir %dir (%COLOR_ALARM% %+ echo OH SHIT! %dir FOLDER DOESN'T EXIST! %+ set ERROR=1)
		%COLOR_SUCCESS% %+ echo * directory exists: %dir
	return
	::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
	:######################################################################################### UTILITY FUNCTIONS - END 





:END

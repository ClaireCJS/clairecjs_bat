@on break cancel
@echo off


:DESCRIPTION: ::::::::::::::::::::::::::::::::::: INDEX DIGITAL AUDIO ::::::::::::::::::::::::::::::::::::
:DESCRIPTION: Runs our perl script (developed over 25 year) that generates all our playlists.
:DESCRIPTION: A lot of personal maintenance/adjunct tasks have evolved in and out of this over the decades
:DESCRIPTION: ::::::::::::::::::::::::::::::::::: INDEX DIGITAL AUDIO ::::::::::::::::::::::::::::::::::::




:PRE_SETUP
	timer>nul
    rem  Validate the environment:
            call     validate-environment-variables  MP3OFFICIALDRIVE   MP3OFFICIAL 
            call     ensure-drive-is-mapped         %MP3OFFICIALDRIVE%
            rem OLD: validate-in-path                mchk mp3index generate-audio-playlists generate-filelists-by-attribute.pl create-all_m3u-playlists create-these_m3u-playlists 
            call     validate-in-path                mchk          generate-audio-playlists generate-filelists-by-attribute.pl generate_thesem3u_and_allm3u_playlists_in_folder.py
            call     checkusername
            cls
            timer /3 on



:DEFINE_VARIABLES
	SET MP3LISTDRIVE=%MP3OFFICIALDRIVE%
	SET MP3LIST=%MP3OFFICIAL%\lists\everything.m3u
	SET MP3LISTBAK=%MP3OFFICIAL%\lists\everything.m3u.old
	:ET RECENTLISTDIR=%MP3OFFICIAL%
	:ET RECENTLISTFILE=newest-files.m3u
	:ET RECENTLIST=%RECENTLISTDIR\%RECENTLISTFILE
	:ET RECENTLISTBAK=c:\recycled\recentlistbakmp3.delme
	:ET RECENTLISTPUB=%MP3OFFICIAL%\mp3-%USERNAME-new.htm
	SET                            NUM_RECENT_TO_KEEP=4000
	if "%USERNAME"=="%CAROLYN" SET NUM_RECENT_TO_KEEP=500


:BACKUP_CERTAIN_FILES
    %COLOR_REMOVAL%
	if exist %MP3LIST% (echo ray|copy %MP3LIST% c:\recycled\latest-everything.m3u)
	:f     exist    "%MP3LISTBAK%" (echos                 >:u8   "%MP3LISTBAK")
	                                echos                 >:u8   "%MP3LISTBAK"     %+ REM Let's try just doing this always
	:f     exist "%RECENTLISTBAK%" (echos                 >:u8"%RECENTLISTBAK")
	if     exist    "%MP3LIST%"    (echo ray|*copy /q     "%MP3LIST"    "%MP3LISTBAK")
	:f     exist "%RECENTLIST%"    (echo ray|*copy /q  "%RECENTLIST" "%RECENTLISTBAK")
    if not exist    "%MP3LISTBAK%" (call alarm "MP3LISTBAK of %MP3LISTBAK% does not exist, and should!")



:CHANGE_BEHAVIOR_BASED_ON_COMMAND_LINE_PARAMETERS:
	if "%1" != "quick" .and. "%1" == "PUBLISH" (goto :PUBLISH) %+ rem We kinda stopped the publish part when RIAA started campaigning against Napster



:CREATE_THESE_AND_ALL_IN_EACH_DIR
    	%MP3OFFICIAL%\
        call important "Creating %MP3OFFICIAL\LISTS\dir.txt to flush filenames into cache"
		dir /s >:u8%MP3OFFICIAL%\LISTS\dir.txt

		if "%1"=="quick" (goto :quick2_YES)
            call important "Creating directory & recursive playlists..(these.m3u & all.m3u)"
            %COLOR_RUN%
            pushd .
            %MP3OFFICIAL%\
                rem OLD: call create-these_m3u-playlists
                rem OLD: call create-all_m3u-playlists 
                rem NEW:
                generate_thesem3u_and_allm3u_playlists_in_folder.py c:\mp3\
            popd
		:quick2_YES
	%MP3OFFICIAL\







:ACTUALLY_RUN_THE_INDEXER_SUBSCRIPT:
    call important "Generating playlists by attribute...       (generate-filelists-by-attribute.pl/gap.bat)"
    call %BAT%\generate-audio-playlists.bat %*
    :: open results in text editor
        pushd
            %MP3OFFICIAL%\LISTS\
            :%EDITOR%   diff*.dat  :we explicitly open just the one we make, nowadays
            :%EDITOR% indexer.log  :2017 - debug info got too big for text editor
        popd





:POST_INDEX_TRIGGERS_TO_LET_REACTIVE_PROCESSES_KNOW_THIS_HAS_HAPPENED
	>"%MP3OFFICIAL\LISTS\TRIGGER-CASMP3.TRG"
	>"%MP3OFFICIAL\LISTS\TRIGGER-CL-4G-SD-CARD.TRG"
	>"%MP3OFFICIAL\LISTS\TRIGGER-CL-IPHONE2G.TRG"

:THINGS_WE_DO_NOT_DO_ANYMORE
	:SYNC_PLAYLISTS_TO_PORTABLE_DEVICES
		:::: We may get stuck here, so let's start it in a new window until we master it.
		:::: NO! THIS IS NOW OFFLOADED TO CAROLYN'S 4NT WINDOWS! AWESOME! call sync-mp3-playlists-to-carolyn's-mp3player.bat
		:::: 2014 update: We now have a nice sync.bat that we manually run when inserting memory cards into cardreaders and such
	:REMAP_PLAYLISTS_TO_CORRECT_DRIVE_LETTERS
		::::	NO LONGER DOING THIS, as I've decided all playlists should be c:\mp3\, and computers can create junctions at c:\mp3\ that point to wherever the music actually is
		::::	This has caused a half-crash on Hades due to Hell's networking problems:
		::::	call remap-playlists.bat
	:RELOAD_PLAYLISTS
		:::: ::::: Reload playlists for secondary and other music servers, so new playlists are instantly reflcted:
		:::: 	call reload-playlists.bat
		:::: echo TODO: Note that reloading the playlist like that does NOT instantly reflect changes anymore, due to changes in how they are reloaded!
		:::: echo       Nowadays we just reload now-playing-playlist.m3u which does NOT get updated!
		:::: echo       What we could do is look in now-playing.dat and simply copy that file over now-playing-playlist.m3u
		:::: echo             - but that will not work with "these.m3u" and "all.m3u" style lists, just meta-attribute lists!



:UPDATE_THE_MCHK_2ND_LEVEL_INDEX_WITH_THIS_NEW_INDEX
	call mchk.bat index



:CREATE_AND_PUBLISH_OUR_ANCILLARY_LISTS_EXCEPT_WE_DO_NOT_PUBLISH_ANYMORE
	gosub CREATE_RECENTLIST
    rem WE STOPPED BOTHERING WITH THIS... We save diffs in a historical folder in a post-MPAA world where sharing what new music you got is legally inadvisable for legally ridiculous reasons: 
    rem gosub PUBLISH_LISTS         

:CLEAN_UP_AND_REPORT

        rem WE STOPPED BOTHERING WITH THIS:       call important "Removing extraneous playlists...          (redundant and 0-byte lists)"
        rem WE STOPPED BOTHERING WITH THIS:       %COLOR_REMOVAL%
        rem WE STOPPED BOTHERING WITH THIS:::		echo set A=%%@FILESIZE[these.m3u]           >:u8"%TEMP\temp-kill.bat"
        rem WE STOPPED BOTHERING WITH THIS:::		echo set B=%%@FILESIZE[all.m3u]            >>:u8"%TEMP\temp-kill.bat"
        rem WE STOPPED BOTHERING WITH THIS:::		echo if "%%A"=="0"      *del /q these.m3u  >>:u8"%TEMP\temp-kill.bat"
        rem WE STOPPED BOTHERING WITH THIS:::		echo if "%%B"=="0"      *del /q all.m3u    >>:u8"%TEMP\temp-kill.bat"
        rem WE STOPPED BOTHERING WITH THIS:::		echo if "%%A"=="%%B"    *del /q all.m3u    >>:u8"%TEMP\temp-kill.bat"
        rem WE STOPPED BOTHERING WITH THIS:::		echo if exist delme.m3u *del /q delme.m3u  >>:u8"%TEMP\temp-kill.bat"
        rem WE STOPPED BOTHERING WITH THIS:::		start exitafter.bat (sweep call "%TEMP\temp-kill.bat") >& nul


	:report how long it took to index
		%COLOR_IMPORTANT% %+ echos Time to index MP3s: `` %+ timer|cut -c33-
		echo.

	:report how many lines/bytes our root playlists are:
        %COLOR_NORMAL%
		call wcheader -lc
		wc  -lc *.m3u | winsort /R
		echo.

	:report total size of mp3 collection:
        %COLOR_WARNING%
		echo Total Size Of MP3 Collection (MB):
		du -sm

	:report that we're done!
        call success "All playlists successfully created"










goto :END

::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:CREATE_RECENTLIST
	:ET TMP1=c:\recycled\latest-diff.txt
	:ET TMP2=%@UNIQUE[c:\recycled]
	:ET TMP3=%@UNIQUE[c:\recycled]

	:OLD:
                if not exist "%MP3LISTBAK%" (%COLOR_ALARM %+ echo MP3LISTBAK of %MP3LISTBAK% does not exist, and should! Safe to continue, but no real diff this time! %+ beep %+ pause)
				:diff -ni "%MP3LISTBAK%" "%MP3OFFICIAL%\LISTS\everything.m3u" >:u8%TMP1
            	:tail +1 %TMP1 | grep -vq "^< " | grep -iq "%MP3LISTDRIVE:" | grep -vq "%RECENTLISTFILE" | insert-before-each-line "Added/Renamed: %_date %_time: " >>:u8%RECENTLISTBAK
	:201503 ADDITION:
        		:NOTE: for diff, -i makes it ignore case. That way, if we just capitalize something, it won't show up as new
                set DIFF_OPTIONS=-i
                set DIFF=diff %DIFF_OPTIONS%
                set DIFF_NAME=diff-%_DATETIME.dat
                set DIFF_DIR=%MP3OFFICIAL%\LISTS\history
                set DIFF_FULL=%DIFF_DIR%\%DIFF_NAME%
                if not exist %DIFF_DIR% mkdir /s "%DIFF_DIR%"
				%DIFF% "%MP3LISTBAK%" %MP3\LISTS\everything.m3u >:u8"%DIFF_FULL%"
                if %@FILESIZE["%DIFF_FULL%"] eq 0 (*del /q "%DIFF_FULL%" >nul)
                gosub

if exist %TEMP\changer-diff-report.txt (%EDITOR %TEMP\changer-diff-report.txt)


	::::: Let's see what's gone into the changer/not into it
		rem %COLOR_IMPORTANT% %+ echo Changer changes: >:u8%TEMP\changer-diff-report.txt %+ %COLOR_NORMAL%
		%DIFF% %MP3OFFICIAL\LISTS\changer.m3u c:\recycled\changer.m3u >>:u8%TEMP\changer-diff-report.txt
        gosub EditIfExistsAndNonZero %TEMP\changer-diff-report.txt

	::::: Let's see what's gone into the party/not into it
		rem %COLOR_IMPORTANT% %+ echo Party changes: >:u8%TEMP\party-diff-report.txt %+ %COLOR_NORMAL%
		%DIFF% %MP3OFFICIAL\LISTS\party.m3u c:\recycled\party.m3u >>:u8%TEMP\party-diff-report.txt
		gosub EditIfExistsAndNonZero %TEMP\party-diff-report.txt

	::::: Let's see what's gone into the best/not into it
		rem %COLOR_IMPORTANT% %+ echo Best changes: >:u8%TEMP\best-diff-report.txt %+ %COLOR_NORMAL%
		%DIFF% %MP3OFFICIAL\LISTS\best.m3u c:\recycled\best.m3u >>:u8%TEMP\best-diff-report.txt
		gosub EditIfExistsAndNonZero %TEMP\best-diff-report.txt

	::::: Might be good to edit the file to remove extraneous entries, but we decided to stop doing this:
		rem tail -%NUM_RECENT_TO_KEEP "%RECENTLISTBAK"    >:u8"%RECENTLIST"
		rem %EDITOR% %RECENTLIST
return
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

        :EditIfExistsAndNonZero [filename]
            set file=%@UNQUOTE[%filename%]
            if  not exist "%file%"        (goto :prereturn5)

            %COLOR_DEBUG% %+ echo if %@FILESIZE["%file%"] lt 1 (goto :prereturn5) %+ %COLOR_NORMAL%
                                  if %@FILESIZE["%file%"] lt 1 (goto :prereturn5)

            %EDITOR%      "%file%"
            :prereturn5
        return

::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:PUBLISH
:PUBLISH_LISTS
    call checkusername
	:DoIt
		set FILE=%MP3OFFICIAL\mp3-%USERNAME.htm
		call important_less "Generating published MP3 list...          (%FILE)"
			type    c:\bat\html-uptohead.dat               >:u8%FILE
			html-title.pl %USERNAME's digital audio list  >>:u8%FILE
			type c:\bat\html-headclosebodyopen.dat        >>:u8%FILE
			type c:\bat\html-h1opencenter.dat             >>:u8%FILE
			echo %USERNAME's Digital Audio List           >>:u8%FILE
			type c:\bat\html-h1close.dat                  >>:u8%FILE
			type c:\bat\html-h2opencenter.dat             >>:u8%FILE
			echo You are visitor number                   >>:u8%FILE
			type c:\bat\html-counter.dat                  >>:u8%FILE
			type c:\bat\html-h2close.dat                  >>:u8%FILE
			type c:\bat\html-pre.dat                      >>:u8%FILE
			type %MP3LIST%                                >>:u8%FILE
			type c:\bat\html-preclose.dat                 >>:u8%FILE
			type c:\bat\html-bodyhtmlclose.dat            >>:u8%FILE
		:::: Okay, we've published the full list.

		call important_less "Generating published NEW audio list...    (%RECENTLISTPUB)"
			copy /q c:\bat\html-uptohead.dat                                                         %RECENTLISTPUB
			html-title.pl %USERNAME's last %NUM_RECENT_TO_KEEP new/renamed digital audio files  >>:u8%RECENTLISTPUB
			type c:\bat\html-headclosebodyopen.dat                                              >>:u8%RECENTLISTPUB
			type c:\bat\html-h1opencenter.dat                                                   >>:u8%RECENTLISTPUB
			echo %USERNAME's last %NUM_RECENT_TO_KEEP new/renamed digital audio files           >>:u8%RECENTLISTPUB
			type c:\bat\html-h1close.dat                                                        >>:u8%RECENTLISTPUB
			type c:\bat\html-h2opencenter.dat                                                   >>:u8%RECENTLISTPUB
			echo (Most recent files are at the bottom!!)                                        >>:u8%RECENTLISTPUB
			type c:\bat\html-h2close.dat                                                        >>:u8%RECENTLISTPUB
			type c:\bat\html-h3opencenter.dat                                                   >>:u8%RECENTLISTPUB
			echo You are visitor number                                                         >>:u8%RECENTLISTPUB
			type c:\bat\html-counter.dat                                                        >>:u8%RECENTLISTPUB
			type c:\bat\html-h3close.dat                                                        >>:u8%RECENTLISTPUB
			type c:\bat\html-pre.dat                                                            >>:u8%RECENTLISTPUB
			type %RECENTLIST                                                                    >>:u8%RECENTLISTPUB
			type c:\bat\html-preclose.dat                                                       >>:u8%RECENTLISTPUB
			type c:\bat\html-bodyhtmlclose.dat                                                  >>:u8%RECENTLISTPUB

	if "%1"=="PUBLISH" goto :DONE
return
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::




:END
	rem We stopped doing this here because we do it as part of bedtime.bat since we manually update playlists more often than we run the indexeer:
		rem call upload-playlists

	rem Force a glance at any errors generated. 
    rem In the past, the file exceeded the maximum file size for older versions of EditPlus, so we would check for presence of an alternate text editor (SlickEdit):
        set BIGEDITOR="%Program Files%\SlickEdit Pro 21.0.0\win\vs.exe"
        if     exist %BIGEDITOR% ( %BIGEDITOR% "%MP3OFFICIAL%\LISTS\INDEXER.LOG" )
        if not exist %BIGEDITOR% (    %EDITOR% "%MP3OFFICIAL%\LISTS\INDEXER.LOG" )

	rem Stop the timer we started earlier:
		timer /3 off


:DONE

    rem Exit the window/pane:
        call helper-end




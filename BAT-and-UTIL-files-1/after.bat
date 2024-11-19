@echo off
 on break cancel

::::: SETUP:
        :ASSUME 'gr' is an alias for grep
        title after %*
        call checkeditor
        call fixclip
        call fixtmp
        unset /q LOGFILE_BASENAME_TO_USE
        unset /q YearInFileName
        call validate-environment-variable PUBCL
        if not isdir %PUBCL (echo Environment variable %%PUBCL must be set to use this. %+ goto :END)

::::: PARAMETER BRANCHING:
    if "%1"=="aftershock"	    goto :earthquake
    if "%1"=="application"	    goto :jobapplication
    if "%1"=="book"			   (set  LOGFILE_BASENAME_TO_USE=book)
    if "%1"=="camera"		   (gosub :AfterCamera)
    if "%1"=="censor"		   (call after-censor %+ goto :END)
    if "%1"=="censored"		   (call after-censor %+ goto :END)
    if "%1"=="camping"		   (set  LOGFILE_BASENAME_TO_USE=NULL	%+		%EDITOR %WWW\events\camping\camping-trips.txt)
    if "%1"=="coincidence"	   (set  LOGFILE_BASENAME_TO_USE=movie	%+		gosub coincidence )
    if "%1"=="concert"		   (set  LOGFILE_BASENAME_TO_USE=NULL	%+		gosub concert)
    if "%1"=="dream"		   (set  LOGFILE_BASENAME_TO_USE=dream	%+		gosub dream)
    if "%1"=="disagreement"	   (goto :Disagreement)
    if "%1"=="divorce"		   (goto wedding)
    if "%1"=="earthquake"	    goto :earthquake
    if "%1"=="electro"	        goto :hairRemoval
    if "%1"=="electrolysis"	    goto :hairRemoval
    if "%1"=="electrolisis"	    goto :hairRemoval
    if "%1"=="laser"	        goto :hairRemoval
    if "%1"=="laserhairremoval"	goto :hairRemoval
    if "%1"=="funeral"	        goto :funeral
    if "%1"=="game"			   (set  LOGFILE_BASENAME_TO_USE=game)
    if "%1"=="gun"			   (goto :Guns)
    if "%1"=="guns"			   (goto :Guns)
    if "%1"=="hair"			   (goto :hair)
    if "%1"=="hitomi"     	   (goto :hitomi)
    if "%1"=="inject"	        goto :injection
    if "%1"=="injection"        goto :injection

    if "%1"=="internetoutage"  (goto :InternetOutage)
    if "%1"=="inventory"       (goto :Inventory)
    if "%1"=="jobapplication"   goto jobapplication
    if "%1"=="meter"		   (goto meter)
    if "%1"=="month"		   (set  LOGFILE_BASENAME_TO_USE=year  %+       goto month            )
    if "%1"=="mouse"		   (set  LOGFILE_BASENAME_TO_USE=mouse %+		set  YearInFileName=no)
    if "%1"=="movie"		   (set  LOGFILE_BASENAME_TO_USE=movie %+		goto movie            )
    if "%1"=="mov"  		   (set  LOGFILE_BASENAME_TO_USE=movie %+		goto mov              )
    if "%1"=="m"  		       (set  LOGFILE_BASENAME_TO_USE=movie %+		goto m                )
    if "%1"=="nap"  		   (call awake)
    if "%1"=="netflix"		   (goto :netflix)
    if "%1"=="year"		        goto year
    if "%1"=="pictures"		   (gosub :AfterCamera)
    if "%1"=="peapod"		   (goto :Peapod)
    if "%1"=="poweroutage"	   (goto :PowerOutage)
    if "%1"=="powerfailure"	   (goto :PowerOutage)
    if "%1"=="quake"		   (goto :quake)
    if "%1"=="quakelive"	   (goto :quakelive)
    if "%1"=="quote"		   (goto :quote)
    if "%1"=="rocksmith"       (goto :RockSmith)
    if "%1"=="screw"		   (call qd>:u8clip:          %+   %EDITOR %PUBCL\journal\companies-that-screwed-me.txt	%+ goto :END )
    if "%1"=="sex"			   (goto :sexyTimes)
    if "%1"=="show"			   (set  LOGFILE_BASENAME_TO_USE=show)
    if "%1"=="tagging"		   (goto :tagging)
    if "%1"=="trans"	        goto :hairRemoval
    if "%1"=="wedding"		   (goto :wedding)
    if "%1"=="weigh"		   (goto :weight)
    if "%1"=="weight"		   (goto :weight)
    if "%1"=="yardsale"		   (goto :yardsale)
    :DEBUG: echo %%LOGFILE_BASENAME_TO_USE is %LOGFILE_BASENAME_TO_USE
    if "%LOGFILE_BASENAME_TO_USE"==""     (echo. %+ echo %ANSI_COLOR_ALARM%*** Error:  "after" type unknown: %+ %COLOR_WARNING% %+ echo *** Must be one of the following: book, camera/pictures, camping, censor[ed], coincidence, concert, disagreement, dream, earthquake/aftershock, funeral, game, gun[s], hair, inject, internetoutage, [job]application, laser, month, mouse, movie, mov, nap, netflix, peapod, poweroutage, quake[live], quote, RockSmith, screw (bad companies), show, tagging, trans, wedding/divorce, weigh[t], yardsale, year %ANSI_RESET% %+ goto :END )
    if "%LOGFILE_BASENAME_TO_USE"=="NULL" (goto :LOGFILE_BASENAME_TO_USEisnull)


                           set tmpfile=%PUBCL%\journal\%LOGFILE_BASENAME_TO_USE%-%_YEAR.txt
if "%YearInFileName"=="no" set tmpfile=%PUBCL%\journal\%LOGFILE_BASENAME_TO_USE%.txt
    :DEBUG: echo tmpfile is %tmpfile
	if "%MINIMIZE_AFTER" eq ""  %EDITOR%   %tmpfile%
	if "%MINIMIZE_AFTER" eq "0" %EDITOR%   %tmpfile%
	if "%MINIMIZE_AFTER" eq "1" %EDITORBG% %tmpfile%
:LOGFILE_BASENAME_TO_USEisnull
goto :END


::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:year
	%EDITOR %BAT\after.bat

	:::::::::: 2011 :::::::::::::::: -- Set the date for something in April. We will need time for pictures to catch up.

	echo.
	Echo * Make image clouds for that year? (meh)

	echo.
	Echo * Do the LAST.fm music graphs?  How about some album charts like albums most listened to this year? Include in AFTER MONTH blogpost.
	echo                2011,(2012?),2013,2014, done

	echo.
	Echo * Do AFTER MONTH monthly summaries? Make a 'year in text and music' blogpost using this and the last.fm music graphs.
	Echo %=^------ USE THE TEMPLATE!
	:2011 done
	echo * Tweet car expenditure statistics!
	echo                   DONE: 2012, 2013

	echo.
	Echo * Do final yard sale stats? Those were probably already done at the end of yard sale season... Include in monthly summary.
	:2009 - has been posted in the correct tag
	:2010 - NOT POSTED YET!!!!!!!!!!!!! INCLUDE IN 2012 WRITEUP!!!!!!!!!!!
	:2011 - done
	:2012 - see 2010 note above before doing this! NOT YET DONE

	echo.
	Echo * Do PICTURES OF THE YEAR post?
	:2011 - done to a point but needs completion

	echo.
	Echo * Do GAMES OF THE YEAR post? Include BrettSpielWelt stats. ?
	:2011 - done

	echo.
	Echo * Do BOOKS OF THE YEAR post?
	:2011 - NOT DONE - ONLY 2 BOOKS TO MENTION - TABLE FOR NEXT YEAR

	echo.
	Echo * Do movies watched that year?
	:2011 - done

	echo.
	Echo * Do TV shows watched that year?
	:2011 NOT DONE

	echo.
	Echo * Do My Year In Stats tweet montage? Also: Tweet cloud.
	:2011 on flickr



	Echo.
	echo ***** DON'T FORGET TO USE "YEAR IN REVIEW" TAG IN ADDITION TO "MEDIA CONSUMPTION LISTS" (when applicable) ****
goto :END
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:PowerOutage
	echo Paste your clipboard into this next file... It will contain the date...
	call YYYYMMDD
	echo %YYYYMMDD: >clip:
	call qd.bat
	pause
	%EDITOR %PUBCL\house\power-outages.txt
goto :END
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:InternetOutage
	echo Paste your clipboard into this next file... It will contain the date...
	call qd.bat
	pause
    call validate-environment-variables DROPBOX ISP
    call now
	%EDITOR %dropbox%\notes\%ISP%-NOTES.txt
    ipconfig /release
    ipconfig /renew
goto :END
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:Inventory
    https://docs.google.com/document/d/1pyMKxpwMyrjwvCcFeYeGhy6NfHFeXjiZu39YmcG7oh4/edit
goto :END
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:AfterCamera
    call move-dropbox-newpics-to-newpics
goto :END
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::




:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:hairRemoval
    call diary
    call notes
    call checkeditor
    %EDITOR% laser-notes.txt
goto :END
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:Peapod
	call YYYYMMDD
	echos %YYYYMMDD: >clip:
	echo : >>clip:
	pause
	%EDITOR %PUBCL\house\peapod.txt
goto :END
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:Disagreement
	echo Paste your clipboard into this next file... It will contain the date...
	call YYYYMMDD
	echo %YYYYMMDD: >clip:
	pause
	%EDITOR %PUBCL\Carolyn\disagreements.txt
goto :END
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:wedding
	echo Paste your clipboard into this next file... It will contain the date...
	call YYYYMMDD
	echo %YYYYMMDD: >clip:
	pause
	%EDITOR %PUBCL\journal\weddings.txt
goto :END
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:jobapplication
	%EDITOR% %PUBCL\jobs\cover-letter.txt
	echo Paste your clipboard into this next file... It will contain the date...
	call YYYYMMDD
	echos %YYYYMMDD: >clip:
	:pause
	if exist  %PUB\jobs\applications.txt             %EDITOR  %PUB\jobs\applications.txt
	if exist "%PUB\work\job search\applications.txt" %EDITOR "%PUB\work\job search\applications.txt"
goto :END
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:quote
	if not isdir %WWW\quotes            (echo FATAL ERROR: quotes folder of %WWW\quotes            does not exist! %+ goto :END)
	if not exist %WWW\quotes\quotes.txt (echo FATAL ERROR: quotes   file of %WWW\quotes\quotes.txt does not exist! %+ goto :END)
	%EDITOR %WWW\quotes\quotes.txt
	echo After adding your quote, hit any key to update the RSS feed and upload to web...
	pause
	pause
	:Normal quotes feed:
	c:\bat\quotes-RSS-feed-generator.pl   <%WWW\quotes\quotes.txt >%WWW\quotes\quotes-rss.xml

	:::NO LONGER DOING THIS:
	::Quotes feed for Gmail signatures, where the title is all that counts, and where my other info must be inserted:
	:c:\bat\quotes-RSS-feed-generator.pl 1 <%WWW\quotes\quotes.txt >%WWW\quotes\quotes-rss-gmail-signature-test1.xml
	echo asdf |:u8 call auto-ftp
goto :END
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:movie
		set AFTERMOVIE=1
		call killifrunning editPlus editplus
		set categories=People,Carolyn,Claire,Media,Video,Movies,Reviews
		echo.
		echo Enter movie name:
            if "%MOVIE"=="" set MOVIE=.
		     echos %MOVIE% (%YEAR%) >clip:
            :Try turning this off/on:
                :%EDITORBG% %PUBCL\journal\%LOGFILE_BASENAME_TO_USE-%_YEAR.txt  %+call sleep 1 %+ window restore
		eset MOVIE
			call     imdb.bat  %MOVIE%
			call  netflix.bat  %MOVIE%
			echos %MOVIE%>clip:
			call validate-environment-variable MACHINENAME_SCRIPT_AND_DROPBOX_AUTHORITY_CDRIVE
        :2008:
        :%EDITOR% %MACHINENAME_SCRIPT_AND_DROPBOX_AUTHORITY_CDRIVE%:\perl\site\lib\Claire\HTML.pm
        :201511: trying to stop multiple editplus window bug:
         %EDITOR% %PUBCL\journal\%LOGFILE_BASENAME_TO_USE-%_YEAR.txt %MACHINENAME_SCRIPT_AND_DROPBOX_AUTHORITY_CDRIVE%:\perl\site\lib\Claire\HTML.pm

		if "%NETFLIX_RATING%"          == "" set NETFLIX_RATING=.
		if "%IMDB_RATING%"             == "" set IMDB_RATING=.
		if "%IMDB_LINK%"               == "" set IMDB_LINK=.
		if "%CLAIRES_NETFLIX_RATING%"  == "" set CLAIRES_NETFLIX_RATING=.
		if "%CLAIRES_IMDB_RATING%"     == "" set CLAIRES_IMDB_RATING=.
		if "%CAROLYNS_NETFLIX_RATING%" == "" set CAROLYNS_NETFLIX_RATING=.
		if "%CAROLYNS_IMDB_RATING%"    == "" set CAROLYNS_IMDB_RATING=.
		if "%YEAR%"                    == "" set YEAR=%_YEAR
		window restore
		eset YEAR
			echos %MOVIE% (%YEAR%) - >clip:
			%EDITOR% %PUBCL\journal\%LOGFILE_BASENAME_TO_USE-%_YEAR.txt
			pause
        :NetflixRating
		eset NETFLIX_RATING             %+ if "%NETFLIX_RATING%"          eq "." goto :NetflixRating
        :IMBRating
		eset IMDB_RATING                %+ if "%IMDB_RATING%"             eq "." goto :IMDBRating
        :imdb_link
		eset IMDB_LINK                  %+ if "%IMDB_LINK%"               eq "." goto :imdb_link
        :claires_netflix_rating
		eset CLAIRES_NETFLIX_RATING     %+ if "%CLAIRES_NETFLIX_RATING%"  eq "." goto :claires_netflix_rating
        :claires_imdb_rating
		eset CLAIRES_IMDB_RATING        %+ if "%CLAIRES_IMDB_RATING%"     eq "." goto :claires_imdb_rating
        :carolyns_netflix_rating
		eset CAROLYNS_NETFLIX_RATING    %+ if "%CAROLYNS_NETFLIX_RATING%" eq "." goto :carolyns_netflix_rating
        :carolyns_imdb_rating
		eset CAROLYNS_IMDB_RATING       %+ if "%CAROLYNS_IMDB_RATING%"    eq "." goto :carolyns_imdb_rating
	:ause
		:: NAH http://www.rhymezone.com/
		%EDITOR% %BAT\blog-movie-body-template.txt
		if "%_MONITORS" eq "1" (call minimize "*Google Chrome*")       %+  echos %MOVIE% (%YEAR%) >clip:
		%EDITOR %PUBCL\journal\%LOGFILE_BASENAME_TO_USE-%_YEAR.txt                      %+  echos %MOVIE% (%YEAR%) >clip:
	:ause
		set TITLE=VIDEO: MOVIES: REVIEW: %MOVIE% (%YEAR%)
        %COLOR_DEBUG% %+ echo * title will be "%TITLE%" %+ %COLOR_NORMAL%
		echo                             %MOVIE% (%YEAR%)>clip:
		echo ** Eventually we should program %BAT\blog-movie-body-template.txt to automatically import... %+ echos %MOVIE% (%YEAR%) >clip:
		%EDITOR% %BAT\blog-movie-body-template.txt %MACHINENAME_SCRIPT_AND_DROPBOX_AUTHORITY_CDRIVE%:\perl\site\lib\clio\HTML.pm
		set DRAFT=1
		echo NOTE: This is being put into drafts, and not published right away. %+ echos %MOVIE% (%YEAR%) >clip:
		call mtblog %BAT\blog-movie-body-template.txt %*
	goto :gotoblog%USERNAME
		:gotoblogclaire
			SET TMPNAME=%NETNAME_DEAD%
		goto :gotoblogdone_BEGIN
		:gotoblogcarolyn
			SET TMPNAME=carolyncasl
		goto :gotoblogdone_BEGIN
	:gotoblogdone_BEGIN
			http://%TMPNAME%.wordpress.com/wp-admin/edit.php?post_status=future
			http://%TMPNAME%.wordpress.com/wp-admin/edit.php?post_status=draft
			if exist c:\delme-last-post-id.dat type c:\delme-last-post-id.dat>clip:
			echo * Post ID copied to clipboard!
			call sleep 1
			REM *** We could do some crazier stuff like generating the entire HTML line...
			%EDITOR %MACHINENAME_SCRIPT_AND_DROPBOX_AUTHORITY_CDRIVE%:\perl\site\lib\clio\HTML.pm
	:gotoblogdone_END


	:Clean_Up_After_Movie
		set AFTERMOVIE=0
		set LASTMOVIE=%TITLE%
		unset /q title
		unset /q categories
		::NAH, this will copy the header crap: type %BAT\mtsend-last-blog-sent.bak >clip:
		:why was I saying this again? echo * Copy the review to your clipboard - please paste into full log now...
        window restore

goto :END
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:mov
	echo.
	echo *SHORT* movie review mode. Relies on IFTTT (which sucks)
	echo.
	echo Enter movie name:
		if "%MOVIE"=="" set MOVIE=.
		eset  MOVIE
		echo %MOVIE >clip:
	%EDITOR %PUBCL\journal\%LOGFILE_BASENAME_TO_USE-%_YEAR.txt %BAT\blog-movie-body-template.txt c:\perl\site\lib\clio\HTML.pm
		http://www.facebook.com/%NETNAME%
		call sleep 1
		http://%NETNAME_DEAD%.wordpress.com
		call sleep 1
		https://ifttt.com/myrecipes/personal/632571
		call sleep 1
		https://ifttt.com/myrecipes/personal/632559
		call sleep 1
	call netflix.bat %MOVIE
	call sleep 1
	call    imdb.bat %MOVIE
goto :END
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:m
	echo.
	echo *2019 MINIMALIST* movie review mode. Text file only.
	echo.
	echo Enter movie name:
		if "%MOVIE"=="" set MOVIE=.
		eset  MOVIE
		echo %MOVIE >clip:
	%EDITOR%  %PUBCL\journal\%LOGFILE_BASENAME_TO_USE-%_YEAR.txt
    echo.
    echo.
    echo.
    echo.
    echo.
    echo gonna IMDB it now...ctrl-break to abort.....
    pause
    pause
    pause
	call    imdb.bat %MOVIE
goto :END
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:coincidence
	%EDITOR %PUBCL\journal\%LOGFILE_BASENAME_TO_USE-%_YEAR.txt
return
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:earthquake
	http://earthquake.usgs.gov/earthquakes/recenteqsus/Maps/US2/37.39.-79.-77_eqs.php
	%EDITOR %PUBCL\journal\earthquake.txt
return
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:quake
	echo.
	rem echo Restarting Setpoint... %+ start setpoint
	rem echo Killing IHateThisKey... %+ kill /f IHateThisKey*
	echo 
    call less_important "Killing WinKill..."        
    @kill /f WinKill
    call less_important "Restarting AutoHotKey..."
    call AutoHotKey-autoexec
    call unimportant "(we used to restart torrents automatically here)"
	rem echo Restarting torrents...
	rem call utorrent-control resumealltorrents
goto :END
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::



::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:concert
		echo Add concert to diary too...
		pause
	call as claire diary
		pause
	http://www.songkick.com/
	%EDITOR %WWWCL\media\concerts.htm
		echo Fix concertnext band (after pressing a key)...
		pause>nul
	call al.bat
	set categories=People,Carolyn,Claire,Media,Audio,Music,Journal,Concerts,Reviews
		echo.
		echo Enter band name:
	if "%BAND"=="" set BAND=.
	eset BAND
	set TITLE=JOURNAL: CONCERT: %BAND
		echo %BAND >:u8clip:
		echo ** Eventually we should program %BAT\blog-concert-body-template.txt to automatically import ????
	%EDITOR     %BAT\blog-concert-body-template.txt
	call mtblog %BAT\blog-concert-body-template.txt
		unset /q title
		unset /q categories
	::NAH, this will copy the header crap: type %BAT\mtsend-last-blog-sent.bak >clip:
	echo Copy the review to your clipboard - paste into concert.htm if you want...
	:seems to be done in mtblog.bat: http://4jcl.wordpress.com
return
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:weight
	call yyyymmddhhmm
    call validate-environment-variables USERNAME KNOWN_NAME EDITOR PUBCL YYYYMMDDHHMM

	set OURFILE=%PUBCL\medical\weight-tracking.txt
    call validate-environment-variable OURFILE
        set WEIGHTS=%ourfile%
        set WEIGHTS_FILE=%ourfile%

    unset /q WEIGHT
    if "%2"       ne "" (set   WEIGHT=%2        )      %+ REM %1 is the username, %2 is the weight
    if "%WEIGHT%" ne "" (goto :AlreadyHaveWeight)

        querybox /d /l3 "Just got weighed!" Enter your new weight:  %%WEIGHT

    :AlreadyHaveWeight
    set WEIGHT_NAME=%KNOWN_NAME%
    if "%USERNAME%" eq "claire" (set WEIGHT_NAME=claire)
    if  %WEIGHT%    lt  150     (set WEIGHT_NAME=carolyn)

    echo %WEIGHT_NAME,%YYYYMMDDHHMM,%WEIGHT >>:u8%OURFILE

    :: nah %EDITOR %OURFILE
    gr %WEIGHT_NAME% %OURFILE%

    set LAST_FILE_EDITED=%OURFILE%     %+  unset /q OURFILE
    set LAST_WEIGHT_MEASURED=%WEIGHT%  %+  unset /q WEIGHT
	                                       unset /q YYYYMMDDHHMM
goto :END
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:meter
	call checkeditor
	:::::call checkusername
	call yyyymmdd
	querybox /d "Just looked at power meter!" Enter your new reading:  %%METER
	set OURFILE=%PUBCL\house\power-meter.txt
	echo %YYYYMMDD,%METER >>:u8%OURFILE
	%EDITOR %OURFILE
	unset /q YYYYMMDD
	unset /q METER
	unset /q OURFILE
goto :END
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:hair
	call checkeditor
	call checkusername
	call yyyymmdd
	querybox  "Just measured hair!" Enter your new hair length (in inches, decimals acceptable):  %%WEIGHT
	set OURFILE=%PUBCL\medical\hair-tracking.txt
	echo %USERNAME,%YYYYMMDD,%WEIGHT >>:u8%OURFILE
	%EDITOR %OURFILE
	unset /q YYYYMMDD
	unset /q WEIGHT
	unset /q OURFILE
goto :END
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:dream
	set categories=People,Journal,Dreams,Claire
	if "%USERNAME"=="carolyn" set categories=People,Journal,Dreams,Carolyn
	echo Paste your clipboard into this next file... It will contain the date...
	call YYYYMMDD
	echo %YYYYMMDD: >clip:
	pause
	set FILE=%PUBCL\journal\dreams\dreams-%_YEAR.txt
	if "%USERNAME"=="carolyn" set FILE=%PUBCAS\journal\dreams\dreams-%_YEAR.txt
	%EDITOR %FILE
	echo Once done typing up your dream, copy it to clipboard to be blogged...
	pause
	set DRAFT=1
	set TITLE=JOURNAL: DREAM: %YYYYMMDD:
	call mtblog %BAT\blog-dream-body-template.txt %*
	if "%username"=="carolyn" goto :CarolynDreamAfter
	https://%NETNAME_DEAD%.wordpress.com/wp-admin/edit.php?post_status=future&post_type=post
	https://%NETNAME_DEAD%.wordpress.com/wp-admin/edit.php?post_status=draft&post_type=post
	goto :CarolynDreamAfterAfter
	:CarolynDreamAfter
	https://carolyncasl.wordpress.com/wp-admin/edit.php?post_status=future&post_type=post
	https://carolyncasl.wordpress.com/wp-admin/edit.php?post_status=draft&post_type=post
	:CarolynDreamAfterAfter
	unset /q categories
	unset /q FILE
	unset /q DRAFT
goto :END
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:month
    set tmpyear=%_YEAR
    if "%2" ne "" (set tmpyear=%2)
	if "%_DAY"=="1" goto :DoLastMonth

	:DoThisMonth
		if "%1"=="noclip" goto :NoClipAfterMonth
			REM        echos ******` `>clip:
			REM display-this-month.pl>>clip:
			REM        echo  ******: >>clip:
			echo %_MONTH/%_DAY:>clip:
			call advice "%_MONTH/%_DAY: copied to clipboard"
		:NoClipAfterMonth
	    set FILE=%PUB\journal\year-%tmpyear%.txt
		%EDITOR %FILE
	goto :END_month

	:DoLastMonth
		echos ******` `>clip:
		display-last-month.pl>>clip:
		echo  ******: >>clip:
		set FILE=%PUB\journal\year-%tmpyear%.txt
		%EDITOR %FILE
:END_month
goto :END
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::



::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:yardsale
	:et categories=People,Carolyn,Claire,Yard Sales,Hobbies & Activities
	set categories=People,Carolyn,Claire,Yard Sales,Hobbies &amp; Activities
	echo Paste your clipboard into this next file... It will contain the date...
	call YYYYMMDDclip
	pause
	%EDITOR "%PUBCL\journal\Yard Sales\yardsale-%_YEAR.html"
	echo Once done typing up your yardsale, copy it to clipboard to be blogged...
	pause
	set TITLE=JOURNAL: YARD SALES:
	set DRAFT=1
	call mtblog %BAT\blog-yardsale-template.txt %*
	https://picasaweb.google.com/118170621314144271410/Cloudsave?authkey=Gv1sRgCJXE6pPOhfmS8AE
	https://%NETNAME_DEAD%.wordpress.com/wp-admin/edit.php?post_status=draft
	https://%NETNAME_DEAD%.wordpress.com/wp-admin/edit.php?post_status=future&post_type=post
	:This seems to be resolved... echo Still trying to get Hobbies & Activities category to work successfully -- you may have to manually add it.
	unset /q categories
	unset /q draft
goto :END
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::




::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:guns
	echo Copying date to clipboard...
	call YYYYMMDD
	echo %YYYYMMDD: >clip:
	call qd.bat
	pause
	%EDITOR %PUBCL\journal\guns.txt
goto :END
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:netflix
	call yyyymmddclip
	http://movies.netflix.com/Queue?lnkctr=mhbque
	%EDITOR %PUBCL\journal\netflix.txt
goto :END
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:quakelive
	echo.
	echo.
	echo.
	echo.
	:echo Restarting Setpoint...
	:start setpoint
	:echo Killing IHateThisKey...
	:kill /f IHateThisKey*
	:echo Restarting torrents...
	:call utorrent-control resumealltorrents
	echo Restart the torrents...
	call fire
	pause
	echo Restarting Winamp visualizer...
	call    restart-winamp-visualizer
	pause
	echo.
	echo.
	echo.

	echo Fix the snd level for Winamp...
	:back when I had the why-is-it-set-to-20% problem: call snd
	launchkey "#w"
	pause
	echo.
	echo.
	echo.
	echo.
	echo All done!
	echo You may now get on with your life.
goto :END
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

::::::::::::::::::::::::::::::::::::::::::::::::
:funeral
	call now
	%EDITOR %PUBCL\journal\funerals.txt
	pause
	call diary
goto :END
::::::::::::::::::::::::::::::::::::::::::::::::

::::::::::::::::::::::::::::::::::::::::::::::::
:RockSmith
    call rocksmith after
goto :END
::::::::::::::::::::::::::::::::::::::::::::::::


::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:tagging
    if "%USERNAME%" eq "claire" goto :TaggingCommon
    if "%USERNAME%" eq "clio"   goto :TaggingCommon
    pause %+ %COLOR_ADVICE%  %+ echo * You didn't just make things up when tagging difficult things - You referred to standards-and-practices, right?
             %COLOR_ADVICE%  %+ echo * You didn't say "I" or "me" in the caption, did you?
    pause %+ %COLOR_ADVICE%  %+ echo * You didn't change tense in the middle of your caption, did you?
    pause %+ %COLOR_ADVICE%  %+ echo * There's a  place tag, right?  You forget to tag the place a lot.
    pause %+ %COLOR_ADVICE%  %+ echo * There's an event tag, right?  Holidays, birthday parties, etc?
    pause %+ %COLOR_ADVICE%  %+ echo * Have you spell-checked what you have written?  EditPlus has capabilities to install one.
    pause %+ %COLOR_ADVICE%  %+ echo * Did you have Claire review the tags so it's not a big fight the next day? :)
    pause

    :TaggingCommon
    call spellcheck attrib.lst
    cls   %+ %COLOR_WARNING% %+ echo * Now we will grep for some patterns that are invalid.
             %COLOR_WARNING% %+ echo   There should be no results for any of these greps.
             %COLOR_WARNING% %+ echo   Any output below represents something that shouldn't
             %COLOR_WARNING% %+ echo   exist, and thus action that needs to be taken:
             %COLOR_NORMAL%  %+ echo.

    :PatternsToGrepFor
        gr entertainment-cartoons    attrib.lst %+ REM * should be entertainment-TV-cartoons
        gr entertainment-TV-cartoon- attrib.lst %+ REM * cartoons should be plural
        gr entertainment-TV-movie-   attrib.lst %+ REM * movies   should be plural
goto :END
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


::::::::::::::::::::::::::::::::::::::::::::::::
:injection
    call injection-history.bat
goto :hairRemoval
::::::::::::::::::::::::::::::::::::::::::::::::


:::::::::::::::::::::::::::::::::::::::::::::::::::::::
:sexyTimes
    call validate-environment-variables PUBCL EDITOR
    %EDITOR% %PUBCL%\sex\sex.txt
goto :END
:::::::::::::::::::::::::::::::::::::::::::::::::::::::

::::::::::::::::::::::::::::::::::::::::::::::::
:hitomi
echo Hitomi!
call %BAT%\hitomi-assimilate.bat
echo Done!
goto :END
::::::::::::::::::::::::::::::::::::::::::::::::

::::::::::::::::::::::::::::::::::::::::::::::::
:TEMPLATE
goto :END
::::::::::::::::::::::::::::::::::::::::::::::::








:END

::::: CLEAN-UP:
	unset /q movie
	:nset /q LOGFILE_BASENAME_TO_USE
	unset /q tmpfile
	unset /q year
	unset /q DRAFT
	call fix-window-title

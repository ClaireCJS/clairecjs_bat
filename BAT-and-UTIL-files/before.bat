@echo off

:: OBSOLETE:
	:: set tmpeditor=%EDITOR
	:: if %tempeditor=="" set tmpeditor=start editpad
	:: if not isdir %PUBCL (echo Environment variable %%PUBCL must be set to use this. %+ goto :END)
:: NEW:
	call checkeditor


:: DETERMINE WHICH KIND OF "BEFORE" WE ARE RUNNING --- REMEMBER TO ADD NEW ONES TO THE USAGE... TRY TO KEEP THESE A-B-C:
	if "%1"=="anger"          goto :anger
	if "%1"=="application"    goto :jobapplication
    If "%1"=="appointment"    goto :appointment
	if "%1"=="bed"            goto :bedtime
	if "%1"=="bedtime"        goto :bedtime
	if "%1"=="breakfast"      goto :breakfast
	if "%1"=="camping"        goto :camping
	if "%1"=="dinner"         goto :dinner
	if "%1"=="fra"            goto :fra
	if "%1"=="guest"          goto :guests
	if "%1"=="guests"         goto :guests
	if "%1"=="hangout"        goto :hangout
	if "%1"=="inject"         goto :inject
	if "%1"=="injection"      goto :inject
	if "%1"=="injections"     goto :inject
	if "%1"=="jobapplication" goto :jobapplication
	if "%1"=="lunch"          goto :lunch
	if "%1"=="mastering"      goto :mastering
	if "%1"=="meal"           goto :meal
	if "%1"=="party"          goto :party
	if "%1"=="roadtrip"       goto :trip
	if "%1"=="sleep"          goto :bedtime
	if "%1"=="quake"          goto :quake
	if "%1"=="quake3"         goto :quake3
	if "%1"=="quakelive"      goto :quakelive
	if "%1"=="travel"         goto :trip
	if "%1"=="trip"           goto :trip
	if "%1"=="vacation"       goto :trip
	if "%1"=="yardsale"       goto :yardsale

:::::: USAGE IS UPDATED HERE:
	if "%tmplog"=="" (echo Error: "before" type unknown. Must be anger, bed, camping, dinner, guests, injection, [job]application, mastering, meal, party, quake[live], yardsale. %+ goto :END)

	:
	:                           set tmpfile=%PUBCL\journal\%tmplog-%_YEAR.txt
	:if "%YearInFileName"=="no" set tmpfile=%PUBCL\journal\%tmplog.txt

	%tmpeditor %tmpfile
goto :END


::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::




::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:anger
    http://www.wikihow.com/Overcome-Emotional-Sensitivity
    echo.
    echo.
    echo.
    echo.
    echo.
    echo.
    echo.
    echo.
    echo    The next time you experience an emotion, such as panic, anxiety, or anger, 
    echo         stop what you're doing and shift your focus to your sensory experiences. 
    echo         What are your five senses doing? Don’t judge your experiences, but note them.
    echo.
    echo.
    echo.
    window restore
goto :END
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:breakfast
:lunch
:dinner
:meal
	%EDITOR "%PUBCAS\food\dinners.txt"
goto :END
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::



::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:fra
    call dol
    cd ..
    call sizes|:u8hil gol|:u8gr gol
goto :END
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:bedtime
	call bedtime.bat %*
goto :END
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:jobapplication
	call after jobapplication
goto :END
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:mastering
	call checkeditor
	%EDITOR %BAT\notes\mastering-NOTES.txt
goto :END
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:quake
        call validate-environment-variables UTIL
        call validate-in-path               winkill kill advice less_important winamp-pause
        call advice         "FYI: There are also separate, OLD '%italics%after quake3%italics_off%' and '%italics%after quakelive%italics_off%' commands"
        call less_important "Killing %italics%AutoHotKey64%italics_off%..."                    %+ kill  /f   AutoHotKey64
        call less_important "Killing %italics%OVRServiceLauncher/Server/Redir%italics_off%..." %+ kill  /f   OVRServiceLauncher      %+ kill /f OVRServer_x64       %+ kill /f OVRRedir          
        call less_important "Pausing %italics%WinAmp%italics_off%..."                          %+ call       winamp-pause
        call less_important "Disabling %italics%Windows%italics_off% key..."                   %+ call       WinKill
        cls
        say "Go forth"
        say "and frag!"
        keystack "after" " " "quake"
goto :END
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:guests
    ::::: Erase clipboard:
        echo ..>clip:

	::::: Kill/erase things:
		kill /f opera*
		kill /f flock*
		kill /f yahoo*
		kill /f bid
		h/f

    ::::: Lighting:
        if "%SLEEPING%" eq "1" goto :NoLightsBeforeGuestsBecauseSleeping
            ::::: Turn on party lights:
                call pon
                echo.
                echo.
                echo.
            ::::: Turn on kitchen LEDs:
                call kon
            ::::: Turn on incoming hall light:
                call b1 on
        :NoLightsBeforeGuestsBecauseSleeping

    ::::: Programs we'd like running:
        call isRunning EvilLyrics %+ if "%ISRUNNING%" eq "0" (call EvilLyrics)
        call isRunning LastFM     %+ if "%ISRUNNING%" eq "0" (call LastFM    )

    ::::: Manual reminders:
        %COLOR_IMPORTANT% %+ echo Make sure things you want closed... are closed!        %+ pause
        %COLOR_IMPORTANT% %+ echo What about other computers?                            %+ pause %+ pause %+ cls
        %COLOR_IMPORTANT% %+ echo Bathroom medicine cabinet closed? Bedroom door closed? %+ pause
        %COLOR_IMPORTANT% %+ echo Any toys out that need putting away?                   %+ pause
        %COLOR_IMPORTANT% %+ echo Clear directory history and clean out %NEWCL ...       %+ call newcl
goto :END
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:quake3
	echo Disabling Windows key...
	:"d:\program files\I Hate This Key\IHateThisKey.exe"
	start /min IHateThisKey-helper.bat
	echo.
	echo Killing Setpoint to stop annoying caps lock OSD...
	kill /f setpoint
	echo.
    rem doesn't work anymore:
	rem echo Pausing torrents...
	rem call utorrent-control pausealltorrents
	echo.
	echo.
	echo.
	echos Now play Quake! When done, I will run "after quake" for you, if you simply
	pause
	after quake
goto :END
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:quakelive
		echo Disabling Windows key isn't as necessary in QuakeLive as with Quake 3...skipping!
		:start /min IHateThisKey-helper.bat
		echo.

	echo Killing Setpoint isn't as necessary in QuakeLive as with Quake 3 either...skipping!
		:kill /f setpoint
		echo.

	echo Pausing torrents doesn't work anymore...so you have to pause them yourself!
	echo (No need to close VNC afterward, it will be killed before QuakeLive starts...)
		call fire
		:call utorrent-control pausealltorrents
		pause
	echo.

	echo Stop your winamp visualizer...     and set music to 25%% or so...
		pause
		echo.
		echo.

	echo Change the stereo to CD mode + volume 42...
		call paus

	:Follow-up on previous promise to close VNC:
		echo Killing VNCViewer...
		kill /f vncviewer
		:Kill ambient reality effects (Ambilight system)
		echo.

	echo If ambilight is running, stop it now...
		:kill /f ARE
		pause
		echo.

	echo Stop any nuisance web browsers, handbrake encodes, AVG scans, etc...
		pause
		echo.
		echo.
		echo.
		echo.
		http://www.quakelive.com/

	echos Now play Quake! When done, I will run "after quake" for you, if you simply
		pause
		after quakelive
goto :END
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:party
	::::: Open pre-party checklist:
		call checkeditor
		%EDITOR "%PUBCL\house\party - pre-party checklist.txt"

        %COLOR_WARNING %+ echo Gonna turn on party lights next
        pause

	::::: Turn on party lights:
		call pon
goto :END
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:yardsale
	http://maps.google.com/
	http://www.drivingrouteplanner.com/
	call checkeditor
	call now
	call yardsale-craigslist
    http://www.yardsalesearch.com/garage-sales.html?week=0&date=0&zip=22312&r=1&q=
	http://www.yardsalesearch.com/garage-sales.html?week=0&date=0&zip=22312&r=5&q=
	%EDITOR "%PUBCL\journal\yard sales\yardsale-%_YEAR.html"
	call wait 5
goto :END
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:camping
	%tmpeditor "%PUBCL\EVENTS\camping canned message.txt"
	echo The checklist is online now! Opening in browser!
	http://docs.google.com/Doc?docid=dgjkmwpf_2cmtnb2&hl=en
goto :END
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:trip
	call checkeditor
	echo The checklist is online now! Opening in browser!
	https://docs.google.com/document/d/1xGdi2I2aKB0hOP3-SHGrRb63CJ3bigpoiZC17X8XKTM
goto :END
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::



::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:hangout
	call checkeditor
	echo The checklist is online now! Opening in browser!
	https://docs.google.com/document/d/1b0drGFd30tBMvxSPnp4gBTO7vZLPHwIfuV1bZRJOlZY
goto :END
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::



::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:inject
:injection
	call injection-history
    call diary
goto :END
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:appointment
	call checkeditor
    https://docs.google.com/document/d/1ezPCv4YHkralE3SURDgitQi9xed-ZFHELuk5AcPa7Ko/edit
goto :END
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

:END
	unset /q tmplog
	unset /q tmpeditor
	unset /q tmpfile
	unset /q year


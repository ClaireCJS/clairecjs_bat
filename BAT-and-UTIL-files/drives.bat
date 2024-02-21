@echo off

::::: VALIDATE ENVIRONMENT:
    call validate-environment-variable THE_ALPHABET
    call validate-in-path windowhide.exe


::::: PARAMETERS:
    if "%@UPPER[%2]"      eq "HIDDEN"    (set HIDDEN=1    %+ set MINIMIZE_FIRST=1)
    if "%@UPPER[%1]"      eq "EXITAFTER" (set EXITAFTER=1 %+ set MINIMIZE_FIRST=1)
    if "%MINIMIZE_FIRST%" eq "1"         (window minimize)
    if "%HIDDEN%"         eq "1"         (windowhide.exe /hide *drives.bat*hidden* %+ window /trans=0)



::::: MAIN:
    echo.
    setdos /x-678
    echo %ANSI_WIDE_LINE%  %EMOJI_GLOWING_STAR%%ansi_green_bright%%double_underline_on%Drives%double_underline_off%:%EMOJI_GLOWING_STAR% %ANSI_RESET%
    setdos /x0
    :or %drive in (%_drives     ) gosub describeDrive %drive%
    for %drive in (%THE_ALPHABET) gosub describeDrive %drive%:

goto :END

	:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
	:describeDrive [drive]
		if "%@READY[%drive%]" eq "1" goto :Ready_YES
		                             goto :Ready_NO
			:Ready_NO
				set DESC=[NOT READY]
                if "%HIDDEN%" eq "1" (dir %drive%:\)

				goto :Ready_DONE
			:Ready_YES
				set DESC=%@label[%drive%]
				goto :Ready_DONE
			:Ready_DONE
		%COLOR_WARNING%
        set color_to_use=%color_warning%
        set spacer=
        set EMOJITOUSE=%EMOJI_OPTICAL_DISK%
        set echocommand=call echobig
		if "%@REGEX[NOT READY,%DESC%]" eq "1" %COLOR_NORMAL%
		if "%@REGEX[HD[0-9]+G,%DESC%]" eq "1" .or. "%@REGEX[HD[0-9]+T,%DESC%]" eq "1" (
                set EMOJITOUSE=%EMOJI_HARD_DISK%
				color green on black
                set spacer=  ``
                set FOUND=0
				if "%@REGEX[FIRE,%DESC%]"    eq "1" (set FOUND=1 %+ %COLOR_RUN%                    %+ set echocommand=echos)
				if "%@REGEX[HADES,%DESC%]"   eq "1" (set FOUND=1 %+  color        red     on black %+ set echocommand=echos)
				if "%@REGEX[THAILOG,%DESC%]" eq "1" (set FOUND=1 %+  color        red     on black %+ set echocommand=echos %+ set EMOJITOUSE=%EMOJI_SMILING_FACE_WITH_HORNS%)
				if "%@REGEX[GOLIATH,%DESC%]" eq "1" (set FOUND=1 %+  color bright magenta on black %+ set echocommand=echos %+ set EMOJITOUSE=%EMOJI_PURPLE_HEART%)
				if "%@REGEX[WYVERN,%DESC%]"  eq "1" (set FOUND=1 %+  color bright magenta on black %+ set echocommand=echos %+ set EMOJITOUSE=%EMOJI_PURPLE_HEART%)
				if "%@REGEX[DEMONA,%DESC%]"  eq "1" (set FOUND=1 %+  color bright red     on black %+ set echocommand=echos %+ set EMOJITOUSE=%EMOJI_BAT%)
                if  %FOUND eq 0 (set spacer= ``)
        ) else (
                set spacer=
                if "%desc%" eq "[NOT READY]" (
	                set echocommand=echos 
                    %COLOR_SUBTLE% 
                    echos %FAINT_ON% 
                    REM unset /q spacer
                    set spacer=  ``
                    set desc=[%ITALICS_ON%NOT READY%ITALICS_OFF%]
                    set EMOJITOUSE=%EMOJI_WILTED_FLOWER%
                )
        )
        set ToBlinkOrNotToBlink=
        set Post=
        if "%drive%" eq "%_disk:" (
            set ToBlinkOrNotToBlink=%BLINK_ON%%ITALICS_Off%%UNDERLINE_ON%%@ANSI_BG[0,42,0]
            set Post=%UNDERLINE_OFF%%BLINK_OFF%%ANSI_RESET%%ANSI_COLOR_SUCCESS%%FAINT_ON%  `<`---- you are here%FAINT_OFF%
        )
        setdos /x-678
		%echocommand% %EmojiToUse%%spacer%%ToBlinkOrNotToBlink%%drive% %DESC%%POST%
        setdos /x0
        if "%echocommand%" eq "echos" (%COLOR_NORMAL%%FAINT_OFF% %+ echo.)
	return
	:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

:END


    if "%@UPPER[%1]" eq "EXITAFTER" exit

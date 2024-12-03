@echo off
 on break cancel

::::: If we are tethering, there is no hope:
    if "%TETHERING%" eq "1" goto :END


::::: USAGE:
	:: checkmappings
	:: checkmappings once - only run map-drives once afterward; give up after one try



::::: Wake up all harddrives, and GOLIATH/other sleepy computers:
    echo.
    call wake-all-drives
	call wake >nul

::::: CHECK IF WE'VE BEEN TOLD TO ONLY TRY ONCE OR NOT:
	if "%AUTOEXEC"=="1" set CHECKMAPPINGSONCE=1
	if "%ONCE"=="1"     set CHECKMAPPINGSONCE=1
	if "%1"=="once"     set CHECKMAPPINGSONCE=1




::::: MAP ALL DRIVES POSSIBLE:
	:BEGIN
		set ALLDRIVESMAPPED=0
		if "%NOERRORRESET%" eq "1" goto :NoErrorReset
			set      ERROR=0
            unset /q ERRORFULL
		:NoErrorReset
		call print-if-debug "ERROR[0] is %ERROR%!"


::: FIRE:
	if %FIRE_DOWN==1 goto :firedown1
        title Checking Fire mapping...
        :f "%@READY[%HD250G:]"  eq "0"   (call warning "ERROR! HD250G  [%HD250G%:] not mapped!" %+ set ERROR=1 %+ set ERRORFULL=%ERRORFULL% HD250G)
        :f "%@READY[%HD300G:]"  eq "0"   (call warning "ERROR! HD300G  [%HD300G%:] not mapped!" %+ set ERROR=1 %+ set ERRORFULL=%ERRORFULL% HD300G)
        :f "%@READY[%HD750G3:]" eq "0"   (call warning "ERROR! HD750G3 [%HD750G3:] not mapped!" %+ set ERROR=1 %+ set ERRORFULL=%ERRORFULL% HD750G3)
        :f "%@READY[%HD1000G:]" eq "0"   (call warning "ERROR! HD1000G [%HD1000G:] not mapped!" %+ set ERROR=1 %+ set ERRORFULL=%ERRORFULL% HD1000G)
	:firedown1

::: MIST:
	:MIST IS UNRELIABLE!:
    :f "%@READY[%HD25G:]"  eq "0"    (call warning "ERROR! HD25G    [%HD25G%:] not mapped!" %+ set ERROR=1)
	:::"%@READY[%HD40G:]"  eq "0"    (call warning "ERROR! HD40G    [%HD40G%:] not mapped!" %+ set ERROR=1)
	:::"%@READY[%HD60G:]"  eq "0"    (call warning "ERROR! HD60G    [%HD60G%:] not mapped!" %+ set ERROR=1)
	:::"%@READY[%HD80G:]"  eq "0"    (call warning "ERROR! HD80G    [%HD80G%:] not mapped!" %+ set ERROR=1)
	:::"%@READY[%HD80G2:]" eq "0"    (call warning "ERROR! HD80G2   [%HD80G2:] not mapped!" %+ set ERROR=1)
	:MIST IS UNRELIABLE!:
    :f "%@READY[%HD80G3:]" eq "0"    (call warning "ERROR! HD80G3   [%HD80G3:] not mapped!" %+ set ERROR=1)

::: HELL:
	if "%HELL_DOWN"=="1" goto :HELLDOWN1
        title Checking Hell mapping...
	:HELLDOWN1

::: MIST? OLD DRIVES?
	title Checking Mist mapping...
	::::"%@READY[%HD120G:]"  eq "0"  (call warning "ERROR! HD120G   [%HD120G%:] not mapped!" %+ set ERROR=1 %+ set ERRORFULL=%ERRORFULL% HD120G)
	:if "%@READY[%HD120G2:]" eq "0"  (call warning "ERROR! HD120G2  [%HD120G2:] not mapped!" %+ set ERROR=1 %+ set ERRORFULL=%ERRORFULL% HD120G2)
	:MIST IS UNRELIABLE!: %HD120G3   (call warning "ERROR! HD120G3  [%HD120G3:] not mapped!" %+ set ERROR=1 %+ set ERRORFULL=%ERRORFULL% HD120G3)
	:if "%@READY[%HD120G4:]" eq "0"  (call warning "ERROR! HD120G4  [%HD120G4:] not mapped!" %+ set ERROR=1 %+ set ERRORFULL=%ERRORFULL% HD120G4)
	:DRIVE UNHOOKED:
    :if "%@READY[%HD120G5:]" eq "0"  (call warning "ERROR! HD120G5  [%HD120G5:] not mapped!" %+ set ERROR=1 %+ set ERRORFULL=%ERRORFULL% HD120G5)

::: MAGIC:
	if "%MAGIC_DOWN"=="1" goto :MAGICDOWN
        title Checking Magic mapping...
         if "%@READY[%HD100G:]"   eq "0" (call warning "ERROR! HD100G   [%HD100G%:] not mapped!" %+ set ERROR=1 %+ set ERRORFULL=%ERRORFULL% HD100G)
        :if "%@READY[%HD140G:]"   eq "0" (call warning "ERROR! HD100G   [%HD140G%:] not mapped!" %+ set ERROR=1 %+ set ERRORFULL=%ERRORFULL% HD140G)
        :if "%@READY[%HD250G2A:]" eq "0" (call warning "ERROR! HD250G2A [%HD250G2A:]not mapped!" %+ set ERROR=1 %+ set ERRORFULL=%ERRORFULL% HD250G2A)
        :if "%@READY[%HD250G2B:]" eq "0" (call warning "ERROR! HD250G2B [%HD250G2B:]not mapped!" %+ set ERROR=1 %+ set ERRORFULL=%ERRORFULL% HD250G2B)
        :if "%@READY[%HD300G:]"   eq "0" (call warning "ERROR! HD300G   [%HD300G%:] not mapped!" %+ set ERROR=1 %+ set ERRORFULL=%ERRORFULL% HD300G)
        :if "%@READY[%HD500G:]"   eq "0" (call warning "ERROR! HD500G   [%HD500G%:] not mapped!" %+ set ERROR=1 %+ set ERRORFULL=%ERRORFULL% HD500G)
        :if "%@READY[%HD500G2:]"  eq "0" (call warning "ERROR! HD500G2  [%HD5002G:] not mapped!" %+ set ERROR=1 %+ set ERRORFULL=%ERRORFULL% HD5002G)
        if "%HD750G2DOWN"=="1" goto :HD750G2DOWN
            :if "%@READY[%HD750G2:]" eq "0" (call warning "ERROR!HD750G2[%HD750G2:] not mapped!" %+ set ERROR=1 %+ set ERRORFULL=%ERRORFULL% HD750G2)
        :HD750G2DOWN
	:MAGICDOWN

::: HADES:
	::: title Checking Hades mapping...

::: GOLIATH:
	title Checking Goliath mapping...
    if %GOLIATH_DOWN ne 1 (
        if "%@READY[%HD128G:]"   eq "0"  (call warning "ERROR! HD128G   [%HD128G%:]  not mapped!" %+ set ERROR=1 %+ set ERRORFULL=%ERRORFULL% HD128G)
	    if "%@READY[%HD512G:]"   eq "0"  (call warning "ERROR! HD512G   [%HD512G%:]  not mapped!" %+ set ERROR=1 %+ set ERRORFULL=%ERRORFULL% HD512G)
        :f "%@READY[%HD750G:]"   eq "0"  (call warning "ERROR! HD750G   [%HD750G%:]  not mapped!" %+ set ERROR=1 %+ set ERRORFULL=%ERRORFULL% HD750G)
        :f "%@READY[%HD1500G:]"  eq "0"  (call warning "ERROR! HD1500G  [%HD1500G:]  not mapped!" %+ set ERROR=1 %+ set ERRORFULL=%ERRORFULL% HD1500G)
        :f "%@READY[%HD2000G4:]" eq "0"  (call warning "ERROR! HD2000G4 [%HD2000G4:] not mapped!" %+ set ERROR=1 %+ set ERRORFULL=%ERRORFULL% HD2000G4)
        if "%@READY[%HD2000G5:]" eq "0"  (call warning "ERROR! HD2000G5 [%HD2000G5:] not mapped!" %+ set ERROR=1 %+ set ERRORFULL=%ERRORFULL% HD2000G5)
        if "%@READY[%HD4000G:]"  eq "0"  (call warning "ERROR! HD4000G  [%HD4000G%:] not mapped!" %+ set ERROR=1 %+ set ERRORFULL=%ERRORFULL% HD4000G)
        if "%@READY[%HD4000G2:]" eq "0"  (call warning "ERROR! HD4000G2 [%HD4000G2:] not mapped!" %+ set ERROR=1 %+ set ERRORFULL=%ERRORFULL% HD4000G2)
        :f "%@READY[%HD4000G3:]" eq "0"  (call warning "ERROR! HD4000G3 [%HD4000G3:] not mapped!" %+ set ERROR=1 %+ set ERRORFULL=%ERRORFULL% HD4000G3)
        if "%@READY[%HD4000G4:]" eq "0"  (call warning "ERROR! HD4000G4 [%HD4000G4:] not mapped!" %+ set ERROR=1 %+ set ERRORFULL=%ERRORFULL% HD4000G4)
        if "%@READY[%HD4000G5:]" eq "0"  (call warning "ERROR! HD4000G5 [%HD4000G5:] not mapped!" %+ set ERROR=1 %+ set ERRORFULL=%ERRORFULL% HD4000G5)
        if "%@READY[%HD6000G1:]" eq "0"  (call warning "ERROR! HD6000G1 [%HD6000G1:] not mapped!" %+ set ERROR=1 %+ set ERRORFULL=%ERRORFULL% HD6000G1)
        if "%@READY[%HD18T2:]"   eq "0"  (call warning "ERROR! HD18T2   [%HD18T2%:]  not mapped!" %+ set ERROR=1 %+ set ERRORFULL=%ERRORFULL% HD18T2)
        if "%@READY[%HD10T1:]"   eq "0"  (call warning "ERROR! HD10T1   [%HD10T1%:]  not mapped!" %+ set ERROR=1 %+ set ERRORFULL=%ERRORFULL% HD10T1)

        if %HD6000G3_DOWN ne 1 (
            if "%@READY[%HD6000G3:]" eq "0" (call warning "ERROR!HD6000G3[%HD6000G3%:]not mapped!"%+ set ERROR=1 %+ set ERRORFULL=%ERRORFULL% HD6000G3)
        )
    )

::: THAILOG:
     title Checking Thailog mapping...
        if 1 ne %HD240G_DOWN%   if "%@READY[%HD240G:]"   eq "0"  (call warning "ERROR! HD240G   [%HD240G%:]   not mapped!" %+ set ERROR=1 %+ set ERRORFULL=%ERRORFULL% HD240G)
        if 1 ne %HD240G2_DOWN%  if "%@READY[%HD240G2:]"  eq "0"  (call warning "ERROR! HD240G2  [%HD240G2%:]  not mapped!" %+ set ERROR=1 %+ set ERRORFULL=%ERRORFULL% HD240G2)
        if 1 ne %HD1500G2_DOWN  if "%@READY[%HD1500G2:]" eq "0"  (call warning "ERROR! HD1500G2 [%HD1500G2%:] not mapped!" %+ set ERROR=1 %+ set ERRORFULL=%ERRORFULL% HD1500G2)
        if 1 ne %HD2000G_DOWN%  if "%@READY[%HD2000G:]"  eq "0"  (call warning "ERROR! HD2000G  [%HD2000G%:]  not mapped!" %+ set ERROR=1 %+ set ERRORFULL=%ERRORFULL% HD2000G)
        if 1 ne %HD2000G2_DOWN  if "%@READY[%HD2000G2:]" eq "0"  (call warning "ERROR! HD2000G2 [%HD2000G2%:] not mapped!" %+ set ERROR=1 %+ set ERRORFULL=%ERRORFULL% HD2000G2)
        if 1 ne %HD2000G3_DOWN  if "%@READY[%HD2000G3:]" eq "0"  (call warning "ERROR! HD2000G3 [%HD2000G3%:] not mapped!" %+ set ERROR=1 %+ set ERRORFULL=%ERRORFULL% HD2000G3)

    if "%HD4000G6_DOWN%" eq "1"  goto :HD4000G6_DOWN_1
    	if 1 ne %HD4000G6_DOWN  if "%@READY[%HD4000G6:]" eq "0"  (call warning "ERROR! HD4000G6 [%HD4000G6%:] not mapped!" %+ set ERROR=1 %+ set ERRORFULL=%ERRORFULL% HD4000G6)
    :HD4000G6_DOWN_1

	if 1 ne %HD4000G7_DOWN  if "%@READY[%HD4000G7:]" eq "0"  (call warning "ERROR! HD4000G7 [%HD4000G7:] not mapped!"  %+ set ERROR=1 %+ set ERRORFULL=%ERRORFULL% HD4000G7)
	if 1 ne %HD6000G2_DOWN  if "%@READY[%HD6000G2:]" eq "0"  (call warning "ERROR! HD6000G2 [%HD6000G2:] not mapped!"  %+ set ERROR=1 %+ set ERRORFULL=%ERRORFULL% HD6000G2)
	if 1 ne %HD10T2_DOWN%   if "%@READY[%HD10T2:]"   eq "0"  (call warning "ERROR! HD10T2   [%HD10T2%:]  not mapped!"  %+ set ERROR=1 %+ set ERRORFULL=%ERRORFULL% HD10T2)
	if 1 ne %HD18T1_DOWN%   if "%@READY[%HD18T1:]"   eq "0"  (call warning "ERROR! HD18T1   [%HD18T1%:]  not mapped!"  %+ set ERROR=1 %+ set ERRORFULL=%ERRORFULL% HD18T1)

::: DEMONA:
	if 1 ne %HD1000G3_DOWN% if "%@READY[%HD1000G3:]" eq "0"  (call warning "ERROR! HD1000G3 [%HD1000G3:] not mapped!"  %+ set ERROR=1 %+ set ERRORFULL=%ERRORFULL% %HD1000G3)
	if 1 ne   %HD18T3_DOWN% if "%@READY[%HD18T3:]"   eq "0"  (call warning "ERROR! HD18T3   [%HD18T3%:]  not mapped!"  %+ set ERROR=1 %+ set ERRORFULL=%ERRORFULL% HD18T3)
	if 1 ne   %HD22T1_DOWN% if "%@READY[%HD22T1:]"   eq "0"  (call warning "ERROR! HD22T1   [%HD22T1%:]  not mapped!"  %+ set ERROR=1 %+ set ERRORFULL=%ERRORFULL% HD22T1)

::: WYVERN:
	if 1 ne  %HD2T1_DOWN    if "%@READY[%HD2T1%:]"   eq "0"  (call warning "ERROR! HD2T1  [%HD2T1%:] not mapped!"      %+ set ERROR=1 %+ set ERRORFULL=%ERRORFULL% HD2T1)
	if 1 ne %HD18T1_DOWN    if "%@READY[%HD18T1:]"   eq "0"  (call warning "ERROR! HD18T1 [%HD18T1:] not mapped!"      %+ set ERROR=1 %+ set ERRORFULL=%ERRORFULL% HD18T1)
        if 1 ne %HD20T2_DOWN    if "%@READY[%HD20T2:]"   eq "0"  (call warning "ERROR! HD20T2 [%HD20T2:] not mapped!"      %+ set ERROR=1 %+ set ERRORFULL=%ERRORFULL% HD20T2)


::::: CHECK TO SEE IF THERE WERE ANY ERRORS:
		call print-if-debug "ERROR[1] is %ERROR%!"
		if %ERROR==1 goto :ERROR
		if %ERROR==2 goto :FATAL_ERROR
		             goto :SUCCESS

::::: IF THERE WERE ANY ERRORS, TRY REMAPPING THE DRIVES JUST ONCE:
	:ERROR
        call map-drives once
        echo %%CHECKMAPPINGSONCE is %CHECKMAPPINGSONCE
        if "%CHECKMAPPINGSONCE"=="1" goto :noretry
            set ERROR=2
            goto :BEGIN
        :noretry

::::: IF THERE ARE STILL ERRORS, LET THE USER KNOW:
	if %ERROR==0 goto :ERRORS_FIXED
	:FATAL_ERROR
        %COLOR_WARNING% %+ echo *** AT LEAST ONE ERROR HAS OCCURRED.  HIT CTRL-BREAK TO ABORT. ***
                           echo *** AT LEAST ONE ERROR HAS OCCURRED.  HIT CTRL-BREAK TO ABORT. ***
                           echo *** AT LEAST ONE ERROR HAS OCCURRED.  HIT CTRL-BREAK TO ABORT. ***
                           echo *** AT LEAST ONE ERROR HAS OCCURRED.  HIT CTRL-BREAK TO ABORT. ***
        %COLOR_REMOVAL% %+ echo * FULL ERROR:
        %COLOR_ALARM%   %+ echos %ERRORFULL%
        %COLOR_NORMAL%  %+ echo.
    :ERRORS_FIXED
	if "%AUTOEXEC" == "1" goto :nopause
	if "%1" eq "nopause" .or. "%2" eq "nopause" .or. "%3" eq "nopause" .or. "%4" eq "nopause" goto :nopause
		pause
		pause
		pause
		pause
	goto :did_pause
		::::well, :nopause used to be here, but I moved it one line below so it wont beep every reboot... hopefully
		call white-noise 3
		:nopause
		call sleep 2
	:did_pause
	goto :FAILURE



::::: CURRENTLY THE END-BEHAVIOUR OF SUCCESS AND FAILURE IS IDENTICAL:
	:FAILURE
		set ALLDRIVESMAPPED=0
		goto :Cleanup

	:SUCCESS
		set ALLDRIVESMAPPED=1
		if "%1"=="/verbose" .or. "%2"=="/verbose" .or. "%3"=="/verbose" .or. "%4"=="/verbose" (%COLOR_SUCCESS% %+ echo Regardless of above error messages, drives are NOW successfully mapped. %+ %COLOR_NORMAL%)


:Cleanup
	unset /q CHECKMAPPINGSONCE
    call fix-window-title
:END

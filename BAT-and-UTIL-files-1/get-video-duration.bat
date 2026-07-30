@echo off
@if not "%_4VER%" == "" on break cancel

rem ============================================================================
rem  get-video-duration.bat
rem
rem  Gets a media file's duration with ffprobe, sets useful environment
rem  variables for the calling shell, and displays a large blinking result.
rem ============================================================================


rem CLEAR PUBLIC RESULTS FIRST, SO A FAILED CALL NEVER LEAVES STALE ANSWERS:
        set "VIDEO_DURATION_IN_SECONDS="
        set "VIDEO_DURATION_IN_MINUTES="
        set "VIDEO_DURATION_IN_HOURS="
        set "VIDEO_DURATION="
        set "VIDEO_DURATION_HH_MM_SS="
        set "RESULT="


rem CAPTURE PARAMETERS IN BOTH TCC AND CMD:
        if not "%_4VER%" == "" goto :CAPTURE_PARAMETERS_TCC

        :CAPTURE_PARAMETERS_CMD
                set "GVD_FILE=%~1"
                set "GVD_EXTRA=%~2"
                for %%F in ("%~1") do set "GVD_DISPLAY_FILE=%%~nxF"
        goto :PARAMETERS_CAPTURED

        :CAPTURE_PARAMETERS_TCC
                set "GVD_FILE=%@UNQUOTE[%1]"
                set "GVD_EXTRA=%@UNQUOTE[%2]"
                set "GVD_DISPLAY_FILE=%@FILENAME[%GVD_FILE]"

        :PARAMETERS_CAPTURED
        if "1" == "%GVD_DEBUG%" echo DEBUG: FILE=[%GVD_FILE%] EXTRA=[%GVD_EXTRA%] DISPLAY=[%GVD_DISPLAY_FILE%] TCC=[%_4VER%]


rem USAGE / HELP:
        if "%GVD_FILE%" == ""       goto :USAGE
        if /i "%GVD_FILE%" == "-h"     goto :USAGE
        if /i "%GVD_FILE%" == "--h"    goto :USAGE
        if /i "%GVD_FILE%" == "/h"     goto :USAGE
        if /i "%GVD_FILE%" == "-?"     goto :USAGE
        if /i "%GVD_FILE%" == "--?"    goto :USAGE
        if /i "%GVD_FILE%" == "/?"     goto :USAGE
        if /i "%GVD_FILE%" == "-help"  goto :USAGE
        if /i "%GVD_FILE%" == "--help" goto :USAGE
        if /i "%GVD_FILE%" == "/help"  goto :USAGE
        if "1" == "%GVD_DEBUG%" echo DEBUG: Help checks passed.


rem VALIDATE PARAMETERS:
        if "%GVD_EXTRA%" == "" goto :ONE_PARAMETER_RECEIVED
        echo.
        echo ERROR: Please pass exactly one quoted video filename.
        echo.
        set "GVD_EXIT_CODE=64"
        goto :USAGE_BODY

        :ONE_PARAMETER_RECEIVED
        if "1" == "%GVD_DEBUG%" echo DEBUG: Extra-parameter check passed.

        if exist "%GVD_FILE%" goto :INPUT_FILE_EXISTS
        echo.
        echo ERROR: Video file does not exist:
        echo        "%GVD_FILE%"
        echo.
        set "GVD_EXIT_CODE=2"
        goto :CLEANUP

        :INPUT_FILE_EXISTS
        if "1" == "%GVD_DEBUG%" echo DEBUG: Input exists.


rem VALIDATE ENVIRONMENT:
rem (Use where.exe explicitly because this environment also has a where.bat.)
        where.exe ffprobe.exe >nul 2>nul
        if not errorlevel 1 goto :FFPROBE_FOUND
        echo.
        echo ERROR: ffprobe.exe was not found in PATH.
        echo        Install FFmpeg or add ffprobe's folder to PATH.
        echo.
        set "GVD_EXIT_CODE=3"
        goto :CLEANUP

        :FFPROBE_FOUND

        where.exe powershell.exe >nul 2>nul
        if not errorlevel 1 goto :POWERSHELL_FOUND
        echo.
        echo ERROR: powershell.exe was not found in PATH.
        echo.
        set "GVD_EXIT_CODE=3"
        goto :CLEANUP

        :POWERSHELL_FOUND
        if "1" == "%GVD_DEBUG%" echo DEBUG: Environment validation passed.


rem READ THE DURATION:
        set "GVD_EXIT_CODE=0"
        set "GVD_RAW_SECONDS="
        set "GVD_TEMP_FILE=%TEMP%\get-video-duration-%RANDOM%-%RANDOM%.tmp"

        ffprobe.exe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "%GVD_FILE%" >"%GVD_TEMP_FILE%" 2>nul
        if "1" == "%GVD_DEBUG%" echo DEBUG: ffprobe ERRORLEVEL=[%ERRORLEVEL%] TEMP=[%GVD_TEMP_FILE%]
        if errorlevel 1 goto :FFPROBE_FAILED

        set /p GVD_RAW_SECONDS=<"%GVD_TEMP_FILE%"
        if "1" == "%GVD_DEBUG%" echo DEBUG: RAW_SECONDS=[%GVD_RAW_SECONDS%]
        if not defined GVD_RAW_SECONDS goto :FFPROBE_FAILED
        if /i "%GVD_RAW_SECONDS%" == "N/A" goto :FFPROBE_FAILED


rem CALCULATE NUMERIC AND HUMAN-READABLE RESULTS:
rem
rem Numeric values use invariant decimals, with no pointless trailing zeroes.
rem The readable result rounds only for display, to the nearest whole second.
        powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -Command "$d=[double]::Parse($env:GVD_RAW_SECONDS,[Globalization.CultureInfo]::InvariantCulture); function N([double]$n){$n.ToString('0.######',[Globalization.CultureInfo]::InvariantCulture)}; function P([double]$n){$n.ToString('0.##',[Globalization.CultureInfo]::InvariantCulture)}; function U([long]$n,[string]$one,[string]$many){if($n -eq 1){[string]$n+' '+$one}else{[string]$n+' '+$many}}; $w=[long][Math]::Round($d,[MidpointRounding]::AwayFromZero); $tm=[long][Math]::Floor($w/60); $h=[long][Math]::Floor($w/3600); $m=$tm-($h*60); $s=$w-($tm*60); $showSeconds=0;$n2='';$u2=''; if($w -lt 1){$n1='<1';$u1='second'}elseif($w -lt 60){$n1=[string]$w;$u1=if($w -eq 1){'second'}else{'seconds'}}else{$n1=[string]$tm;$u1=if($tm -eq 1){'minute'}else{'minutes'};if($s -ne 0){$showSeconds=1;$n2=[string]$s;$u2=if($s -eq 1){'second'}else{'seconds'}}}; $line1=$n1+' '+$u1;if($showSeconds){$line1+=', '+$n2+' '+$u2}; $showHours=if($d -gt 300){1}else{0};$hoursNumber='';$hoursSuffix='';$hoursBreakdown='';$hoursLine='';if($showHours){$hoursNumber=P ($d/3600);if($h -gt 0){$clock=U $h 'hr' 'hrs';if($m -ne 0){$clock+=', '+(U $m 'minute' 'minutes')};if($s -ne 0){$clock+=', '+(U $s 'second' 'seconds')};$hoursBreakdown='  ('+$clock+')'};$hoursSuffix='hours'+$hoursBreakdown;$hoursLine=$hoursNumber+' '+$hoursSuffix};$pretty=$line1;if($showHours){$pretty+='; '+$hoursLine}; 'VIDEO_DURATION_IN_SECONDS='+(N $d); 'VIDEO_DURATION_IN_MINUTES='+(N ($d/60)); 'VIDEO_DURATION_IN_HOURS='+(N ($d/3600)); 'VIDEO_DURATION_HH_MM_SS='+('{0:00}:{1:00}:{2:00}' -f $h,$m,$s); 'VIDEO_DURATION='+$pretty; 'RESULT='+$pretty; 'GVD_BIG_NUMBER_1='+$n1; 'GVD_BIG_UNIT_1='+$u1; 'GVD_SHOW_SECONDS='+$showSeconds; 'GVD_BIG_NUMBER_2='+$n2; 'GVD_BIG_UNIT_2='+$u2; 'GVD_SHOW_HOURS='+$showHours; 'GVD_HOURS_NUMBER='+$hoursNumber; 'GVD_HOURS_SUFFIX='+$hoursSuffix; 'GVD_HOURS_BREAKDOWN='+$hoursBreakdown" >"%GVD_TEMP_FILE%"
        if "1" == "%GVD_DEBUG%" echo DEBUG: PowerShell ERRORLEVEL=[%ERRORLEVEL%]
        if errorlevel 1 goto :CALCULATION_FAILED

        for /f "usebackq tokens=1,* delims==" %%A in ("%GVD_TEMP_FILE%") do set "%%A=%%B"
        if "1" == "%GVD_DEBUG%" echo DEBUG: RESULT=[%RESULT%]
        if not defined RESULT goto :CALCULATION_FAILED


rem PRETTY OUTPUT:
        set "GVD_STAR=*"
        set "GVD_SPARKLES=*"
        set GVD_LQUOTE="
        set GVD_RQUOTE="
        set "GVD_BLINK_ON=%BLINK_SLOW_ON%"
        set "GVD_BLINK_OFF=%BLINK_SLOW_OFF%"
        if not defined GVD_BLINK_ON set "GVD_BLINK_ON=%BLINK_ON%"
        if not defined GVD_BLINK_OFF set "GVD_BLINK_OFF=%BLINK_OFF%"

        if "%_4VER%" == "" goto :DECORATORS_READY
        set "GVD_LQUOTE=%@CHAR[8220]"
        set "GVD_RQUOTE=%@CHAR[8221]"
        if defined EMOJI_STAR goto :CHOOSE_DECORATORS
        if exist C:\BAT\set-emoji.bat call C:\BAT\set-emoji.bat

        :CHOOSE_DECORATORS
                if defined EMOJI_GLOWING_STAR set "GVD_STAR=%EMOJI_GLOWING_STAR%"
                if defined EMOJI_STAR set "GVD_STAR=%EMOJI_STAR%"
                if defined EMOJI_SPARKLES set "GVD_SPARKLES=%EMOJI_SPARKLES%"

        :DECORATORS_READY
        echo.
        echo %GVD_SPARKLES% %ANSI_COLOR_ADVICE%Duration of %GVD_LQUOTE%%ITALICS_ON%%GVD_DISPLAY_FILE%%ITALICS_OFF%%ANSI_COLOR_ADVICE%%GVD_RQUOTE%:%ANSI_COLOR_NORMAL%
        echo.

        if defined BIG_TOP if defined BIG_BOT goto :DISPLAY_WITH_CONFIGURED_ANSI

rem FALLBACK ANSI SETUP (FOR A CLEAN TCC OR CMD SESSION):
        if not "%_4VER%" == "" set "GVD_ESC=%@CHAR[27]"
        if not defined GVD_ESC for /f "delims=#" %%E in ('"prompt #$E# & for %%E in (1) do rem"') do set "GVD_ESC=%%E"

        if not defined GVD_ESC goto :DISPLAY_WITHOUT_ANSI
        if "%GVD_SHOW_SECONDS%" == "1" goto :DISPLAY_FALLBACK_TWO_VALUES

        :DISPLAY_FALLBACK_ONE_VALUE
                echo %GVD_ESC%#3%GVD_ESC%[1;96m%GVD_STAR% %GVD_ESC%[5;92m%GVD_BIG_NUMBER_1%%GVD_ESC%[25;96m %GVD_BIG_UNIT_1%%GVD_ESC%[0m
                echo %GVD_ESC%#4%GVD_ESC%[1;96m%GVD_STAR% %GVD_ESC%[5;92m%GVD_BIG_NUMBER_1%%GVD_ESC%[25;96m %GVD_BIG_UNIT_1%%GVD_ESC%[0m
        goto :DISPLAY_HOURS

        :DISPLAY_FALLBACK_TWO_VALUES
                echo %GVD_ESC%#3%GVD_ESC%[1;96m%GVD_STAR% %GVD_ESC%[5;92m%GVD_BIG_NUMBER_1%%GVD_ESC%[25;96m %GVD_BIG_UNIT_1%, %GVD_ESC%[5;92m%GVD_BIG_NUMBER_2%%GVD_ESC%[25;96m %GVD_BIG_UNIT_2%%GVD_ESC%[0m
                echo %GVD_ESC%#4%GVD_ESC%[1;96m%GVD_STAR% %GVD_ESC%[5;92m%GVD_BIG_NUMBER_1%%GVD_ESC%[25;96m %GVD_BIG_UNIT_1%, %GVD_ESC%[5;92m%GVD_BIG_NUMBER_2%%GVD_ESC%[25;96m %GVD_BIG_UNIT_2%%GVD_ESC%[0m
        goto :DISPLAY_HOURS

        :DISPLAY_WITH_CONFIGURED_ANSI
                if "%GVD_SHOW_SECONDS%" == "1" goto :DISPLAY_CONFIGURED_TWO_VALUES

        :DISPLAY_CONFIGURED_ONE_VALUE
                echo %BIG_TOP%%ANSI_COLOR_IMPORTANT%%GVD_STAR% %GVD_BLINK_ON%%ANSI_COLOR_SUCCESS%%GVD_BIG_NUMBER_1%%GVD_BLINK_OFF%%ANSI_COLOR_IMPORTANT% %GVD_BIG_UNIT_1%%ANSI_COLOR_NORMAL%%ANSI_ERASE_TO_EOL%
                echo %BIG_BOT%%ANSI_COLOR_IMPORTANT%%GVD_STAR% %GVD_BLINK_ON%%ANSI_COLOR_SUCCESS%%GVD_BIG_NUMBER_1%%GVD_BLINK_OFF%%ANSI_COLOR_IMPORTANT% %GVD_BIG_UNIT_1%%ANSI_COLOR_NORMAL%%ANSI_ERASE_TO_EOL%
        goto :DISPLAY_HOURS

        :DISPLAY_CONFIGURED_TWO_VALUES
                echo %BIG_TOP%%ANSI_COLOR_IMPORTANT%%GVD_STAR% %GVD_BLINK_ON%%ANSI_COLOR_SUCCESS%%GVD_BIG_NUMBER_1%%GVD_BLINK_OFF%%ANSI_COLOR_IMPORTANT% %GVD_BIG_UNIT_1%, %GVD_BLINK_ON%%ANSI_COLOR_SUCCESS%%GVD_BIG_NUMBER_2%%GVD_BLINK_OFF%%ANSI_COLOR_IMPORTANT% %GVD_BIG_UNIT_2%%ANSI_COLOR_NORMAL%%ANSI_ERASE_TO_EOL%
                echo %BIG_BOT%%ANSI_COLOR_IMPORTANT%%GVD_STAR% %GVD_BLINK_ON%%ANSI_COLOR_SUCCESS%%GVD_BIG_NUMBER_1%%GVD_BLINK_OFF%%ANSI_COLOR_IMPORTANT% %GVD_BIG_UNIT_1%, %GVD_BLINK_ON%%ANSI_COLOR_SUCCESS%%GVD_BIG_NUMBER_2%%GVD_BLINK_OFF%%ANSI_COLOR_IMPORTANT% %GVD_BIG_UNIT_2%%ANSI_COLOR_NORMAL%%ANSI_ERASE_TO_EOL%
        goto :DISPLAY_HOURS

        :DISPLAY_WITHOUT_ANSI
                if "%GVD_SHOW_SECONDS%" == "1" echo %GVD_STAR% %GVD_BIG_NUMBER_1% %GVD_BIG_UNIT_1%, %GVD_BIG_NUMBER_2% %GVD_BIG_UNIT_2%
                if not "%GVD_SHOW_SECONDS%" == "1" echo %GVD_STAR% %GVD_BIG_NUMBER_1% %GVD_BIG_UNIT_1%

        :DISPLAY_HOURS
                echo.
                if "%GVD_SHOW_HOURS%" == "1" echo %GVD_STAR% %ANSI_COLOR_LESS_IMPORTANT%Hours:   %ANSI_COLOR_SUCCESS%%GVD_HOURS_NUMBER%%ANSI_COLOR_IMPORTANT%%GVD_HOURS_BREAKDOWN%%ANSI_COLOR_NORMAL%%ANSI_ERASE_TO_EOL%
                echo %GVD_STAR% %ANSI_COLOR_LESS_IMPORTANT%Seconds: %ANSI_COLOR_SUCCESS%%VIDEO_DURATION_IN_SECONDS%%ANSI_COLOR_NORMAL%%ANSI_ERASE_TO_EOL%
                echo %GVD_STAR% %ANSI_COLOR_LESS_IMPORTANT%Clock:   %ANSI_COLOR_SUCCESS%%VIDEO_DURATION_HH_MM_SS%%ANSI_COLOR_NORMAL%%ANSI_ERASE_TO_EOL%
                echo.
        goto :CLEANUP


rem ERRORS:
        :FFPROBE_FAILED
                echo.
                echo ERROR: ffprobe could not read a duration from:
                echo        "%GVD_FILE%"
                echo        The file may be invalid, unsupported, or missing duration metadata.
                echo.
                set "GVD_EXIT_CODE=4"
        goto :CLEANUP

        :CALCULATION_FAILED
                echo.
                echo ERROR: Could not calculate a readable duration from:
                echo        "%GVD_RAW_SECONDS% seconds"
                echo.
                set "GVD_EXIT_CODE=5"
        goto :CLEANUP


rem USAGE TEXT:
        :USAGE
                set "GVD_EXIT_CODE=64"

        :USAGE_BODY
                if defined ANSI_COLOR_ADVICE echos %ANSI_COLOR_ADVICE%
                echo USAGE:
                echo     call get-video-duration "video-file"
                echo     get-video-duration --help
                echo.
                echo EXAMPLE:
                echo     call get-video-duration "D:\Video\movie with spaces.mkv"
                echo.
                echo OUTPUT EXAMPLES:
                echo     30-second video:  * 30 seconds
                echo     24:28 video:       * 24 minutes, 28 seconds
                echo                       * Hours:   0.41
                echo                       * Seconds: 1468
                echo                       * Clock:   00:24:28
                echo     67-minute video:  * 67 minutes
                echo                       * Hours:   1.12  (1 hr, 7 minutes)
                echo.
                echo SETS THESE VARIABLES IN THE CALLING ENVIRONMENT:
                echo     VIDEO_DURATION_IN_SECONDS   Numeric total seconds
                echo     VIDEO_DURATION_IN_MINUTES   Numeric total minutes
                echo     VIDEO_DURATION_IN_HOURS     Numeric total hours
                echo     VIDEO_DURATION_HH_MM_SS     Clock form, such as 01:07:00
                echo     VIDEO_DURATION              Human-readable duration
                echo     RESULT                      Same human-readable duration
                echo.
                echo NOTES:
                echo     Quote filenames containing spaces or special characters.
                echo     Durations over five minutes also get a decimal-hours line.
                echo     The primary numeric values are double-height and blinking.
                echo     Requires ffprobe.exe and powershell.exe in PATH.
                echo     Optional troubleshooting: set GVD_DEBUG=1
                if defined ANSI_COLOR_NORMAL echos %ANSI_COLOR_NORMAL%
        goto :CLEANUP


rem CLEAN UP ONLY PRIVATE VARIABLES; PUBLIC RESULTS MUST SURVIVE THE CALL:
        :CLEANUP
                if defined GVD_TEMP_FILE if exist "%GVD_TEMP_FILE%" del /q "%GVD_TEMP_FILE%" >nul 2>nul
                set "GVD_RAW_SECONDS="
                set "GVD_TEMP_FILE="
                set "GVD_ESC="
                set "GVD_FILE="
                set "GVD_EXTRA="
                set "GVD_DISPLAY_FILE="
                set "GVD_BIG_NUMBER_1="
                set "GVD_BIG_UNIT_1="
                set "GVD_SHOW_SECONDS="
                set "GVD_BIG_NUMBER_2="
                set "GVD_BIG_UNIT_2="
                set "GVD_SHOW_HOURS="
                set "GVD_HOURS_NUMBER="
                set "GVD_HOURS_SUFFIX="
                set "GVD_HOURS_BREAKDOWN="
                set "GVD_STAR="
                set "GVD_SPARKLES="
                set "GVD_LQUOTE="
                set "GVD_RQUOTE="
                set "GVD_BLINK_ON="
                set "GVD_BLINK_OFF="

                if not defined GVD_EXIT_CODE set "GVD_EXIT_CODE=0"
                if "%GVD_EXIT_CODE%" == "0"  goto :RETURN_0
                if "%GVD_EXIT_CODE%" == "2"  goto :RETURN_2
                if "%GVD_EXIT_CODE%" == "3"  goto :RETURN_3
                if "%GVD_EXIT_CODE%" == "4"  goto :RETURN_4
                if "%GVD_EXIT_CODE%" == "5"  goto :RETURN_5
                goto :RETURN_64

        :RETURN_0
                set "GVD_EXIT_CODE="
                exit /b 0
        :RETURN_2
                set "GVD_EXIT_CODE="
                exit /b 2
        :RETURN_3
                set "GVD_EXIT_CODE="
                exit /b 3
        :RETURN_4
                set "GVD_EXIT_CODE="
                exit /b 4
        :RETURN_5
                set "GVD_EXIT_CODE="
                exit /b 5
        :RETURN_64
                set "GVD_EXIT_CODE="
                exit /b 64

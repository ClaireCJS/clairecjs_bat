@loadbtm on
@rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ PRINT-MESSAGE.bat — BEGIN ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ PRINT-MESSAGE.bat — BEGIN ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ PRINT-MESSAGE.bat — BEGIN ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@Echo Off
@on break cancel
@setdos /x0

set print_message_running=1

:REQUIRES: set-colors.bat to be run first —— to define certain environment variables that represent ANSI character control sequences

:USAGE: call print-message MESSAGE_TYPE "message" [0|1|2|silent|3|big]              - arg1=message/colorType, arg2=message, arg3=pause (1) or not (0), or be silent (2), or display in big mode (3)
:USAGE:                    ^^^^^^^^^^^^—— MESSAGE_TYPE must match an existing message from the MESSAGE_TYPES list
:USAGE:                                  ^^^^^^^———— use "{PERCENT}" in your message to insert a   "%"   into your message
:USAGE:                                  ^^^^^^^———— use     "\n"    in your message to insert a newline into your message but only if %NEWLINE_REPLACEMENT% is set to 1, which must be done EACH time you do this
:USAGE:
:USAGE: call print-message demo      ————— to run demo suite
:USAGE: call print-message TEST      ————— to run internal test suite
:USAGE: call print-message TEST fast ————— to run internal test suite without a pause for keystroke in between each one
:USAGE:                                           
:USAGE: call print-message message without quotes —— WRONG!! —— no 3rd arg of 0|1 will cause the whole line to be treated as a message without a message type. This is really only meant for processing malformed calls in a non-execution-breaking way. We’re NOT supposed to do it this way.
:USAGE:
:USAGE: ENVIRONMENT: set PRINTMESSAGE_OPT_SUPPRESS_AUDIO=1 to suppress audio effects. DOES INDEED need to be set each call.
:USAGE: ENVIRONMENT: set                        SLEEPING=1 to suppress audio effects. DOES  *NOT* need to be set each call.
:USAGE: ENVIRONMENT: set             NEWLINE_REPLACEMENT=1 to replace \n w/ newlines. DOES INDEED need to be set each call.
:USAGE:
:USAGE: NOTE: “hand” and “question” windows system sounds are currently used 
:USAGE:           —— hear them with the “beep hand” & “beep question” commands
:USAGE:           ——  set them with the Control Panel->Sounds menu



rem MESSAGE TYPES LIST: PLEASE ADD ANY NEW MESSAGE TYPES TO THIS LIST BEFORE IMPLEMENTING THEM!!!!!!!!!!!!!!!!!!!!!!!!!!!
    set                 MESSAGE_TYPES=WARNING WARNING_LESS WARNING_SOFT ALARM REMOVAL IMPORTANT IMPORTANT_LESS LESS_IMPORTANT ADVICE NORMAL DEBUG UNIMPORTANT SUBTLE COMPLETION SUCCESS CELEBRATION FATAL_ERROR ERROR_FATAL ERROR 
    set MESSAGE_TYPES_WITHOUT_ALIASES=WARNING WARNING_LESS              ALARM REMOVAL IMPORTANT IMPORTANT_LESS                ADVICE NORMAL DEBUG UNIMPORTANT SUBTLE COMPLETION SUCCESS CELEBRATION FATAL_ERROR             ERROR 
    if "%1" == "vars_only" (goto :END) %+ rem we like to grab these 2 env varibles when environm is run, even before print-message is ever run, via this call: if not defined MESSAGE_TYPES (call print-message vars_only)
    rem ^^^ Gther all these into a nice looking environment variable where they are each appropriately ansi-colored with: gather-message-types-into-pretty-environment-variable.bat






REM DEBUG:
        set DEBUG_PRINTMESSAGE=0
        rem don’t change until @WIDTH[] function is released to public and implemented here:
            set FUDGE_FACTOR=10                         

REM Initialize variables:
    set PM_PARAMS=%*
    set PM_PARAMS2=%2$
    set PM_PARAM1=%1
    set PM_PARAM2=%2``
    set PM_PARAM3=%3
    set TYPE=
    set EXECUTE_PROTECTION_PAUSES=-666
    set OUR_COLORTOUSE=
    if %SLEEPING eq 1 .or. "%PM_PARAM3" == "2" .or. "%PM_PARAM3" == "silent" .or. "%PM_PARAM3" == "quiet" (set PRINTMESSAGE_OPT_SUPPRESS_AUDIO=1)
    
    rem echoerr %ANSI_COLOR_DEBUG%DEBUG: PRINTMESSAGE_OPT_SUPPRESS_AUDIO is %PRINTMESSAGE_OPT_SUPPRESS_AUDIO% ... PM_PARAM3 IS %PM_PARAM3 %ANSI_COLOR_NORMAL%


REM Process parameters
                                  set FAST=0
    if "%PM_PARAM2%" != "fast" (set   FAST=0   )                                 %+ REM used for "test fast" 
    if "%PM_PARAM2%" == "fast" (set   FAST=1   )                                 %+ REM used for "test fast" 
    if "%PM_PARAM1%" == "demo" (goto :DemoSuite)                                 
    if "%PM_PARAM1%" == "test" (goto :TestSuite)
    if "%PM_PARAM1%" == "none" (goto :None     )
    rem if "%PM_PARAM3%" == ""                     (
    rem         set MESSAGE=%@UNQUOTE[`%PM_PARAMS`]``
    rem         if %DEBUG_PRINTMESSAGE eq 1 (%COLOR_DEBUG% %+ echoerr debug branch 2: message is now %MESSAGE %+ %COLOR_NORMAL%)
    rem         REM set TYPE=NORMAL                                         making this assumption hurts flexibility for misshappen calls to this script. We like to alzheimer’s-proof things around here.
    rem         REM set OUR_COLORTOUSE=%COLOR_NORMAL%                       making this assumption hurts flexibility for misshappen calls to this script. We like to alzheimer’s-proof things around here.
    rem         REM changed my mind: set EXECUTE_PROTECTION_PAUSES=1                         we pause by default becuase calling this way means the user doesn’t know what they are doing quite as well
    rem )
    set MESSAGE=Null
    set SILENT_MESSAGE=0
    set TYPE=%PM_PARAM1%                                                         %+ REM both the color and message type, actually

    rem moved to end of this block      set  MESSAGE=%@UNQUOTE[`%PM_PARAMS2`]``
    set BIG_MESSAGE=0
    if "%PM_PARAM3%"       == "1" .or. "%PM_PARAM3%" == "2" .or. "%PM_PARAM3%" == "3" .or. "%PM_PARAM3%" == "4" .or. "%PM_PARAM3%" == "" (set MESSAGE=%@UNQUOTE[`%PM_PARAM2%`])
    if "%PM_PARAM3%"       == "1"                                (set  EXECUTE_PROTECTION_PAUSES=1)
    if "%PM_PARAM2%"       == "yes"                              (set  EXECUTE_PROTECTION_PAUSES=1)                         %+ REM capture a few potential call mistakes
    if "%PM_PARAM2%"       == "pause"                            (set  EXECUTE_PROTECTION_PAUSES=1)                         %+ REM capture a few potential call mistakes
    if 1 eq %PRINTMESSAGE_OPT_SUPPRESS_AUDIO                     (set  SILENT_MESSAGE=1)
    if "%PM_PARAM3%"       == "2" .or. "%PM_PARAM3%" == "silent" (set  SILENT_MESSAGE=1 %+ set PM_PARAMS3= %+ set PM_PARAMS2=%2 %4$)
    if "%PM_PARAM3%"       == "3" .or. "%PM_PARAM3%" == "big"    (set     BIG_MESSAGE=1 %+ set PM_PARAMS3= %+ set PM_PARAMS2=%2 %4$)
    if %DEBUG_PRINTMESSAGE eq  1                                 (echoerr %ANSI_COLOR_DEBUG%- debug branch 1 because %%PM_PARAM3 is %PM_PARAM3 - btw %%PM_PARAM2=%PM_PARAM2 - message is now %MESSAGE%ANSI_RESET% %+ echoerr DEBUG: TYPE=%TYPE%,EXECUTE_PROTECTION_PAUSES=%EXECUTE_PROTECTION_PAUSES%,MESSAGE=%MESSAGE%)
    set MESSAGE=%@UNQUOTE[`%PM_PARAMS2`]``

    iff defined COLOR_%TYPE% then
            set     OUR_COLORTOUSE=%[COLOR_%TYPE%]
            set OUR_ANSICOLORTOUSE=%[ANSI_COLOR_%TYPE%]
            echos %ansi_color_yellow%
    endiff
    if not defined OUR_COLORTOUSE  (
            if %DEBUG_PRINTMESSAGE% eq 1 (echoerr %ANSI_COLOR_DEBUG% %RED_FLAG% Oops! Let’s try setting OUR_COLORTOUSE to %%COLOR_%@UPPER[%PM_PARAM1])
            set TYPE=%PM_PARAM1%
            set OUR_COLORKEY=COLOR_%TYPE%
            if %DEBUG_PRINTMESSAGE eq 1 (
                echoerr colorkey is ``%OUR_COLORKEY%
                echoerr     next is %[%OUR_COLORKEY%]
            )
            set OUR_COLORTOUSE=%[%OUR_COLORKEY%]
            set MESSAGE=%@UNQUOTE[`%PM_PARAMS2`]``
    )
    if %DEBUG_PRINTMESSAGE eq 1 (echoerr TYPE=%TYPE% OUR_COLORTOUSE=%OUR_COLORTOUSE% EXECUTE_PROTECTION_PAUSES=%EXECUTE_PROTECTION_PAUSES% MESSAGE is: %MESSAGE% )

REM Validate parameters
        set print_message_running=2
        iff "1" != "%VALIDATED_PRINTMESSAGE_ENV%"  then
                if not defined COLOR_%TYPE%    (echoerr %ANSI_COLOR_fatal_error%This variable COLOR_%TYPE% should be an existing COLOR_* variable in our environment %+ *pause %+ goto :END)
                if not defined MESSAGE         (echoerr %ANSI_COLOR_fatal_error%$0 called without a message %+ *pause %+ go)
                if "%@PLUGIN[StripAnsi]" == "" (echoerr %ANSI_COLOR_fatal_error%$0 called without StripAnsi plugin loaded %+ *pause %+ go)
                if "1" != "%beep_validated_in_path%" call validate-in-path beep.bat 
                set beep_validated_in_path=1
                set GOTOEND=0
                echos %reverse_on%
                if not defined BLINK_OFF                           gosub validate BLINK_OFF 
                if not defined REVERSE_ON                          gosub validate REVERSE_ON 
                if not defined REVERSE_OFF                         gosub validate REVERSE_OFF 
                if not defined ITALICS_ON                          gosub validate ITALICS_ON 
                if not defined ITALICS_OFF                         gosub validate ITALICS_OFF 
                if not defined BIG_TEXT_LINE_1                     gosub validate BIG_TEXT_LINE_1 
                if not defined BIG_TEXT_LINE_2                     gosub validate BIG_TEXT_LINE_2 
                if not defined OUR_COLORTOUSE                      gosub validate OUR_COLORTOUSE 
                if not defined EXECUTE_PROTECTION_PAUSES           gosub validate EXECUTE_PROTECTION_PAUSES 
                if not defined EMOJI_TRUMPET                       gosub validate EMOJI_TRUMPET 
                if not defined ANSI_RESET                          gosub validate ANSI_RESET 
                if not defined EMOJI_FLEUR_DE_LIS                  gosub validate EMOJI_FLEUR_DE_LIS 
                if not defined ANSI_COLOR_WARNING                  gosub validate ANSI_COLOR_WARNING 
                if not defined ANSI_COLOR_IMPORTANT                gosub validate ANSI_COLOR_IMPORTANT 
                if not defined RED_FLAG                            gosub validate RED_FLAG 
                if not defined EMOJI_WARNING                       gosub validate EMOJI_WARNING 
                if not defined big_top                             gosub validate big_top 
                if not defined BIG_TOP_ON                          gosub validate BIG_TOP_ON 
                if not defined big_bot                             gosub validate big_bot 
                if not defined BIG_BOT_ON                          gosub validate BIG_BOT_ON 
                if not defined FAINT_ON                            gosub validate FAINT_ON 
                if not defined FAINT_OFF                           gosub validate FAINT_OFF 
                if not defined EMOJI_WARNING                       gosub validate EMOJI_WARNING 
                if not defined EMOJI_WHITE_EXCLAMATION_MARK        gosub validate EMOJI_WHITE_EXCLAMATION_MARK 
                if not defined EMOJI_RED_EXCLAMATION_MARK          gosub validate EMOJI_RED_EXCLAMATION_MARK 
                if not defined EMOJI_STAR                          gosub validate EMOJI_STAR 
                if not defined STAR                                gosub validate STAR 
                if not defined STAR2                               gosub validate STAR2 
                if not defined EMOJI_GLOWING_STAR                  gosub validate EMOJI_GLOWING_STAR 
                if not defined EMOJI_ALARM_CLOCK                   gosub validate EMOJI_ALARM_CLOCK 
                if not defined ENDASH                              gosub validate ENDASH 
                if not defined EMOJI_MAGNIFYING_GLASS_TILTED_RIGHT gosub validate EMOJI_MAGNIFYING_GLASS_TILTED_RIGHT 
                if not defined EMOJI_MAGNIFYING_GLASS_TILTED_LEFT  gosub validate EMOJI_MAGNIFYING_GLASS_TILTED_LEFT  
                echos %reverse_off%
                set   VALIDATED_PRINTMESSAGE_ENV=1
                if "1" == "%GOTOEND%" (goto /i :END)              
        endiff

                goto :validate_subroutine_done
                        :validate [validatee]
                                rem echo validate called with validatee=“%validatee%”
                                iff "" ==  "%[%validatee]" then
                                        echo %ansi_color_fatal_error%!!! ERROR !!!   %validatee%  needs to be defined%ansi_color_normal%
                                        goto /i END
                                endiff
                        return
                :validate_subroutine_done


REM convert special characters
    set MESSAGE=%@UNQUOTE[%MESSAGE]``
    set ORIGINAL_MESSAGE=%MESSAGE%``
    REM might want to do if %NEWLINE_REPLACEMENT eq 1 instead:
    iff "%NEWLINE_REPLACEMENT" == "1" then
            set MESSAGE=%@REPLACE[\n,%@CHAR[12]%@CHAR[13],%@REPLACE[\t,%@CHAR[9],%MESSAGE]]``
            unset /q NEWLINE_REPLACEMENT
    endiff
    rem sixteen percent symbols is insane, but what is needed:
    set MESSAGE=%@REPLACE[{PERCENT},%%%%%%%%%%%%%%%%,%MESSAGE]``
    


REM Type alias/synonym handling
    if "%TYPE%" == "ERROR_FATAL"    (
        set TYPE=FATAL_ERROR
    )  else (
            if "%TYPE%" == "IMPORTANT_LESS" (
                set TYPE=LESS_IMPORTANT
            ) else (
                if "%TYPE%" == "WARNING_SOFT"   (set TYPE=WARNING_LESS)
            )
    )

REM Behavior overides and message decorators depending on the type of message?
                                       set DECORATOR_LEFT=              %+ set DECORATOR_RIGHT=
    if  "%TYPE%"  == "ADVICE"         (set DECORATOR_LEFT=%EMOJI_BACKHAND_INDEX_POINTING_RIGHT% `` %+ set DECORATOR_RIGHT= %EMOJI_BACKHAND_INDEX_POINTING_LEFT% %+ goto decorator_defined) 
    if  "%TYPE%"  == "WARNING_LESS"   (set DECORATOR_LEFT=%STAR% ``     %+ set DECORATOR_RIGHT= %STAR% %+ goto decorator_defined) 
    rem "%TYPE%"  == "WARNING"        (set DECORATOR_LEFT=%EMOJI_WARNING%%EMOJI_WARNING%%EMOJI_WARNING% %blink%!!%blink_off% `` %+ set DECORATOR_RIGHT= %blink%!!%blink_off% %EMOJI_WARNING%%EMOJI_WARNING%%EMOJI_WARNING% %+ goto decorator_defined)
    rem "%TYPE%"  == "IMPORTANT"      (set DECORATOR_LEFT=%ANSI_RED%%EMOJI_TRUMPET_COLORABLE%%@ANSI_FG[255,127,0]%EMOJI_TRUMPET_COLORABLE%%@ansi_fg[212,234,0]%EMOJI_TRUMPET_COLORABLE%%ANSI_BRIGHT_GREEN%%EMOJI_TRUMPET_COLORABLE%%ANSI_BRIGHT_BLUE%%EMOJI_TRUMPET_COLORABLE%%@ANSI_FG[200,0,200]%EMOJI_TRUMPET_COLORABLE%  %ANSI_RESET%%@ANSI_FG[255,0,0]%reverse_on%%blink_on%%EMOJI_FLEUR_DE_LIS%%blink_off%%reverse_off%%ANSI_COLOR_IMPORTANT% `` %+ set DECORATOR_RIGHT= %ANSI_RESET%%@ANSI_FG[255,0,0]%reverse_on%%blink_on%%EMOJI_FLEUR_DE_LIS%%blink_off%%reverse_off%%ANSI_COLOR_IMPORTANT%  %@ANSI_FG[200,0,200]%EMOJI_TRUMPET_FLIPPED%%ANSI_BRIGHT_BLUE%%EMOJI_TRUMPET_FLIPPED%%ANSI_BRIGHT_GREEN%%EMOJI_TRUMPET_FLIPPED%%@ansi_fg[212,234,0]%EMOJI_TRUMPET_FLIPPED%%@ANSI_FG[255,127,0]%EMOJI_TRUMPET_FLIPPED%%ANSI_RED%%EMOJI_TRUMPET_FLIPPED% %+ goto decorator_defined)
    rem "%TYPE%"  == "IMPORTANT"      (set DECORATOR_LEFT=%ANSI_RED%%EMOJI_TRUMPET_COLORABLE%%@ANSI_FG[255,127,0]%EMOJI_TRUMPET_COLORABLE%%@ansi_fg[212,234,0]%EMOJI_TRUMPET_COLORABLE%%ANSI_BRIGHT_GREEN%%EMOJI_TRUMPET_COLORABLE%%ANSI_BRIGHT_BLUE%%EMOJI_TRUMPET_COLORABLE%%@ANSI_FG[200,0,200]%EMOJI_TRUMPET_COLORABLE%  %ANSI_RESET%%BLINKING_PENTAGRAM%%ANSI_COLOR_IMPORTANT% %DOUBLE_UNDERLINE_ON%`` %+ set DECORATOR_RIGHT=%DOUBLE_UNDERLINE_OFF% %ANSI_RESET%%BLINKING_PENTAGRAM%%ANSI_COLOR_IMPORTANT%  %@ANSI_FG[200,0,200]%EMOJI_TRUMPET_FLIPPED%%ANSI_BRIGHT_BLUE%%EMOJI_TRUMPET_FLIPPED%%ANSI_BRIGHT_GREEN%%EMOJI_TRUMPET_FLIPPED%%@ansi_fg[212,234,0]%EMOJI_TRUMPET_FLIPPED%%@ANSI_FG[255,127,0]%EMOJI_TRUMPET_FLIPPED%%ANSI_RED%%EMOJI_TRUMPET_FLIPPED% %+ goto decorator_defined)
    if  "%TYPE%"  == "WARNING"        (set DECORATOR_LEFT=%RED_FLAG%%RED_FLAG%%RED_FLAG%%ANSI_COLOR_WARNING% %EMOJI_WARNING%%EMOJI_WARNING%%EMOJI_WARNING% %@ANSI_BG_RGB[0,0,255]%blink%!!%blink_off% ``  %+  set DECORATOR_RIGHT= %blink%!!%blink_off%%ANSI_COLOR_WARNING% %EMOJI_WARNING%%EMOJI_WARNING%%EMOJI_WARNING% %RED_FLAG%%RED_FLAG%%RED_FLAG% %+ goto decorator_defined)
    if  "%TYPE%"  == "IMPORTANT"      (set DECORATOR_LEFT=%ANSI_RED%%EMOJI_TRUMPET_COLORABLE%%@ANSI_FG[255,127,0]%EMOJI_TRUMPET_COLORABLE%%@ansi_fg[212,234,0]%EMOJI_TRUMPET_COLORABLE%%ANSI_BRIGHT_GREEN%%EMOJI_TRUMPET_COLORABLE%%ANSI_BRIGHT_BLUE%%EMOJI_TRUMPET_COLORABLE%%@ANSI_FG[200,0,200]%EMOJI_TRUMPET_COLORABLE% %ANSI_RESET%%BLINKING_PENTAGRAM%%ANSI_COLOR_IMPORTANT%  `` %+ set DECORATOR_RIGHT=  %ANSI_RESET%%BLINKING_PENTAGRAM%%ANSI_COLOR_IMPORTANT% %@ANSI_FG[200,0,200]%EMOJI_TRUMPET_FLIPPED%%ANSI_BRIGHT_BLUE%%EMOJI_TRUMPET_FLIPPED%%ANSI_BRIGHT_GREEN%%EMOJI_TRUMPET_FLIPPED%%@ansi_fg[212,234,0]%EMOJI_TRUMPET_FLIPPED%%@ANSI_FG[255,127,0]%EMOJI_TRUMPET_FLIPPED%%ANSI_RED%%EMOJI_TRUMPET_FLIPPED% %+ goto decorator_defined)
    REM "%TYPE%"  == "ADVICE"         (set DECORATOR_LEFT=`-->`         %+ set DECORATOR_RIGHT= %+ goto decorator_defined) 
    if  "%TYPE%"  == "DEBUG"          (set DECORATOR_LEFT=- DEBUG: ``   %+ set DECORATOR_RIGHT= %+ goto decorator_defined=)
    rem "%TYPE%"  == "LESS_IMPORTANT" .or. "%TYPE%" == "IMPORTANT_LESS" (set DECORATOR_LEFT=%STAR% %ANSI_COLOR_IMPORTANT_LESS%``  %+ set DECORATOR_RIGHT= %+ goto decorator_defined) %+ rem some bug was making the color bold, so we fixed it by putting the ansi color here, even though that’s not how this is designed to be used
    if  "%TYPE%"  == "LESS_IMPORTANT" .or. "%TYPE%" == "IMPORTANT_LESS" (set DECORATOR_LEFT=%STAR2% %ANSI_COLOR_IMPORTANT_LESS%`` %+ set DECORATOR_RIGHT= %+ goto decorator_defined) %+ rem some bug was making the color bold, so we fixed it by putting the ansi color here, even though that’s not how this is designed to be used
    if  "%TYPE%"  == "LESS_IMPORTANT" .or. "%TYPE%" == "IMPORTANT_LESS" (set DECORATOR_LEFT=%ansi_color_important%%UPSIDE_DOWN_STAR% %ANSI_COLOR_IMPORTANT_LESS% `` %+ set DECORATOR_RIGHT= %+ goto decorator_defined) %+ rem some bug was making the color bold, so we fixed it by putting the ansi color here, even though that’s not how this is designed to be used
    if  "%TYPE%"  == "UNIMPORTANT"    (set DECORATOR_LEFT=...           %+ set DECORATOR_RIGHT= %+ goto decorator_defined)
    REM to avoid issues with the redirection character, ADVICE’s left-decorator needs to be inserted at runtime if it contains a “>” character. Could proably avoid this with setdos
    if  "%TYPE%"  == "SUCCESS"        (set DECORATOR_LEFT=%REVERSE%%BLINK%%EMOJI_CHECK_MARK%%EMOJI_CHECK_MARK%%EMOJI_CHECK_MARK%%BLINK_OFF%%REVERSE_OFF% ``        %+ set DECORATOR_RIGHT= %REVERSE%%BLINK%%EMOJI_CHECK_MARK%%EMOJI_CHECK_MARK%%EMOJI_CHECK_MARK%%REVERSE_OFF%%BLINK_OFF% %PARTY_POPPER%%EMOJI_BIRTHDAY_CAKE% %+ goto decorator_defined)
    if  "%TYPE%"  == "COMPLETION"     (set DECORATOR_LEFT=*** ``        %+ set DECORATOR_RIGHT=! *** %+ goto decorator_defined)
    rem "%TYPE%"  == "CELEBRATION"    (set DECORATOR_LEFT=%emoji_STAR%%emoji_STAR%%emoji_STAR% %BLINK_ON%%EMOJI_PARTYING_FACE% %ITALICS%``        %+ set DECORATOR_RIGHT=%ITALICS_OFF%! %EMOJI_PARTYING_FACE%%BLINK_OFF% %emoji_STAR%%emoji_STAR%%emoji_STAR% %+ goto decorator_defined)
    if  "%TYPE%"  == "CELEBRATION"    (set DECORATOR_LEFT=%blink_off%%emoji_STAR%%emoji_STAR%%emoji_STAR% %BLINK_ON%%EMOJI_PARTYING_FACE% %ITALICS%``        %+ set DECORATOR_RIGHT=%ITALICS_OFF% %EMOJI_PARTYING_FACE%%BLINK_OFF% %emoji_STAR%%emoji_STAR%%emoji_STAR% %+ goto decorator_defined)
    if  "%TYPE%"  == "REMOVAL"        (set DECORATOR_LEFT=%RED_SKULL%%SKULL%%RED_SKULL% ``        %+ set DECORATOR_RIGHT= %RED_SKULL%%SKULL%%RED_SKULL% %+ goto decorator_defined)
    if  "%TYPE%"  == "ERROR"          (set DECORATOR_LEFT=*** ``        %+ set DECORATOR_RIGHT= *** %+ goto decorator_defined)
    if  "%TYPE%"  == "FATAL_ERROR"    (set DECORATOR_LEFT=***** !!! ``  %+ set DECORATOR_RIGHT= !!! ***** %+ goto decorator_defined)
    if  "%TYPE%"  == "ALARM"          (set DECORATOR_LEFT=* ``          %+ set DECORATOR_RIGHT= * %+ goto decorator_defined)
    if  "%TYPE%"  == "NORMAL"         (set DECORATOR_LEFT=              %+ set DECORATOR_RIGHT= %+ goto decorator_defined) 
    rem 20240419 moved to after setting COLOR_TO_USE so we can start setting that before the right decorator in case the message contents changed the color: set DECORATED_MESSAGE=%DECORATOR_LEFT%%MESSAGE%%DECORATOR_RIGHT%
    :decorator_defined        


REM We’re going to change the cursor color to the cursor color associated with this message, IF one was defined in set-ansi:
        rem set HEX=%[COLOR_%TYPE%_HEX]
        rem echoerr setting cursor to %HEX%
        if defined COLOR_%TYPE%_HEX echoserr %@ANSI_CURSOR_COLOR_CHANGE_HEX[%[COLOR_%TYPE%_HEX]]


REM We’re going to update the window title to the message. If possible, strip any ANSI color codes from it:

        rem this became unreliable: if not "1"== "%PLUGIN_STRIPANSI_LOADED" (goto :No_Title_Stripping)
        if not plugin stripansi (goto :No_Title_Stripping)
                set CLEAN_MESSAGE=%@STRIPANSI[%ORIGINAL_MESSAGE]
                goto :Set_Title_Var_Now
        :No_Title_Stripping
                set CLEAN_MESSAGE=%ORIGINAL_MESSAGE%
        :Add_Decorators_AFter_Newlines
        :Set_Title_Var_Now
                set TITLE=%CLEAN_MESSAGE%

        REM But first let’s decorate the window title for certain message types Prior to actually updating the window title:
                if "%TYPE%" ==          "DEBUG" (set TITLE=%EMOJI_MAGNIFYING_GLASS_TILTED_RIGHT% %title% %EMOJI_MAGNIFYING_GLASS_TILTED_LEFT% %+ goto done_defining_title)
                if "%TYPE%" == "LESS_IMPORTANT" (set TITLE=%EMOJI_STAR% %title% %EMOJI_STAR% %+ goto done_defining_title)
                if "%TYPE%" == "IMPORTANT_LESS" (set TITLE=%EMOJI_STAR% %title% %EMOJI_STAR% %+ goto done_defining_title)
                if "%TYPE%" ==      "IMPORTANT" (set TITLE=%EMOJI_GLOWING_STAR%%EMOJI_GLOWING_STAR% %title% %EMOJI_GLOWING_STAR%%EMOJI_GLOWING_STAR% %+ goto done_defining_title)
                if "%TYPE%" ==          "ALARM" (set TITLE=%EMOJI_ALARM_CLOCK%%EMOJI_ALARM_CLOCK%  %title%  %EMOJI_ALARM_CLOCK%%EMOJI_ALARM_CLOCK% %+ goto done_defining_title)
                if "%TYPE%" ==   "WARNING_LESS" (set TITLE=%EMOJI_WARNING%%title% %+ goto done_defining_title)
                if "%TYPE%" ==        "WARNING" (set TITLE=%EMOJI_WARNING%%EMOJI_WARNING%%title!%EMOJI_WARNING%%EMOJI_WARNING% %+ goto done_defining_title)
                if "%TYPE%" ==          "ERROR" (set TITLE=%EMOJI_RED_EXCLAMATION_MARK%%EMOJI_RED_EXCLAMATION_MARK% ERR0R: %title% %EMOJI_RED_EXCLAMATION_MARK%%EMOJI_RED_EXCLAMATION_MARK% %+ goto done_defining_title)
                if "%TYPE%" ==    "FATAL_ERROR" (set TITLE=%EMOJI_RED_EXCLAMATION_MARK%%EMOJI_RED_EXCLAMATION_MARK%%EMOJI_RED_EXCLAMATION_MARK% FATAL ERROR: %title% %EMOJI_RED_EXCLAMATION_MARK%%EMOJI_RED_EXCLAMATION_MARK%%EMOJI_RED_EXCLAMATION_MARK% %+ goto done_defining_title)
                :done_defining_title

        REM Then actually set the current window title to our newly-constructed window title text:        
                title %title%


REM Some messages will be decorated with audio:
        if %PRINTMESSAGE_OPT_SUPPRESS_AUDIO ne 1 .and. 1 ne %PRINTMESSAGE_OPT_SUPPRESS_AUDIO (
                if "%TYPE%" == "DEBUG"  (
                        call beep.bat  lowest 1
                ) else (
                        if "%TYPE%" == "ADVICE" (call beep.bat highest 3)
                )
        )

REM Pre-Message pause based on message type (pausable messages need a litle visual cushion):
        if %EXECUTE_PROTECTION_PAUSES% eq 1 (echoerr.)           

REM Pre-Message determination of if we do a big header or not:
                                                                                         set BIG_HEADER=0
        if  "%TYPE%" == "ERROR" .or. "%TYPE%" == "FATAL_ERROR" .or. "%TYPE%" == "ALARM" (set BIG_HEADER=1)

REM Pre-Message determination of how many times we will display the message:
        set print_message_running=5
        set HOW_MANY=1 
        if "%TYPE%" == "CELEBRATION" (set HOW_MANY=1 2)
        if "%TYPE%" ==       "ERROR" (set HOW_MANY=1 2 3)
        if "%TYPE%" == "FATAL_ERROR" (set HOW_MANY=1 2 3)



REM Actually display the message:
        echos %ANSI_COLOR_BRIGHT_GREEN%
        set FIRST=0
        set SECOND=0
        :actually_display-the_message
        setdos /x-6

        iff 1 eq %BIG_MESSAGE% then
                iff     0 eq %FIRST% then
                                          set FIRST=1
                elseiff 1 eq %FIRST% then
                                          set SECOND=1
                endiff                        
        endiff

        rem Assemble our message, including resetting the color via ansi codes (%OUR_ANSICOLORTOUSE%) before adding the right decorator
        rem in case the color was changed within the message itself.  
        rem ((( However, for FATAL_ERROR, we want the color to persist because we set a special color )))
        rem ((( for one of the repeated messages and want the decorator to remain that  special color )))
        if "%TYPE%" != "FATAL_ERROR" (
            set DECORATED_MESSAGE=%DECORATOR_LEFT%%MESSAGE%%OUR_ANSICOLORTOUSE%%DECORATOR_RIGHT%
        ) else (
            set DECORATED_MESSAGE=%DECORATOR_LEFT%%MESSAGE%%DECORATOR_RIGHT%
        )

        if defined %[ANSI_COLOR_%type%] set OUR_ANSICOLORTOUSE=%[ANSI_COLOR_%type%]

        set DECORATED_MESSAGE=%@Replace[%NEWLINE%,%DECORATOR_RIGHT%%NEWLINE%%[ANSI_COLOR_%type%]%DECORATOR_LEFT%,%DECORATED_MESSAGE%]


        REM display our opening big-header, if we are in big-header mode
        rem production: if %BIG_HEADER eq 1 (set COLOR_TO_USE=%OUR_COLORTOUSE% %+ call bigecho %@ANSI_MOVE_TO_COL[0]****%DECORATOR_LEFT%%@UPPER[%TYPE%]%DECORATOR_RIGHT%****%ANSI_RESET%%ANSI_ERASE_TO_EOL%)
        rem test:

        if %BIG_HEADER eq 1 (
                SET BIG_ECHO_MSG_TO_USE=%our_ansicolortouse%****%DECORATOR_LEFT%%@UPPER[%TYPE%]%DECORATOR_RIGHT%****
                rem There was a lot of weirdness with background color bleedthrough when doing this:
                rem call bigecho %BIG_ECHO_MSG_TO_USE%
                rem I opened this bug report with Windows Terminal to fix it: 
                rem https://github.com/microsoft/terminal/issues/17771
                rem We assemble the double-height lines manually here, without using bigecho.bat, to have the most control over that bug:
                echoerr %@ansi_move_to_col[0]%BIG_TOP%%BIG_ECHO_MSG_TO_USE%%BIG_TEXT_END%%ANSI_RESET%
                echoerr %@ansi_move_to_col[0]%BIG_BOT%%BIG_ECHO_MSG_TO_USE%%BIG_TEXT_END%%ANSI_RESET%%ANSI_EOL%
                rem call bigecho %BIG_ECHO_MSG_TO_USE%
                rem TODO bigechoerr.bat!
        )

        REM repeat the message the appropriate number of times
                SET SPACER_FATAL_ERROR=                 ``

        REM Is the message too long to display in double_height?
                set SKIP_DOUBLE_HEIGHT=0
                iff not plugin StripANSI then
                        set STRIPPED_MESSAGE=%DECORATED_MESSAGE%``
                else
                        set STRIPPED_MESSAGE=%@stripansi[%DECORATED_MESSAGE]``
                endiff
                set LEN=%@LEN[%STRIPPED_MESSAGE]
                if not %@EVAL[%len*2] lt %@EVAL[%_COLUMNS-%FUDGE_FACTOR%] (set SKIP_DOUBLE_HEIGHT=1)

        echos %ANSI_COLOR_BLUE%
        for %msgNum in (%HOW_MANY%) do (           
                set REM=handle pre-message formatting [color/blinking/reverse/italics/faint], based on what type of message and which message in the sequence of repeated messages it is

                if "%OUR_ANSICOLORTOUSE%" == "" ( 
                        %OUR_COLORTOUSE% 
                ) else (
                        echoserr %OUR_ANSICOLORTOUSE%
                )                        

                set REM=handle big mode
                if "1" == "%BIG_MESSAGE%" .and. "1" == "%FIRST%" .and. "1" !=  "%SECOND%" (echoserr %big_top%)
                if "1" == "%BIG_MESSAGE%" .and. "1" == "%FIRST%" .and. "1" ==  "%SECOND%" (echoserr %big_bot%)

                set REM=Special decorators that are only for the message itself, not the header/fooder:

                if "%TYPE%"     == "FATAL_ERROR"      (echoserr %ANSI_RESET%%SPACER_FATAL_ERROR%%ANSI_COLOR_FATAL_ERROR%``)
                if "%TYPE%"     ==       "ERROR"      (echoserr     ``)
                if  %BIG_HEADER ==    1               (echoserr %BLINK_ON%)
                if "%TYPE%"     == "SUBTLE"           (echoserr %FAINT_ON%)
                if "%TYPE%"     == "UNIMPORTANT"      (echoserr %FAINT_ON%)
                if "%TYPE%"     == "SUCCESS"          (echoserr %BOLD_ON%)
                if "%TYPE%"     == "CELEBRATION"  (
                        if        %msgNum        == 1 (echoserr %BIG_TOP_ON%``)
                        if        %msgNum        == 2 (echoserr %BIG_BOT_ON%``)
                )
                if "%TYPE%"     == "ERROR"   (
                        if %@EVAL[%msgNum mod 2] == 1 (echoserr %REVERSE_ON%)
                        if %@EVAL[%msgNum mod 2] == 0 (echoserr %REVERSE_OFF%%BLINK_OFF%)
                )
                if "%TYPE%" == "WARNING" (
                        echoserr %ANSI_COLOR_WARNING%
                )
                if "%TYPE%" == "FATAL_ERROR" (
                        if %@EVAL[%msgNum mod 3] == 0 (echoserr %ANSI_COLOR_FATAL_ERROR%%BLINK_OFF%)
                        rem @EVAL[%msgNum mod 2] == 1 (echoserr %REVERSE_OFF%)
                        if        %msgNum        == 2 (echoserr %BLINK_ON%)
                        if %@EVAL[%msgNum mod 2] == 0 (echoserr %REVERSE_ON%)
                        if        %msgNum        != 3 (echoserr %ANSI_COLOR_FATAL_ERROR%%ITALICS_OFF%)
                        if        %msgNum        == 4 .and. 1 ne %SKIP_DOUBLE_HEIGHT% (
                                echoerr %BIG_TOP%%ANSI_COLOR_FATAL_ERROR%%@ANSI_BG_RGB[128,0,0]%DECORATED_MESSAGE%%@ANSI_BG_RGB[128,0,0]
                                echoserr %BIG_TEXT_LINE_2%%@ANSI_BG_RGB[128,0,0]%DECORATED_MESSAGE%%@ANSI_BG_RGB[128,0,0]
                        ) else (
                                rem echoserr %ANSI_COLOR_FATAL_ERROR%
                        )
                )

                set REM=HACK: Decorators with ">" in them need to be manually outputted here at the last minute to avoid issues with ">" being the redirection character, though setdos could work around this
                        if "%TYPE%" == "ADVICE" (echoserr `----> `)

                set REM=actually print the message, unless it’s fatal error line 4 which has special double-height handling:
                        if "%TYPE%" == "FATAL_ERROR" .and. %msgNum == 4  .and. 1 ne %SKIP_DOUBLE_HEIGHT% (
                                echoserr %ANSI_COLOR_IMPORTANT%   ``
                         ) else (
                                if %msgNum == 2 (echoserr %blink_on%)
                                echoserr %DECORATED_MESSAGE%
                         )

                set REM=handle post-message formatting
                        if "%TYPE%"     == "SUBTLE"      (echoserr %FAINT_OFF%)
                        if "%TYPE%"     == "UNIMPORTANT" (echoserr %FAINT_OFF%)
                        if "%TYPE%"     == "SUCCESS"     (echoserr %BOLD_OFF%)
                        if "%TYPE%"     == "CELEBRATION"  (
                                if %msgNum == 1 (echoserr %BIG_TEXT_END%%ANSI_RESET%``)
                                if %msgNum == 2 (echoserr %BIG_TEXT_END%%ANSI_RESET%%ANSI_EOL%``)
                        )

                        echoerr %ANSI_COLOR_NORMAL%%ANSI_RESET%%ANSI_ERASE_TO_EOL%
        )

        echos %ansi_color_blue%
        REM display our closing big-header, if we are in big-header mode:
                rem if %BIG_HEADER eq 1 (set COLOR_TO_USE=%OUR_COLORTOUSE% %+ call bigecho ****%DECORATOR_LEFT%%@UPPER[%TYPE%]%[DECORATOR_RIGHT]****%ANSI_RESET%%ANSI_ERASE_TO_EOL%)
                iff %BIG_HEADER eq 1 then
                        echoerr %BIG_TOP%%BIG_ECHO_MSG_TO_USE%%BIG_TEXT_END%%ANSI_RESET%%ANSI_EOL%
                        echoerr %BIG_BOT%%BIG_ECHO_MSG_TO_USE%%BIG_TEXT_END%%ANSI_RESET%%ANSI_EOL%
                endiff

        REM If big mode, go back to print the 2ⁿᵈ/lower-½ line:
                if "1" == "%BIG_MESSAGE%" .and. "1" !=  "%SECOND%" goto :actually_display-the_message


        
REM Post-message delays and pauses
        echos %ANSI_COL0R_MAGENTA%
        set print_message_running=10
        setdos /x0
        set DO_DELAY=0    
        REM EXECUTE_PROTECTION_PAUSES=0 WOULD BE FATAL beause we set this from calling scripts for automation
        if "%TYPE%" == "WARNING"                                   (set DO_DELAY=1)
        if "%TYPE%" == "ERROR"       .or. "%TYPE%" == "ALARM"      (set EXECUTE_PROTECTION_PAUSES=1)
        if "%TYPE%" == "FATAL_ERROR" .or. "%TYPE%" == "FATALERROR" (set DO_DELAY=2)
        if "%TYPE%" == "FATAL_ERROR"                               (set EXECUTE_PROTECTION_PAUSES=2)

REM Post-message beeps and sound effects
        if %PRINTMESSAGE_OPT_SUPPRESS_AUDIO eq 1 (goto :No_Beeps_2)
            if "%TYPE%" == "CELEBRATION" .or. "%TYPE%" == "COMPLETION" (beep exclamation)
            if "%TYPE%" == "ERROR" .or. "%TYPE%" == "ALARM"   (
                    beep 145 1 
                    beep 120 1 
                    beep 100 1 
                    beep  80 1 
                    beep  65 1 
                    beep  50 1 
                    beep  40 1 
                    beep hand
            )         
            if "%TYPE%" == "WARNING" (
                    *beep 60 1 
                    *beep 69 1        
                    REM beep hand was overkil
                    beep question
            )                                                                                                                              
            if "%TYPE%" == "FATAL_ERROR" (
                    for %alarmNum in (1) do (beep %+ beep 145 1 %+ beep 120 1 %+ beep 100 1 %+ beep 80 1 %+ beep 65 1 %+ beep 50 1 %+ beep 40 1)
                    beep hand
             )        
        :No_Beeps_2

    REM Do delay:
        if %DO_DELAY gt 0 .and. 1 ne %SILENT_MESSAGE (delay %DO_DELAY)
    
REM Logging
        iff "%TYPE%" == "FATAL_ERROR" then
                if not defined   LOGS   set        logs=c:\logs
                if not isdir   "%LOGS%" mkdir /s "%LOGS%"
                set    log_file=%LOGS%\%TYPE%.log
                echo %_DATETIME:%DECORATED_MESSAGE% >>"%log_file%"
        endiff
    
REM For errors, give chance to gracefully exit the script (no more mashing of ctrl-C / ctrl-Break)
        set print_message_running=15
        rem echoerr type=%type%        
        iff "%TYPE%" == "FATAL_ERROR" .or. "%TYPE%" == "FATALERROR" .or. "%TYPE%" == "ERROR" then
                set DO_IT=
                set temp_title=%_wintitle
                call exit-maybe
                rem call askyn "Cancel all execution and return to command line?" yes
                rem rem yes, CANCELL with 2 L’s. Complex reasons for this:
                rem if %DO_IT eq 1 (
                rem         call CANCELLL.bat
                rem         title %temp_title%
                rem         goto :END
                rem )
        endiff

REM Hit user with the “pause” prompt several times, to prevent accidental passthrough from previous key mashing
        unset /q loop
        if %EXECUTE_PROTECTION_PAUSES gt 0 (set           loop=4 3 2 1 0)
        if %EXECUTE_PROTECTION_PAUSES gt 1 (set loop=9 8 7 6 5 4 3 2 1 0)
        if defined loop (for %pauseNum in (%loop%) do (echoserr    %pause% %ANSI_RESET%%blink_on%%ansi_red%%ansi_save_position%[%ansi_bright_red%%pauseNum%%ansi_red%]%blink_off% %@ANSI_RANDFG_SOFT[]%@ANSI_RANDBG_SOFT[]`` %+ echoserr Press any key when ready... %+ *pause /c >nul %+ echoerr %@ansi_move_left[3] %CHECK%%@ansi_move_up[1]%@ansi_move_left[31]%ansi_restore_positon%%@ansi_move_down[1]%ansi_reset%%ansi_color_green%%faint_on%[%pauseNum%]%ansi_reset%%@ansi_move_right[28]))


goto :END


goto :skip_subroutines
        :divider []
                rem Use my pre-rendered rainbow dividers, or if they don’t exist, just generate a divider dynamically
                set wd=%@EVAL[%_columns - 1]
                set nm=%bat%\dividers\rainbow-%wd%.txt
                iff exist %nm% then
                        *type %nm%
                        if "%1" != "NoNewline" .and. "%2" != "NoNewline" .and. "%3" != "NoNewline" .and. "%4" != "NoNewline" .and. "%5" != "NoNewline"  .and. "%6" != "NoNewline" (echos %NEWLINE%%@ANSI_MOVE_TO_COL[1])
                else
                        echo %@char[27][93m%@REPEAT[%@CHAR[9552],%wd%]%@char[27][0m
                endiff
        return
:skip_subroutines


::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        :DemoSuite
                cls
                echoerr.
                call fatal_error    "We’re DONE! There is NO HOPE! STOP!!!"
                call error          "Uh-oh! This might be broken!"
                call alarm          "Take notice! We need attention!"
                call warning        "This may do a bad thing!"
                call warning_less   "This may do a thing that maybe might be a little bad..."
                call removal        "temp files have been deleted"
                echoerr.
                call important      "narration of main tasks"
                call important_less "narration of subtasks"
                call unimportant    "not sure if we need to bother saying this anymore"
                call subtle         "pretty sure i don’t need to say this anymore"
                echoerr.
                call advice         "some good advice to take into consideration right now"
                call debug          "the value for %foo[1] is 4329.9342093 right now"
                echoerr.
                call completion     "subtask completed"
                call success        "main task successful"
                call celebration    "entire script is done, let’s have cake!"
                echoerr.
                call normal         "we don’t use this one"
                echoerr.
        goto :END

        :TestSuite
                call validate-in-path important 
                set  my_fast=%fast
                if   1  ne %myfast (repeat 3 echoerr.)
                cls
                echoerr.
                if 1 ne %my_fast (
                        echoerr %ANSI_COLOR_IMPORTANT%System print test - press N to go from one to the next --- any other key will cause tests to not complete -- if you get stuck hit enter once, then N -- if that doesn’t work hit enter twice, then N
                        echoerr.
                        pause>nul
                )

                rem      use %MESSAGE_TYPES instead of %MESSAGE_TYPES_WITHOUT_ALIASES to test alias message types:
                gosub divider
                for %%clr in (%MESSAGE_TYPES_WITHOUT_ALIASES%) (   
                        set clr4print=%clr%
                        if 1 ne %my_fast (
                                echoerr.
                                cls
                                echoerr %ANSI_COLOR_IMPORTANT%about to test %clr4print:
                                echoerr.
                                pause>nul
                                cls
                                call print-message %clr "This is a %clr4print message"
                                pause>nul
                        ) else (
                                rem pause
                                call print-message %clr "This is a %clr4print message"
                                gosub divider                   
                        )
                )
        goto :END


::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::



:None
:END


if defined PRINTMESSAGE_OPT_SUPPRESS_AUDIO (set PRINTMESSAGE_OPT_SUPPRESS_AUDIO=)

set print_message_running=999999999


echo %ANSI_RESET% >nul %+ rem reset the color if we are in echo-on mode

@rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ PRINT-MESSAGE.bat — END ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ PRINT-MESSAGE.bat — END ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━> nul
@rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ PRINT-MESSAGE.bat — END ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


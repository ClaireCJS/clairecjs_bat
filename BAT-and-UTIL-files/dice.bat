@Echo OFF

::::: USAGE:                             dice.bat <num_dice_sides> - roll a die with as many sides as the command-line parameter specifies
::::: USAGE:   set NUM_DICE_SIDES=xxx %+ dice.bat                  - roll a die with as many sides as the environment  variable  specifies
::::: USAGE:                             dice.bat [no arguments]   - interactively prompts for number of dice sides, with default value of 6

:REQUIRES: set-colors.bat (for ANSI_FG_RGB function, env vars for stylizing)


::::: GET NUMBER OF SIDES OF DIE:
    :SetUp_Number_Of_Dice_Sides_BEGIN
        if "%1" ne ""                 (set NUM_DICE_SIDES=%1 %+  goto :SetUp_Number_Of_Dice_Sides_END)
        if not defined NUM_DICE_SIDES (set NUM_DICE_SIDES=6  %+ %COLOR_INPUT% %+ echos * `` %+ eset NUM_DICE_SIDES %+ %COLOR_NORMAL%)
    :SetUp_Number_Of_Dice_Sides_END

::::: SET UP DIE ROLL:
    set MIN_DICE_VALUE=1
    set MAX_DICE_VALUE=%NUM_DICE_SIDES%
    %COLOR_SUBTLE% %+ echo. %+ echo %fant%%@ANSI_FG_RGB[48,48,48]* Rolling %underline%%NUM_DICE_SIDES%%underline_off%-sided die.%faint_off% %+ %COLOR_NORMAL%
    echo.

::::: ROLL THE DIE:
    if "%DEBUG%" ne "" (%COLOR_DEBUG% %+ echo set LAST_DICE_ROLL=%@RANDOM[%MIN_DICE_VALUE%,%MAX_DICE_VALUE%] %+ %COLOR_NORMAL%)
    set LAST_DICE_ROLL=%@RANDOM[%MIN_DICE_VALUE%,%MAX_DICE_VALUE%]

::::: CHECK DIE ROLL SUCCESS:
    call validate-environment-variable LAST_DICE_ROLL

::::: REPORT RESULTS: TEXT + BANNER + AUDIO:
    %COLOR_SUCCESS% %+ echo %EMOJI_GAME_DIE% %faint%%italics%Dice roll%italics_off% is%faint_off%: %blink%%LAST_DICE_ROLL%%blink_off% %EMOJI_GAME_DIE% %+ echo.
    call bigecho "%EMOJI_GAME_DIE% %BLINK%%@ANSI_FG_RGB[255,214,65]%double_underline%%LAST_DICE_ROLL%%double_underline_off%%BLINK_OFF% %EMOJI_GAME_DIE%"
    echo. 
    %COLOR_ALARM%   %+ say %LAST_DICE_ROLL%
    %COLOR_NORMAL%  %+ call audio-countdown-noise %@EVAL[MAX_DICE_VALUE - LAST_DICE_ROLL] %MAX_DICE_VALUE% 10

::::: CLEAN UP VARIABLES THAT CAN CAUSE FUTURE SIDE EFFECTS:
    unset /q NUM_DICE_SIDES

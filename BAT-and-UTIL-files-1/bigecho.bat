@Echo off
@on break cancel



:USAGE: bigecho "big message to echo i quotes"

:DESCRIPTION: Uses DEC VT100 ANSI codes to echo a line in double-height text


:DEPRECATED: optionally set COLOR_TO_USE=<command to set the color to use> prior to calling for cosmetically better background color handling to avoid the cosmetic weirdness of newlines with a different background color (likely no longer necessary after 20241015 changes)




rem ———————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————        

rem Get parameters:
        setdos /x-5
        set PARAMS=%@UNQUOTE[%*]
        set PARAMS2=%@UNQUOTE[%1$]
        rem DEBUG: echo    %%1$ is %1$
        rem DEBUG: echo params  is %params%
        rem DEBUG: echo params2 is %params2%
        setdos /x0


rem Validate environment
        if %BIGECHO_VALIDATED ne 1 (
            if not defined BIG_TEXT_LINE_1 (call error "BIG_TEXT_LINE_1 is not defined. Try running set-colors.bat")
            if not defined BIG_TEXT_LINE_2 (call error "BIG_TEXT_LINE_2 is not defined. Try running set-colors.bat")
            call validate-plugin StripANSI
            call validate-environment-variables BIG_TEXT_LINE_1 BIG_TEXT_LINE_2 BIG_TEXT_END ANSI_RESET ANSI_COLOR_NORMAL ANSI_ERASE_TO_EOL emphasis deemphasis blink_on blink_off
            set BIGECHO_VALIDATED=1
        )

rem ———————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————        

rem If it's too wide  then simply revert back to echo'ing the command in normal/single-height lines...
        setdos /x-5
        set            STRIPPED_MESSAGE=%@stripansi[%@UNQUOTE[%PARAMS]]
        rem LEN=%@width[%STRIPPED_MESSAGE%]
        set LEN=%@width["%STRIPPED_MESSAGE%"]
        setdos /x0
        SET MESSAGE_WIDTH_NORMAL=%LEN%
        SET MESSAGE_WIDTH_DOUBLE=%@EVAL[%LEN * 2] 
        rem because we're dealing with double-height text

rem Get the maximum desired width (in normal size, not double size):
        rem MAXIMUM_DESIRED_NORMAL_WIDTH=%@EVAL[%_COLUMNS-16] %+ rem fudge factor of 16 got past the windows terminal bug who's report i filed at https://github.com/microsoft/terminal/issues/18250
        set MAXIMUM_DESIRED_NORMAL_WIDTH=%@EVAL[%_COLUMNS]    %+ rem But then the bug got fixed!
        set MAXIMUM_DESIRED_NORMAL_WIDTH=%@EVAL[%_COLUMNS-20] %+ rem but then 2024/12/09 i noticed emoji screw this up because width vs length ... it turns out @LEN of an emoji is 2 so you can’t accurately place things .. set fudge factor to 4 but that wasn’t enough .. on 12/12/2024 set it to 20 ... even 10 was insufficient
        set MAXIMUM_DESIRED_NORMAL_WIDTH=%@EVAL[%_COLUMNS-10] %+ rem but then 2025/01/31 i realized some of that was print-message which does it internally and doesn’t handle the wrapping like here

rem Now do the special handling if the message it too long
        rem OLD: iff not %MESSAGE_WIDTH_DOUBLE% lt %MAXIMUM_DESIRED_NORMAL_WIDTH%   then
        rem OLD:         echo %STAR%%STAR%%STAR% %blink_on%%emphasis%%1$%deemphasis%%blink_off% %STAR%%STAR%%STAR% 
        rem OLD:         goto :END
        rem OLD: endiff                
        iff %MESSAGE_WIDTH_DOUBLE% gt %MAXIMUM_DESIRED_NORMAL_WIDTH%   then

                rem 🛑 🛑 🛑 🛑 🛑 🛑 We must break it up into lines! 🛑 🛑 🛑 🛑 🛑 🛑 
                rem 🛑 🛑 🛑 🛑 🛑 🛑 We must break it up into lines! 🛑 🛑 🛑 🛑 🛑 🛑 
                rem 🛑 🛑 🛑 🛑 🛑 🛑 We must break it up into lines! 🛑 🛑 🛑 🛑 🛑 🛑 

                REM Initialize the string to process
                        setdos /x-5
                        SET STR=%STRIPPED_MESSAGE%
                        setdos /x0
rem                     echo MESSAGE_WIDTH_DOUBLE = %MESSAGE_WIDTH_DOUBLE%
rem                     echo COLUMNS = %_COLUMNS 🐈
rem                     echo MAXIMUM_DESIRED_NORMAL_WIDTH = %MAXIMUM_DESIRED_NORMAL_WIDTH% 🐈

                REM Loop until the entire string has been processed
                :begin_loop
                        set  widthStr=%@width[%STR]
rem                     echo widthStr(1) is [%widthStr%] for %ansi_color_red%[%ansi_color_normal%%STR%%ansi_color_red%]%ansi_color_normal% 🐱 %+ pause
                        set  widthStr=%@EVAL[%@width["%STR"]-2]                    %+ rem Have to enclose it in quotes to not be vulnerable to text with “]” in it, and then subtract 2 for the quotes we added
rem                     echo widthStr(2) is [%widthStr%] for %ansi_color_red%[%ansi_color_normal%%STR%%ansi_color_red%]%ansi_color_normal% 🐱 %+ pause
                        set string_length_normal_size=%widthStr%
                        rem *2 because we're dealing with double-height text:
                        set string_length_double_size=%@EVAL[%widthStr% * 2]         
rem                     echo STRING_LENGTH_NORMAL_SIZE = %STRING_LENGTH_NORMAL_SIZE% 🐈
rem                     echo STRING_LENGTH_DOUBLE_SIZE = %STRING_LENGTH_DOUBLE_SIZE% 🐈
                        
                        if %string_length_normal_size% == 0 GOTO :done_with_too_long_messages
                        
rem                     iff %string_length_double_size% LE %MAXIMUM_DESIRED_NORMAL_WIDTH% then GOTO DONE WITH TOO LONG MESSAGES OTHERWISE STR LEN ACTUAL IS gt MAX DESIRED WIDTH
                        iff %string_length_double_size% LE %MAXIMUM_DESIRED_NORMAL_WIDTH% then
                                REM If the remaining string is shorter than desired, output normally by exiting this loop
                                        goto :done_with_too_long_messages
                        else
                                rem Else string length actual is GT maximum desired width:
                        endiff


                         REM How far over length are we? By actual/normal width subtracted by normal desired width
                         set OVERRUN_NORMAL_WIDTH=%@EVAL[%string_length_double_size - %MAXIMUM_DESIRED_NORMAL_WIDTH]
                         set OVERRUN_DOUBLE_WIDTH=%@FLOOR[%@EVAL[%OVERRUN_NORMAL_WIDTH / 2 + 0.9999999999]]
rem                     echo OVERRUN_NORMAL_WIDTH = %OVERRUN_NORMAL_WIDTH% 🐈
rem                     echo OVERRUN_DOUBLE_WIDTH = %OVERRUN_DOUBLE_WIDTH% 🐈
                                
                        REM To round up our number add almost-1 to it. I.E.: we really need to strip off 5, so 4.1 + 0.09999999999 = 5.09999999999 floored = 5.0  But 4.0 will remain 4
                                rem REMOVE_AMOUNT=%@EVAL[2 * %@FLOOR[%@EVAL[(%string_length% - %MAXIMUM_DESIRED_NORMAL_WIDTH% + 0.9999999999999999999999)]]] %+ rem double for double-width chars
                                rem OVE_AMOUNT_NORMAL=%OVERRUN_NORMAL_WIDTH%
                                rem REMOVE_AMOUNT_DOUBLE=%@FLOOR[%@EVAL[(%OVERRUN_NORMAL_WIDTH% * 2) + 0.9999999999]]
                                rem   KEEP_AMOUNT_NORMAL=%@EVAL[%MESSAGE_WIDTH_DOUBLE% - %OVERRUN_NORMAL_WIDTH% ]
                                rem   KEEP_AMOUNT_DOUBLE=%@EVAL[%MESSAGE_WIDTH_DOUBLE% - %REMOVE_AMOUNT_DOUBLE% ]
                                rem   KEEP_AMOUNT_DOUBLE=%@EVAL[%KEEP_AMOUNT_NORMAL% * 2]
                                rem REMOVE_AMOUNT_NORMAL=%@FLOOR[%@EVAL[(%REMOVE_AMOUNT_DOUBLE% / 2) + 0.999999999]]
                                rem   KEEP_AMOUNT_DOUBLE=%@EVAL[%KEEP_AMOUNT_NORMAL% * 2]
rem                            echo MESSAGE_WIDTH_NORMAL = %MESSAGE_WIDTH_NORMAL%
                                set REMOVE_AMOUNT_NORMAL=%OVERRUN_DOUBLE_WIDTH%
                                rem   KEEP_AMOUNT_NORMAL=%@EVAL[%MESSAGE_WIDTH_DOUBLE% - %REMOVE_AMOUNT_NORMAL% ]
                                set   KEEP_AMOUNT_NORMAL=%@EVAL[%MESSAGE_WIDTH_NORMAL% - %REMOVE_AMOUNT_NORMAL% ]
rem                            echo REMOVE_AMOUNT_NORMAL = %remove_amount_normal 🐈
                                rem REMOVE_AMOUNT_DOUBLE = %remove_amount_double isn’t a thing anymore
rem                            echo   KEEP_AMOUNT_NORMAL = %keep_amount_normal 🐈 [N/A]
                                rem   KEEP_AMOUNT_DOUBLE = %keep_amount_double   isn’t a thing anymore

                        
                        rem DEBUG: echo  string_length_double_size=%string_length_double_size% not LE MAXIMUM_DESIRED_NORMAL_WIDTH=%MAXIMUM_DESIRED_NORMAL_WIDTH% 
                        rem DEBUG: echo keep_amount_normal=%keep_amount_normal%

                        REM Actually set the line that we are going to echo
                                setdos /x-5
rem                        echo SET LINE=!@LEFT[%KEEP_AMOUNT_NORMAL%,%STR] 
                                rem LINE=%@LEFT[%KEEP_AMOUNT_NORMAL%,%STR] 
                                set left_amount=%@EVAL[%KEEP_AMOUNT_NORMAL%-1]
                                SET LINE=%@UNQUOTE[%@LEFT[%left_amount%,"%STR%"]]
rem                        echo 👈LEFT  (%left_amount%) is: %ansi_color_red%[%ansi_normal%%LINE%%ansi_color_red%]%ansi_normal% 🐈
                                setdos /x0

                        REM Then deal with *the rest* of what remains of this line:
                        REM Remove the first %Desired_Max_msg_width characters from left of STR
                        REM        via removing the precalculated-from-before remove_amount:
rem                            echo SET STR=!@RIGHT[%REMOVE_AMOUNT_NORMAL%,%STR] 🐈
rem                            echo STR 99999 is %ansi_color_red%[%ansi_normal%%STR%%ansi_color_red%]%ansi_normal% 🐱
                                rem STR=%@RIGHT[%REMOVE_AMOUNT_NORMAL%,%STR]                                        
                                rem right_amount=%@EVAL[%KEEP_AMOUNT_NORMAL%-1]
                                set right_amount=%@EVAL[%REMOVE_AMOUNT_NORMAL%+1]
                                SET STR=%@UNQUOTE[%@RIGHT[%right_amount%,"%STR%"]]
rem                            echo 👉RIGHT (%right_amount%) is %ansi_color_red%[%ansi_normal%%STR%%ansi_color_red%]%ansi_normal% 🐱
                        rem Set this value aside because STR will be redefined when we recursively call this                                        
                        rem And also remove any leading spaces off of it (at this point, length doesn't matter) :
                                SET  REMAINING_STR=%@TRIM[%STR%]
rem                             echo REMAINING_STR = %ansi_color_red%[%ansi_color_normal%%REMAINING_STR%%ansi_color_red%]%ansi_color_normal% 🐈

                        REM Spit out what we got, but assign it to a VERY unique variable name out of ridiculously [probably unnecessary] scope paranoia: 
                                set                UNIQUE_VAR_NAME=UNIQUE_VAR_NAME_%@RANDOM[0,999999999999999]
                                set              %[UNIQUE_VAR_NAME]="%@UNQUOTE[%LINE%]"
                                rem setdos /x-678
rem                             echo @call  bigecho %[%[UNIQUE_VAR_NAME]] ---------------------- %newline%
                                if "" !=  "%[%[UNIQUE_VAR_NAME]]" @call bigecho %[%[UNIQUE_VAR_NAME]]
                                rem setdos /x0
                                unset  /q        %[UNIQUE_VAR_NAME]
                                
                        REM Set STR for next message
                                set STR=%REMAINING_STR%
rem                             echo %ansi_color_red%remaining_str is '%REMAINING_STR%'%ansi_normal% ... setting for rest of script 🐈
                                set PARAMS=%STR%
                                
                goto :begin_loop
                :end_loop
        endiff          
        :done_with_too_long_messages

rem ———————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————        

setdos /x-678

    rem We will move to column 1, because switching to big text mid-column makes no sense!
    echos %@ANSI_MOVE_TO_COL[1]

    rem we use the ANSI_ERASE_TO_EOL sequence after setting the color to 'normal' to evade a Windows Terminal+TCC bug where the background color bleeds into the rightmost column
    rem %COLOR_TO_USE% %+  echo %BIG_TEXT_LINE_1%%PARAMS%%BIG_TEXT_END%%ANSI_COLOR_NORMAL%%ANSI_RESET%%ANSI_ERASE_TO_EOL%
    rem %COLOR_TO_USE% %+ echos %BIG_TEXT_LINE_2%%PARAMS%%BIG_TEXT_END%%ANSI_COLOR_NORMAL%%ANSI_RESET%%ANSI_ERASE_TO_EOL% %+ if %ECHOSBIG ne 1 (echo.)
    rem echos %BIG_TEXT_END%%ANSI_RESET%%ANSI_ERASE_TO_EOL%

    rem There was a lot of weirdness with background color bleedthrough:
    rem I opened this bug report with Windows Terminal to fix it: 
    rem https://github.com/microsoft/terminal/issues/17771
    rem But it turned out to not be a bug, and this is just what we have to do:

    if %ECHOSBIG_NEWLINE_AFTER eq 1 (
        set XX=2 
        echos %@ANSI_MOVE_DOWN[%xx]%@ANSI_MOVE_UP[%@EVAL[%xx-1]]%@ANSI_MOVE_TO_COL[1]
    )



    rem %COLR_TO_USE% %+ echos %BIG_TEXT_LINE_1%%PARAMS% %+ echos %BIG_TEXT_END%%ANSI_RESET%           %+ if %ECHOSBIG_SAVE_POS_AT_END_OF_TOP_LINE eq 1 (echos %ANSI_SAVE_POSITION%)  
    rem %COLOR_TO_USE% 

    rem echos %BIG_TEXT_LINE_1%%PARAMS%%ANSI_EOL%             
    rem deprecated if %ECHOSBIG_SAVE_POS_AT_END_OF_TOP_LINE eq 1 (echos %ANSI_SAVE_POSITION%)  
    REM echo.
    rem OR_TO_USE% %+ echos %BIG_TEXT_LINE_2%%PARAMS% %+ echos %BIG_TEXT_END%%ANSI_RESET%%ANSI_EOL% %+ if %ECHOSBIG_SAVE_POS_AT_END_OF_BOT_LINE eq 1 (echos %ANSI_SAVE_POSITION%)  
    rem %COLOR_TO_USE% 
    
    rem echos %BIG_TEXT_LINE_1%%PARAMS%%ANSI_EOL%%NEWLINE%%BIG_TEXT_LINE_2%%PARAMS%%BIG_TEXT_END%%ANSI_EOL%
    %COLOR_TO_USE% 
    
    rem Actually do it:
            setdos /x-5
            rem  didn't quite line up for some reason?!?: echo %BIG_TEXT_LINE_1%%PARAMS%%ANSI_EOL%
            rem  didn't quite line up for some reason?!?: echo %BIG_TEXT_LINE_2%%PARAMS%%BIG_TEXT_END%%ANSI_EOL%
            echo %BIG_TEXT_LINE_1%%PARAMS%%ANSI_ERASE_TO_EOL%
            echo %BIG_TEXT_LINE_2%%PARAMS%%ANSI_ERASE_TO_EOL%
            setdos /x0
    rem also seems to work fine:n
            rem echo %BIG_TEXT_LINE_1%%PARAMS%%BIG_TEXT_END%
            rem echo %BIG_TEXT_LINE_2%%PARAMS%%BIG_TEXT_END%
    rem also seems to work fine:
            rem echo %BIG_TEXT_LINE_1%%PARAMS%
            rem echo %BIG_TEXT_LINE_2%%PARAMS%
   
    rem deprecated: 
            rem if %ECHOSBIG_SAVE_POS_AT_END_OF_BOT_LINE eq 1 (echos %ANSI_SAVE_POSITION%)  
            rem echo.

    echos %ANSI_RESET%
    if %ECHOSBIG ne 1 (echo.)

    echos %@ANSI_MOVE_UP[2]
    echo.
    if %ECHOSBIG_NEWLINE_AFTER eq 1 (echo. %+ echo.)

rem ———————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————        

:END
    setdos /x0

    REM This option should only affect it once, and thus needs to self-delete:
            if defined COLOR_TO_USE (set COLOR_TO_USE=)

rem ———————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————        

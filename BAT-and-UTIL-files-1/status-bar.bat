@loadbtm on
@echo off
@rem MANUALLY save cursor position because the ansi_save_position / restore_position is not sufficient
@set PRE_ROW=%_row
@set PRE_COL=%_column
@rem echos [set pre_row/col to:%pre_row%,%pre_col%]
@if "%1" == "unlock" goto :do_the_unlock
@set DISABLE_STATUS_BAR=0
@rem echo %ansi_color_orange%@if "%temporarily_disable_status_bar%" == "1" set DISABLE_STATUS_BAR=1 
@if "%temporarily_disable_status_bar%" == "1" set DISABLE_STATUS_BAR=1 
@if "1" == "%DISABLE_STATUS_BAR%" goto :The_Very_End
@on break cancel


goto :skip_stuff_1

:DESCRIPTION: Locks a non-scrollable banner message at the top 3 rows of our console menu. Good for keeping track of tasks, percentage complete, etc.

:USAGE: status-bar unlock               - unlock any previously set top banner
:USAGE: status-bar unlock no_erase      - unlock any previously set top banner WITHOUT erasing it                                        
:USAGE: status-bar {no arguments}       - banner message is a report of free space on the current drive
:USAGE: status-bar  C:                  - banner message is a report of free space on the given drive letter
:USAGE: status-bar "Hello precious!"    - banner message is a custom message saying whatever we want
:USAGE: status-bar "Hi! {freespace}"    - banner message is a custom message that includes our report of free space on the current drive
:USAGE: status-bar "Hi! {freespace}" S: - banner message is a custom message that includes our report of free space on the given drive letter
:USAGE: set header_noecho=1              - to not echo it to screen in addition to drawing the header 

:skip_stuff_1

rem Capture parameters:
        unset /q        TB_PARAM_1
        unset /q        TB_PARAM_2
        unset /q           PARAMS
        unset /q  ORIGINAL_PARAMS
        unset /q  status_bar_goto_END
        set             TB_PARAM_1=%1
        set             TB_PARAM_2=%2
        set                PARAMS=%*
        set       ORIGINAL_PARAMS=%*


rem ENVIRONMENT: Validate the environment:
        if "1" != "%VALIDATED_LOCKED_MESSAGE%" (
                call validate-environment-variables PLUGIN_STRIPANSI_LOADED ANSI_UNLOCK_MARGINS ANSI_SAVE_POSITION ANSI_RESTORE_POSITION ANSI_EOL NEWLINE CONNECTING_EQUALS BLINK_ON BLINK_OFF DOT ANSI_COLOR_ERROR ANSI_UNLOCK_MARGINS connecting_equals
                call validate-functions             ANSI_MOVE_UP   ANSI_BG  ANSI_UNLOCK_ROWS    ANSI_SCROLL_DOWN   ANSI_MOVE_DOWN        ANSI_MOVE_TO_ROW
                call validate-plugin                StripANSI
                set VALIDATED_LOCKED_MESSAGE=1
        )




rem CONFIG: Set message background color & divider:
        rem the height of our default status bars:
                set DEFAULT_ROWS_TO_LOCK=3      
        rem if this is changed, need to change hard-coding in create-srt--from-file.bat
                set LOCKED_MESSAGE_COLOR_BG=%@ANSI_BG[0,0,64] 
        rem other stuff:
                set LOCKED_MESSAGE_COLOR=%ANSI_COLOR_IMPORTANT%%LOCKED_MESSAGE_COLOR_BG%
                set DOTTIE=%BLINK_ON%%DOT%%BLINK_OFF%
                set ROWS_TO_LOCK=%DEFAULT_ROWS_TO_LOCK%




rem Respond to command-line parameters:
        echos %@ANSI_BG[0,0,0]%ANSI_RESET%>nul
        unset /q LOCKED_MESSAGE
        rem Unlock mode:
                :do_the_unlock
                if "%TB_PARAM_1" == "unlock" .or. "%1" == "unlock" .or. "1" == "%DISABLE_STATUS_BAR%" goto :lock_yes
                                                                                                      goto :respond_no
                        :lock_yes
                                if "1" != "%STATUSBAR_LOCKED%" .and. "%2" != "force" goto :END
                                echos %big_off%%@ANSI_UNLOCK_ROWS[]
                                set STATUSBAR_LOCKED=0
                                if "%TB_PARAM_2" != "no_erase" .and. "1" != "%DISABLE_STATUS_BAR%"  goto :do_it_80
                                                                                                    goto :endif_88
                                        :do_it_80
                                                set NN=%ROWS_TO_LOCK%
                                                if defined LAST_ROWS_TO_LOCK set NN=%LAST_ROWS_TO_LOCK%
                                                echo %ansi_save_position%%@CHAR[27][%@EVAL[%_rows - %NN% + 1]H%big_off%%ansi_reset%%ansi_erase_to_eol%
                                                echos %big_off%%ansi_erase_to_eol%%ansi_erase_to_end_of_screen%
                                                set repeats=%@EVAL[%nn - %DEFAULT_ROWS_TO_LOCK%]
                                                if %repeats% gt 0 repeat %repeats% echos %big_off%%ansi_erase_to_eol%
                                                echos %big_off%%ansi_erase_to_eol%%ansi_restore_position%%big_off%
                                                iff %_ROW gt %@EVAL[%_rows - %DEFAULT_ROWS_TO_LOCK%] then
                                                        set repeat_num=%@EVAL[%_row - (%_rows - %DEFAULT_ROWS_TO_LOCK%)]
                                                        repeat %repeat_num% echos %ansi_move_up_1%
                                                endiff
                                :endif_88
                                set status_bar_goto_END=1
                                set STATUSBAR_LOCKED=0
                        :endif:
                :respond_no

                if "1" == "%status_bar_goto_END%" goto :END


rem Set free space stuffs:
        set CWDTMP=%_CWD
        set CUSTOM_MESSAGE=0
        set FREE_SPACE_MESSAGE_IS_USED=0
        set USE_JUST_FREE_SPACE_MESSAGE=0
        iff "%TB_PARAM_1%" == "" then
                set USE_JUST_FREE_SPACE_MESSAGE=1
        else
                set LOCKED_MESSAGE=%@UNQUOTE[%TB_PARAM_1]
                set CUSTOM_MESSAGE=1
                rem  %@LEN[%TB_PARAM_1]  eq  2  .and. "%@INSTR[1,1,%TB_PARAM_1]"    eq ":" then
                iff "%@LEN[%TB_PARAM_1]" == "2" .and. "%@INSTR[2,1,"%TB_PARAM_1%"]" == ":" then
                        set CWDTMP=%TB_PARAM_1 
                        set USE_JUST_FREE_SPACE_MESSAGE=1
                        set FREE_SPACE_MESSAGE_IS_USED=1
                        iff "0" == "%@READY[%TB_PARAM_1]" then
                                set LOCKED_MESSAGE=%ANSI_COLOR_ERROR%Drive %TB_PARAM_1: is not ready 
                                goto :Display_Message_Now
                        endiff
                endiff
                rem  %@LEN[%TB_PARAM_2]     eq  2  .and. "%@INSTR[1,1,%TB_PARAM_2]"   eq ":" then
                iff "%@LEN["%TB_PARAM_2%"]" == "4" .and. "%@INSTR[2,1,"%TB_PARAM_2"]" == ":" then
                        set CWDTMP=%TB_PARAM_2 
                        set USE_JUST_FREE_SPACE_MESSAGE=0 %+ rem This is tricky, but it should actually be 0 because if PARAM_2 is a drive letter, we're using a custom message
                        set FREE_SPACE_MESSAGE_IS_USED=1
                        iff "0" == "%@READY[%TB_PARAM_2]" then
                                set LOCKED_MESSAGE=%ANSI_COLOR_ERROR%Drive %TB_PARAM_2: is not ready 
                                goto :Display_Message_Now
                        endiff
                endiff
        endiff


rem Calculate free space values:
        set DF=%@DISKFREE[%CWDTMP]
        set FREE_MEGS=%@COMMA[%@FLOOR[%@EVAL[%DF%/1024/1024]]]
        set FREE_GIGS=%@COMMA[%@FORMATN[.2,%@EVAL[%DF%/1024/1024/1024]]]
        set FREE_TERA=%@FORMATN[.2,%@EVAL[%DF%/1024/1024/1024/1024]]

rem Create message text:
        set OUR_SLASH=%bold_on%%slash%%bold_off%
        SET FREE_SPACE_MESSAGE=%bold_on%%FREE_MEGS%%bold_off% %ansi_color_important_less%%LOCKED_MESSAGE_COLOR_BG%M %our_slash% %locked_message_color%%FREE_GIGS% %ansi_color_important_less%%LOCKED_MESSAGE_COLOR_BG%G
        if %FREE_GIGS gt 1000 (set FREE_SPACE_MESSAGE=%FREE_SPACE_MESSAGE%%locked_message_color% %our_slash% %FREE_tera% %ansi_color_important_less%%LOCKED_MESSAGE_COLOR_BG%T)
        set FREE_SPACE_MESSAGE=%FREE_SPACE_MESSAGE% %italics_on%free%italics_off% on %bold_on%%@UPPER[%@INSTR[0,2,%CWDTMP]]%bold_off%%LOCKED_MESSAGE_COLOR%
        if %USE_JUST_FREE_SPACE_MESSAGE eq 1 ( set LOCKED_MESSAGE=%FREE_SPACE_MESSAGE% )

rem Substitute the token {freespace} with our generated free space message:
        set LOCKED_MESSAGE=%@unquote[%@rereplace[{freespace},"%FREE_SPACE_MESSAGE%","%locked_message"]]
        set LAST_LOCKED_MESSAGE=%LOCKED_MESSAGE%



rem Get message length and create side-spacers of appropriate length to center the message:
        :Display_Message_Now
        set DECORATED_MESSAGE=%dottie% %LOCKED_MESSAGE%%LOCKED_MESSAGE_COLOR% %dottie%
        set LAST_DECORATED_MESSAGE=%DECORATED_MESSAGE%
                                                 SET LOCKED_MESSAGE_LENGTH=%@LEN[%@STRIPANSI[%DECORATED_MESSAGE]]
        if "%FREE_SPACE_MESSAGE_IS_USED" == "1" (SET LOCKED_MESSAGE_LENGTH=%@EVAL[%LOCKED_MESSAGE_LENGTH+2])         
        rem ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ the slash emojis we use twice in our free space message are not correctly measured by %@LEN[] which creates a bug of wrapping the line onto the next line, unless we manually deduct the number of wide emojis {or at least, the # of wide emojis that %@LEN isn't correctly counting!} ... May take some experimentation if you change the free message format
        set NUM_SPACER=%@FLOOR[%@EVAL[(%_COLUMNS-%LOCKED_MESSAGE_LENGTH)/2]]
        if %@EVAL[%num_spacer + %locked_message_length + %num_spacer] ge %@EVAL[%_columns-1] (set num_spacer=%@EVAL[%num_spacer - 1])
        :Spacer_Calc
        if %NUM_SPACER lt 0 (
            set NUM_SPACER_ORIG=%NUM_SPACER%
            set NUM_SPACER=%@FLOOR[%@EVAL[(%NUM_SPACER  +  %_columns)/2]]
            set NUM_SPACER=%@FLOOR[%@EVAL[(((%_columns-1)*2) - %locked_message_length) / 2]]
        )
        if %NUM_SPACER lt 0 (set NUM_SPACER=%@EVAL[-1 * %NUM_SPACER])
        set SPACER=%@REPEAT[ ,%NUM_SPACER]``


rem Was this multiline?
        set MULTILINE=0
        iff %@EVAL[%_columns mod ((%num_spacer*2) + %locked_message_length)] ge %_columns then
                set MULTILINE=1
                set ROWS_TO_LOCK=%@EVAL[%ROWS_TO_LOCK + 1]
                iff %@EVAL[%locked_message_length+2] gt %@EVAL[%_COLUMNS*2] then
                        set ROWS_TO_LOCK=%@EVAL[%ROWS_TO_LOCK + 1]
                endiff
                set SPACER=%@REPEAT[ ,%@EVAL[%NUM_SPACER]]``
        endiff


rem Make cursor invisible:
        if defined ANSI_CURSOR_INVISIBLE echos %ANSI_CURSOR_INVISIBLE%
        goto :skip_rems_1
        

rem Start with our status bar:
        rem The problem with locking rows at the bottom of the screen is
        rem that we lock our cursor INTO the locked area accidentally.     
        rem
        rem One way to deal with this is to clear the screen first, but we don’t 
        rem want to have to pay such a steep toll just to create a status bar.  
        rem
        rem Instead, it was found through experimentation that for a 3 row status bar, 
        rem sending the ansi_move_up code 4 times (num_locked_rows + 1) would ensure
        rem that the cursor is high enough to not get caught within the locked area.
        rem
        rem However, this introduces another problem: Moving up 4 lines means overwriting
        rem whatever was up there prior.  
        rem
        rem So, to eliminate THAT, we echo 4 blank lines before moving up 4 lines.               vv---- but now we’re trying 5 instead of 4       
        :skip_rems_1

        set row=%_ROW
        set rows=%_ROWS

                                                       set ROLL_NEEDED=0
        if %row% gt %@EVAL[%rows% - %rows_to_lock% -1] set ROLL_NEEDED=1

        rem echo roll_decision_row=row "%ROW%" out of "%ROWS%" rows %+ pause
        title row %ROW of %ROWS rows
        rem But perhaps we don’t need to do this block if it’s already locked: ... 
        rem Or if our current row is a bit higher
                iff "0"=="%STATUSBAR_LOCKED%" .and. "1"=="%ROLL_NEEDED%" then
                        set                    adjustment_value=%@EVAL[%rows_to_lock+1   +1]
                        set                    adjustment_value=%@EVAL[%rows_to_lock]
                        set                    adjustment_value=%@EVAL[%rows_to_lock+1]
                        set                    adjustment_value=%@EVAL[%rows_to_lock+1   +1] %+ rem goddamnit
                        REM repeat             %adjustment_value% echo.
                        rem echos %@ansi_MOVE_DOWN[%adjustment_value%]   ━━━
                        REM echos %@ansi_scroll_DOWN[%adjustment_value%] ━━━
                        echos %@ansi_SCROLL_DOWN[%adjustment_value%]
                        echos %@ANSI_MOVE_UP[%adjustment_value%]%ANSI_SAVE_POSITION%%@CHAR[27][r
                else
                        rem maybe not echos %ANSI_SAVE_POSITION%
                endiff

        rem Move to row n where n=last row on the screen minus how much space we need to display our message:
        echos %@ANSI_MOVE_TO_ROW[%@EVAL[%_rows-%rows_to_lock+1]]

        if 1 ne %STATUSBAR_LOCKED ( echos %LOCKED_MESSAGE_COLOR% %+ call divider %_columns NoNewline )
               echos %@ANSI_MOVE_TO_COL[1]%ansi_color_normal%               
               rem 20250221 not sure if 1 ne %STATUSBAR_LOCKED ( 
               rem 20250221 not sure          echos %LOCKED_MESSAGE_COLOR%  
               rem 20250221 not sure          call divider NoNewline lmc
               rem 20250221 not sure          echos %@char[27][%[_COLUMNS]G%locked_message_color%%@CHAR[27][38;2;255;0;5m%connecting_equals%        
               rem 20250221 not sure )

rem Actually lock the screen area:
        echos %@CHAR[27][1;%@EVAL[%_rows-%rows_to_lock%]r%ANSI_RESTORE_POSITION%
        set STATUSBAR_LOCKED=1


rem At this point we have our 1ˢᵗ divider and are at the 2ⁿᵈ line which is the line of our message
rem     echos %ANSI_SAVE_POSITION%%@ANSI_MOVE_TO[%@EVAL[%_ROWS-1],0]%LOCKED_MESSAGE_COLOR%%DIVIDER%
        echos %ANSI_SAVE_POSITION%%@ANSI_MOVE_TO[%@EVAL[%_ROWS-1],0]%LOCKED_MESSAGE_COLOR%

        rem Line 2: The actual message itself
        rem echos %LOCKED_MESSAGE_COLOR%%SPACER%%DECORATED_MESSAGE%%ANSI_EOL%%NEWLINE%
        echo %LOCKED_MESSAGE_COLOR%%SPACER%%DECORATED_MESSAGE%%ANSI_EOL%    

rem At this point, the message is displayed and we’re on the 3ʳᵈ/final line     
        gosub dividerWithStatusBarKludge NoNewLine
  
        rem                               echos %LOCKED_MESSAGE_COLOR%%DIVIDER%
        rem   %@ANSI_MOVE_TO[%@EVAL[%_ROWS-1],0]%LOCKED_MESSAGE_COLOR%%DIVIDER%
rem        echos %@ANSI_MOVE_TO[%@EVAL[%_ROWS-1],0]%LOCKED_MESSAGE_COLOR%
        echos %ANSI_RESTORE_POSITION%

goto :END

        
rem Echo the status bar message (aka “header”——but I hate that name) to the console as well:
        rem (don’t want to use if() because stuff in ( ) doesn’t display unicode correctly in TCC pre-v34):
        if "1" == "%header_noecho%" goto :skip_echo
                echo.  
                echo %ANSI_COLOR_IMPORTANT%%LOCKED_MESSAGE_COLOR_BG% %DOTTIE% %LOCKED_MESSAGE% %DOTTIE% %ansi_reset% 
        :skip_echo


rem END by restoring the cursor and saving the # of rows we unlocked to the environment for auditing/analysis:
        :END
        if defined ANSI_CURSOR_VISIBLE echos %ANSI_CURSOR_VISIBLE%
        set LAST_ROWS_TO_LOCK=%ROWS_TO_LOCK%


goto :skip_subroutines
        :dividerOLD []
                rem Use my pre-rendered rainbow dividers, or if they don’t exist, just generate a divider dynamically
                set wd=%@EVAL[%_columns - 1]
                set wd=%@EVAL[%_columns - 0]
                set nm=%bat%\dividers\rainbow-%wd%.txt
                if exist %nm% (
                echos %@ANSI_MOVE_TO_COL[0]%@CHAR[8]
                        *type %nm%
                        if "%1" ne "NoNewline" .and. "%2" ne "NoNewline" .and. "%3" ne "NoNewline" .and. "%4" ne "NoNewline" .and. "%5" ne "NoNewline"  .and. "%6" ne "NoNewline" (echos %NEWLINE%%@ANSI_MOVE_TO_COL[1])
                ) else (
                        echo %@char[27][93m%@REPEAT[%@CHAR[9552],%wd%]%@char[27][0m
                )
        return

        :dividerWithStatusBarKludge [divider_param]
                iff "1" == "%suppress_next_divider%" then
                        set  suppress_next_divider=0
                        return
                endiff
                set wd=%@EVAL[%_columns - 1] %+ rem results in 1 too few char
                set wd=%@EVAL[%_columns - 0] %+ rem results in 1 too few char but offset 1 to the right! yuck!
                set nm=%bat%\dividers\rainbow-%wd%.txt
                iff exist %nm% then
                                
                        *type %nm%

                        rem this kludge is only specific to status-bar because of the coloring, which we could make a parameter:
                        echo %@ANSI_MOVE_TO_COL[0]%LOCKED_MESSAGE_COLOR%%@ANSI_RGB[255,0,0]%connecting_equals%


                        set last_divider_method=type
                        set last_divider_param=%divider_param%
                else
                        echo %@char[27][93m%@REPEAT[%@CHAR[9552],%wd%]%@char[27][0m
                        set last_divider_method=echo
                endiff
                iff "%divider_param%" == "NoNewline"  then
                        set last_divider_newline=False
                else 
                        set last_divider_newline=True
                        rem we COULD do the newline character, but it’s easier to just do a few spaces so that we end up on the new line anyway:
                        rem echos %NEWLINE%%@ANSI_MOVE_TO_COL[1] 
                        echos     %@ANSI_MOVE_TO_COL[1] 
                endiff
                rem echo last_divider_newline=%last_divider_newline% should we do one?
        return


:skip_subroutines


:The_Very_End

        :cleanup
                rem A cleanup we need to do to prevent getting our cursor stuck in the locked area!
                        iff "1" == "%STATUSBAR_LOCKED%" then
                                rem check if we need to move any rows up but As of 2025/03/16 we still get trapped:
                                        set need_to_move_up=%@EVAL[-1*(%_ROWS - %_ROW - %rows_to_lock%)]
                                        rem 15 on 25 =-1*(15-25)= -1*(-10)= move up -10=  stay  on row 15 because negatives are ignored
                                        rem 21 on 25 = -1*(4-3) = -1*( 1) = move up -1 =  stay  on row 22 because negatives are ignored
                                        rem 22 on 25 = -1*(3-3) = -1*( 0) = move up  0 =  stay  on row 22
                                        rem 23 on 25 = -1*(2-3) = -1*(-1) = move up  1 = arrive at row 22
                                        rem 24 on 25 = -1*(1-3) = -1*(-2) = move up  2 = arrive at row 22
                                        rem 25 on 25 = -1*(0-3) = -1*(-3) = move up  3 = arrive at row 22
                        

                                rem So let’s try kludging an additional row out of it. Maybe there are situations where a newline or other output deposits us in the wrong place without the console fully knowing?
                                        set need_to_move_up=%@EVAL[1 + %need_to_move_up%]


                                rem ONLY If we ended up with a positive number, move those many rows up:
                                        if %need_to_move_up% gt 0 echos %@ANSI_MOVE_UP[%need_to_move_up%]
                                        set audit_row_when_moved_up_after_unlocking_status_bar=%_ROW
                                        set audit_col_when_moved_up_after_unlocking_status_bar=%_COL

                                rem TODO: We could just hard-move to the last available row without these calculations. 
                        endiff



rem MANUALLY restore cursor position because the ansi_save_position / restore_position is not sufficient
        echos %@ANSI_MOVE_TO[%@EVAL[%pre_row%+1],%pre_col%]
        set audit_row_when_done_setting_status_bar=%_ROW
        set audit_col_when_done_setting_status_bar=%_COL

rem 2025/03/16: new method for not getting trapped at the bottom....
        set max_valid_row_to_be_at=%@EVAL[%_ROWS - %ROWS_TO_LOCK]
        if %_ROW gt %max_valid_row_to_be_at echos %@ANSI_MOVE_TO_ROW[%max_valid_row_to_be_at]



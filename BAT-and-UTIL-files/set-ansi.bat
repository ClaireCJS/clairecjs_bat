@Echo Off



:——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————

:USED-BY:     this is run each time our command-line is launched, via environm.btm, which is called from TCStart.bat, which is automatically run each time a TCC command-line window/tab/pane is openened
:DESCRIPTION: Creates a set of environment variables that can be used for messaging improvement
:USAGE:       call set-ansi                  - standard invocation
:USAGE:       call set-ansi   force          - run it again, even if it's already been run (subsequent runs do nothing otherwise)
:USAGE:       call set-ansi   test           - to see the ANSI codes in action
:USAGE:       call set-ansi   stripansitest  - to test our %@STRIPANSI function, loaded from StripAnsi.dll
:EFFECTS:     sets      %COLOR_{messagetype} variables —— of TCC  commands —— for all the message types we intend to have
:EFFECTS:     sets %ANSI_COLOR_{messagetype} variables —— of ANSI env-vars —— for all the message types we intend to have
:EFFECTS:     sets %COLOR_{messagetype}_HEX  variables —— of rgb hex codes —— for all the message types that we have so far used in situations that require hex versions of their color code, particularly custom cursor colors
:REQUIRES:    bigecho.bat (optional, only for testing)
:RELATED:     redefine-the-color-black-randomly.bat (gives each command-line window a slightly different shade of black to make window edges easier to see)
:——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————



rem ———————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————

rem Branch by parameter:
        if "%1" == "force" .or. "%1" == "test" (goto :Force        )
        if "%1" == "stripansitest"             (goto :StripAnsiTest)
        if  "1" == "%COLORS_HAVE_BEEN_SET%"    (goto :AlreadyDone  )
        :Force

rem ————————————————————————————————————————————— BASE ANSI CODES: ————————————————————————————————————————————————————————————————————————————————————————

rem echo setting ansi! %pentagram% %+ pause


rem ANSI: Base variables used in other variables: 
        set                  ESCAPE=%@CHAR[27]
        set             ANSI_ESCAPE=%ESCAPE%[
        set ANSIESCAPE=%ANSI_ESCAPE%

rem ANSI: esoterica to bve used in next section
        set  ANSI_APP_PROGRAM_COMMAND=%ESCAPE%_         %+ rem APC == Application Program    Command
        set  ANSI_DEVICE_CONTROL_STRING=%ESCAPE%P       %+ rem DCS == Device      Control    String
        set  ANSI_OPERATING_SYSTEM_COMMAND=%ESCAPE%]    %+ rem OSC == Operating   System     Command
        set  ANSI_PRIVACY_MESSAGE=%ESCAPE%%@CHAR[94]    %+ rem  PM == Privacy     Message    
        set  ANSI_START_OF_STRING=%ESCAPE%X             %+ rem SOS == Start       Of         String 
        set  ANSI_STRING_TERMINATOR=%ESCAPE%\           %+ rem  ST == String      Terminator

rem ANSI: Names influenced by online references:
        set  ANSI_APC=%ANSI_APP_PROGRAM_COMMAND%        %+ rem APC == Application Program    Command
        set  ANSI_CSI=%ANSI_ESCAPE%                     %+ rem CSI == Control     Sequence   Introducer       
        set  ANSI_DCS=%ANSI_DEVICE_CONTROL_STRING%      %+ rem DCS == Device      Control    String
        set  ANSI_OSC=%ANSI_OPERATING_SYSTEM_COMMAND%   %+ rem OSC == Operating   System     Command
        set  ANSI_PM=%ANSI_PRIVACY_MESSAGE%             %+ rem  PM == Privacy     Message    
        set  ANSI_SOS=%ANSI_START_OF_STRING%            %+ rem SOS == Start       Of         String 
        set  ANSI_ST=%ANSI_STRING_TERMINATOR%           %+ rem  ST == String      Terminator

rem ————————————————————————————————————————————— UTILITY FUNCTIONS: ——————————————————————————————————————————————————————————————————————————————————————

rem Utility functions: 

        rem Returns a random single hex character, i.e. '0', '1', ..., '8', '9', 'A', 'B', ..., 'E', 'F':
                function random_hex_char=`%@substr[0123456789ABCDEF,%@random[0,15],1]`             

        rem Return a random hex rgb i.e. '47A98F', '9D3B5C':
                function random_rgb_hex=`%@random_hex_char[]%@random_hex_char[]%@random_hex_char[]%@random_hex_char[]%@random_hex_char[]%@random_hex_char[]`
        
        rem Return a string with character in a random color:
                function random_color_string=`%@REReplace[(.),%%@randFG_soFt[]\1,%1$]`
                function     colorful_string=`%@REReplace[(.),%%@randFG_soFt[]\1,%1$]`
                function            colorful=`%@REReplace[(.),%%@randFG_soFt[]\1,%1$]`

        rem Change a single digit into the cool version of digits (unicode) that we found, i.e. changing a single character from '1' to '𝟙' bracket cool_x are defined in emoji.inv】: 
                function  cool_digit_plain=`%[cool_%1]`                                           %+ rem COOL_0 through COOL_9 are defined in emoji.env      
                function  cool_char_plain=`%@if[%1==" ",%@if[defined cool_%1,%[cool_%1],%1]`      %+ rem ...but let's allow ANY character to have a 'cool' version in emoji.env, though it's questionable how useful this is with environment variable naming limitations
                rem Now do it in a random color also:
                        function       cool_digit=`%@randfg_soft[]%[cool_%1]`
                        function  cool_char_plain=`%@randfg_soft[]%@if[defined cool_%1,%[cool_%1],%1]`              

        rem Change a full number into the cool version of each digit:
                function cool_number_plain=`%@REPLACE[0,%@cool_digit_plain[0],%@REPLACE[9,%@cool_digit_plain[9],%@REPLACE[8,%@cool_digit_plain[8],%@REPLACE[7,%@cool_digit_plain[7],%@REPLACE[6,%@cool_digit_plain[6],%@REPLACE[5,%@cool_digit_plain[5],%@REPLACE[4,%@cool_digit_plain[4],%@REPLACE[3,%@cool_digit_plain[3],%@REPLACE[2,%@cool_digit_plain[2],%@REPLACE[1,%@cool_digit_plain[1],%1$]]]]]]]]]]`
                rem Now do it in a random color also:
                        function cool_number=`%@random_color_string[%@cool_number_plain[%1$]]`

        rem To coolify a non-numerical string, we simply run the same code —— but maybe we could do something else to make it interesting❓
                        function cool_string_plain=`%@REReplace[\!,%EMOJI_RED_EXCLAMATION_MARK%,%@REREPLACE[\?,%EMOJI_RED_QUESTION_MARK%,%@REPLACE[S,Ṡ,%@REPLACE[f,ƒ,%@REREPLACE[\?\!,%emoji_exclamation_question_mark%,%@cool_number_plain[%1$]]]]]]`
                        function cool_string=`%@random_color_string[%@cool_string_plain[%1$]]`
                        rem Alias:
                                function cool=`%@cool_string[%1$]`
                        rem Experimental:
                                function cool_string_lookup_only=`%@REReplace[([^\s]),%@randFG_soFt[]%@cool_char_plain[\1],%1$]` %+ rem EXPERIMENTAL

rem ————————————————————————————————————————————— RESETTING: ——————————————————————————————————————————————————————————————————————————————————————————————

rem ANSI: special stuff: reset
            set ANSI_RESET_FG_COLOR=%ANSI_ESCAPE%0m
            set ANSI_RESET=%ANSI_ESCAPE%39m%ANSI_ESCAPE%49m%ANSI_RESET_FG_COLOR% %+ REM need to add %ESCAPE%(B to the end of this —— that is, "esc(B" —— in case we are stuck in drawing mode. However, the 2023 version of @STRIPANSI (loaded from a DLL, not modifiable) doesn't properly strip the esc(b which creates some cosmetic problems for me, so I won't put it in 
                set ANSI_RESET_FULL=%ANSI_RESET%
                set ANSI_FULL_RESET=%ANSI_RESET%
                set ANSI_COLOR_RESET=%ANSI_RESET_FG_COLOR%
                set ANSI_RESET_COLOR=%ANSI_RESET_FG_COLOR%
                set ANSI_NORMAL=%ANSI_RESET%
                set ANSI_COLOR_NORMAL=%ANSI_RESET%

rem ————————————————————————————————————————————— CURSOR CUSTOMIZATION: ———————————————————————————————————————————————————————————————————————————————————


 rem ANSI: cursor visibility
        rem Cursor visibility:
                set ANSI_CURSOR_HIDE=%ANSI_ESCAPE%?25l                          %+ rem hides the cursor
                    set ANSI_HIDE_CURSOR=%ANSI_CURSOR_HIDE%                     %+ rem alias
                    set ANSI_INVISIBLE_CURSOR=%ANSI_CURSOR_HIDE%                %+ rem alias
                    set ANSI_CURSOR_INVISIBLE=%ANSI_CURSOR_HIDE%                %+ rem alias
                set ANSI_CURSOR_SHOW=%ANSI_ESCAPE%?25h                          %+ rem shows the cursor
                    set ANSI_SHOW_CURSOR=%ANSI_CURSOR_SHOW%                     %+ rem alias
                    set ANSI_VISIBLE_CURSOR=%ANSI_CURSOR_SHOW%                  %+ rem alias
                    set ANSI_CURSOR_VISIBLE=%ANSI_CURSOR_SHOW%                  %+ rem alias

        rem Cursor shape:
                rem Possible allowable shapes:
                        set ANSI_CURSOR_CHANGE_TO_DEFAULT=%ansi_escape%0 q
                        set ANSI_CURSOR_CHANGE_TO_BLOCK_BLINKING=%ansi_escape%1 q
                        set ANSI_CURSOR_CHANGE_TO_BLOCK_STEADY=%ansi_escape%2 q
                        set ANSI_CURSOR_CHANGE_TO_UNDERLINE_BLINKING=%ansi_escape%3 q
                        set ANSI_CURSOR_CHANGE_TO_UNDERLINE_STEADY=%ansi_escape%4 q
                        set ANSI_CURSOR_CHANGE_TO_VERTICAL_BAR_BLINKING=%ansi_escape%5 q
                        set ANSI_CURSOR_CHANGE_TO_VERTICAL_BAR_STEADY=%ansi_escape%6 q
                        rem Aliases:
                                set ANSI_CURSOR_SHAPE_DEFAULT=%ansi_escape%0 q
                                set ANSI_CURSOR_SHAPE_BLOCK_BLINKING=%ansi_escape%1 q
                                set ANSI_CURSOR_SHAPE_BLOCK_STEADY=%ansi_escape%2 q
                                set ANSI_CURSOR_SHAPE_UNDERLINE_BLINKING=%ansi_escape%3 q
                                set ANSI_CURSOR_SHAPE_UNDERLINE_STEADY=%ansi_escape%4 q
                                set ANSI_CURSOR_SHAPE_VERTICAL_BAR_BLINKING=%ansi_escape%5 q
                                set ANSI_CURSOR_SHAPE_VERTICAL_BAR_STEADY=%ansi_escape%6 q

                rem Random shape:
                        function ANSI_RANDOM_CURSOR_SHAPE=`%@char[27][%@random[0,6] q`
                        function ANSI_CURSOR_RANDOM_SHAPE=`%@char[27][%@random[0,6] q`
                        function ANSI_CURSOR_SHAPE_RANDOM=`%@char[27][%@random[0,6] q`
                        function      CURSOR_SHAPE_RANDOM=`%@char[27][%@random[0,6] q`
                        function      CURSOR_SHAPE_RANDOM=`%@char[27][%@random[0,6] q`
                        function      CURSOR_RANDOM_SHAPE=`%@char[27][%@random[0,6] q`
                        function      RANDOM_CURSOR_SHAPE=`%@char[27][%@random[0,6] q`

        rem Cursor color:
                rem Changing color by word, i.e. 'red', 'magenta':                
                        function    ANSI_CURSOR_CHANGE_COLOR_WORD=`%@char[27][ q%@char[27]]12;%1%@char[7]`                
                        function      CURSOR_COLOR_CHANGE_BY_WORD=`%@char[27][ q%@char[27]]12;%1%@char[7]`
                        function        ANSI_CURSOR_COLOR_BY_WORD=`%@char[27][ q%@char[27]]12;%1%@char[7]`
                        function         ANSI_CURSOR_COLOR_CHANGE=`%@char[27][ q%@char[27]]12;%1%@char[7]`
                        function         SET_CURSOR_COLOR_BY_WORD=`%@char[27][ q%@char[27]]12;%1%@char[7]`
                        function             CURSOR_COLOR_BY_WORD=`%@char[27][ q%@char[27]]12;%1%@char[7]`
                        function              CURSOR_COLOR_CHANGE=`%@char[27][ q%@char[27]]12;%1%@char[7]`
                        function                ANSI_CURSOR_COLOR=`%@char[27][ q%@char[27]]12;%1%@char[7]`
                        function                 SET_CURSOR_COLOR=`%@char[27][ q%@char[27]]12;%1%@char[7]`
                        function                     CURSOR_COLOR=`%@char[27][ q%@char[27]]12;%1%@char[7]`

                rem Changing color by hex, i.e. 'FF0000', 'FF00FF':
                        function     ANSI_CURSOR_CHANGE_COLOR_HEX=`%@char[27][ q%@char[27]]12;#%1%@char[7]`                  %+ rem like above section but with "#" in front of color
                        function     ANSI_CURSOR_COLOR_CHANGE_HEX=`%@char[27][ q%@char[27]]12;#%1%@char[7]`
                        function          CURSOR_COLOR_CHANGE_HEX=`%@char[27][ q%@char[27]]12;#%1%@char[7]`
                        function            ANSI_CURSOR_COLOR_HEX=`%@char[27][ q%@char[27]]12;#%1%@char[7]`
                        function             SET_CURSOR_COLOR_HEX=`%@char[27][ q%@char[27]]12;#%1%@char[7]`
                        function                 CURSOR_COLOR_HEX=`%@char[27][ q%@char[27]]12;#%1%@char[7]`
                        rem       ANSI_CURSOR_CHANGE_COLOR_BY_HEX=`%@char[27][ q%@char[27]]12;#%1%@char[7]` —— name too long
                        rem       ANSI_CURSOR_COLOR_CHANGE_BY_HEX=`%@char[27][ q%@char[27]]12;#%1%@char[7]` —— name too long
                        function       CURSOR_COLOR_CHANGE_BY_HEX=`%@char[27][ q%@char[27]]12;#%1%@char[7]`
                        function         ANSI_CURSOR_COLOR_BY_HEX=`%@char[27][ q%@char[27]]12;#%1%@char[7]`
                        function          SET_CURSOR_COLOR_BY_HEX=`%@char[27][ q%@char[27]]12;#%1%@char[7]`
                        function              CURSOR_COLOR_BY_HEX=`%@char[27][ q%@char[27]]12;#%1%@char[7]`

                rem Random color:
                        function ANSI_CURSOR_CHANGE_COLOR_RANDOM=`%@ansi_cursor_color_by_hex[%@random_rgb_hex[]]`
                        rem Aliases:
                               function ANSI_CURSOR_COLOR_RANDOM=`%@ansi_cursor_color_by_hex[%@random_rgb_hex[]]`
                               function      RANDOM_CURSOR_COLOR=`%@ansi_cursor_color_by_hex[%@random_rgb_hex[]]`

                rem Random shape *AND* color:
                        function    ANSI_CURSOR_RANDOM=`%@ansi_cursor_color_by_hex[%@random_rgb_hex[]]%@char[27][%@random[0,6] q`
                        rem Aliases:                                                                                            
                                function RANDOM_CURSOR=`%@ansi_cursor_color_by_hex[%@random_rgb_hex[]]%@char[27][%@random[0,6] q`
                                function    RANDCURSOR=`%@ansi_cursor_color_by_hex[%@random_rgb_hex[]]%@char[27][%@random[0,6] q`
                                function    CURSORRAND=`%@ansi_cursor_color_by_hex[%@random_rgb_hex[]]%@char[27][%@random[0,6] q`
                                echos %@RANDCURSOR[]

rem ———————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————

rem ANSI: special stuff: cursor position save/restore
        set ANSI_POSITION_SAVE=%ESCAPE%7%ANSI_ESCAPE%s                  %+ REM we do this the DEC way, then the SCO way
        set ANSI_POSITION_RESTORE=%ESCAPE%8%ANSI_ESCAPE%u               %+ REM we do this the DEC way, then the SCO way
            set ANSI_SAVE_POSITION=%ANSI_POSITION_SAVE%                
            set ANSI_RESTORE_POSITION=%ANSI_POSITION_RESTORE%          
            set ANSI_RESTORE=%ANSI_POSITION_RESTORE%          
            set ANSI_LOAD_POSITION=%ANSI_POSITION_RESTORE%          
            set ANSI_POSITION_LOAD=%ANSI_POSITION_RESTORE%          

rem ANSI: special stuff: cursor position requests/polling:
        set ANSI_POSITION_REQUEST=%ANSI_ESCAPE%6n	                    %+ REM query/request current cursor position (reports as ESC[#;#R)
            set       ANSI_REQUEST_POSITION=%ANSI_POSITION_REQUEST%
            set        ANSI_CURSOR_POSITION=%ANSI_POSITION_REQUEST%
            set ANSI_REPORT_CURSOR_POSITION=%ANSI_POSITION_REQUEST%
        set ANSI_REQUEST_FG_COLOR=%ANSI_ESCAPE%38;5;n	                %+ rem query/request current foreground color (2024: not supported in windows terminal)
        set ANSI_REQUEST_BG_COLOR=%ANSI_ESCAPE%48;5;n	                %+ rem query/request current foreground color (2024: not supported in windows terminal)

rem ANSI: cursor position movement
        rem To Home
            set ANSI_HOME=%ANSI_ESCAPE%H	                                %+ REM moves cursor to home position (0, 0)
                set ANSI_MOVE_HOME=%ANSI_HOME%
                set ANSI_MOVE_TO_HOME=%ANSI_HOME%

        rem To a specific position:
            function ANSI_MOVE_TO_POS1=`%@CHAR[27][%1;%2H`                  %+ rem moves cursor to line #, column #\_____ both work
            function ANSI_MOVE_TO_POS2=`%@CHAR[27][%1;%2f`                  %+ rem moves cursor to line #, column #/
                function ANSI_MOVE_POS=`%@CHAR[27][%1;%2H`                  %+ rem alias
                function ANSI_MOVE=`%@CHAR[27][%1;%2H`                      %+ rem alias
            function ANSI_MOVE_TO_COL=`%@CHAR[27][%1G`	                    %+ rem moves cursor to column #
            function ANSI_MOVE_TO_ROW=`%@CHAR[27][%1H`                      %+ rem unfortunately does not preserve column position! not possible! cursor request ansi code return value cannot be captured
            rem tion ANSI_MOVE_TO_COORDINATE                                %+ rem is defined in our unsupported section, as it's a replacement for an unsupported code
            rem tion ANSI_MOVE_TO                                           %+ rem is defined in our unsupported section, as it's a replacement for an unsupported code

        rem Up/Down/Left/Right:
            set ANSI_MOVE_UP_1=%ESCAPE%M                                    %+ rem moves cursor one line up, scrolling if needed
                set ANSI_MOVE_UP_ONE=%ANSI_MOVE_UP_1%                       %+ rem alias
            function ANSI_MOVE_UP=`%@CHAR[27][%1A`                          %+ rem moves cursor up # lines
                function ANSI_UP=`%@CHAR[27][%1A`	                        %+ rem alias
            function ANSI_MOVE_DOWN=`%@CHAR[27][%1B`	                    %+ rem moves cursor down # lines
                function ANSI_DOWN=`%@CHAR[27][%1B`                         %+ rem alias
            function ANSI_MOVE_RIGHT=`%@CHAR[27][%1C`	                    %+ rem moves cursor right # columns
                function ANSI_RIGHT=`%@CHAR[27][%1C`	                    %+ rem alias
            function ANSI_MOVE_LEFT=`%@CHAR[27][%1D`	                    %+ rem moves cursor left # columns
                function ANSI_LEFT=`%@CHAR[27][%1D`                         %+ rem alias

        rem Line-based:
            function   ANSI_MOVE_LINES_UP=`%@CHAR[27][%1F`                  %+ rem moves cursor to beginning of previous line, # lines up
            function   ANSI_MOVE_UP_LINES=`%@CHAR[27][%1F`                  %+ rem moves cursor to beginning of previous line, # lines up
            function ANSI_MOVE_LINES_DOWN=`%@CHAR[27][%1E`                  %+ rem moves cursor to beginning of next line, # lines down
            function ANSI_MOVE_DOWN_LINES=`%@CHAR[27][%1E`                  %+ rem moves cursor to beginning of next line, # lines down

        rem Tab-stop management:
            set        ANSI_TABSTOP_SET=%ESCAPE%H                            %+ rem Sets a tab stop in the current column the cursor is on
            set    ANSI_TABSTOP_SET_COL=%ESCAPE%H                            %+ rem Sets a tab stop in the current column the cursor is on
            set    ANSI_TABSTOP_CLR_COL=%ESCAPE%[0g                          %+ rem Clears tab stop in the current column the cursor is on
            set      ANSI_TABSTOP_CLEAR=%ESCAPE%[0g                          %+ rem Clears tab stop in the current column the cursor is on
            set  ANSI_TABSTOP_CLEAR_COL=%ESCAPE%[0g                          %+ rem Clears tab stop in the current column the cursor is on
            set  ANSI_TABSTOP_CLEAR_ALL=%ESCAPE%[3g                          %+ rem Clears ALLLLLLLLLLLLLLL tab stops —— better run     reset-tab-stops.bat after!
            set ANSI_TABSTOP_RESET_TO_8=%ESCAPE%[?W                          %+ rem resets all tabs to width of 8 —— in leiu of running reset-tab-stops.bat after!
            set      ANSI_TABSTOP_RESET=%ESCAPE%[?W                          %+ rem resets all tabs to width of 8 —— in leiu of running reset-tab-stops.bat after!

        rem Tab-stop management: Not very useful:
            function  ANSI_TAB_FORWARD=`%@CHAR[27][%1I`                     %+ rem Advance the cursor to the   next   column (in the same row) with a tab stop. If there are no more tab stops, move to the  last column in the row. If the cursor is in the  last column, move to the first column of the next row
            function ANSI_TAB_BACKWARD=`%@CHAR[27][%1Z`                     %+ rem Retreat the cursor to the previous column (in the same row) with a tab stop. If there are no more tab stops, move to the first column in the row. If the cursor is in the first column, don't move the cursor



rem ———————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————


REM ANSI: styles —— As of Windows Terminal we can now actually display italic characters
        REM 0m=reset, 1m=bold, 2m=faint, 3m=italic, 4m=underline, 5m=blink slow, 6m=blink fast, 7m=reverse, 8m=conceal, 9m=strikethrough
        set ANSI_BOLD=%ANSI_ESCAPE%1m
        set ANSI_BOLD_ON=%ANSI_BOLD%
        set ANSI_BOLD_OFF=%ANSI_ESCAPE%22m
        set      BOLD_ON=%ANSI_BOLD_ON%
        set      BOLD_OFF=%ANSI_BOLD_OFF%
        set      BOLD=%BOLD_ON%

            set ANSI_BRIGHT=%ANSI_BOLD%
            set ANSI_BRIGHT_ON=%ANSI_BOLD%
            set ANSI_BRIGHT_OFF=%ANSI_ESCAPE%22m
            set      BRIGHT_ON=%ANSI_BOLD_ON%
            set      BRIGHT_OFF=%ANSI_BOLD_OFF%
            set      BRIGHT=%BOLD_ON%

        set ANSI_FAINT=%ANSI_ESCAPE%2m
        set ANSI_FAINT_ON=%ANSI_FAINT%
        set ANSI_FAINT_OFF=%ANSI_ESCAPE%22m
        set      FAINT_ON=%ANSI_FAINT_ON%
        set      FAINT_OFF=%ANSI_FAINT_OFF%
        set      FAINT=%FAINT_ON%

        set ANSI_ITALICS=%ANSI_ESCAPE%3m
        set ANSI_ITALICS_ON=%ANSI_ITALICS%
        set ANSI_ITALICS_OFF=%ANSI_ESCAPE%23m
        set      ITALICS_ON=%ANSI_ITALICS_ON%
        set      ITALICS_OFF=%ANSI_ITALICS_OFF%
        set      ITALICS=%ITALICS_ON%

        set ANSI_UNDERLINE=%ANSI_ESCAPE%4m
        set ANSI_UNDERLINE_ON=%ANSI_UNDERLINE%
        set ANSI_UNDERLINE_OFF=%ANSI_ESCAPE%24m
        set      UNDERLINE_ON=%ANSI_UNDERLINE_ON%
        set      UNDERLINE_OFF=%ANSI_UNDERLINE_OFF%
        set      UNDERLINE=%UNDERLINE_ON%

        set ANSI_OVERLINE=%ANSI_ESCAPE%53m
        set ANSI_OVERLINE_ON=%ANSI_OVERLINE%
        set ANSI_OVERLINE_OFF=%ANSI_ESCAPE%55m
        set      OVERLINE_ON=%ANSI_OVERLINE_ON%
        set      OVERLINE_OFF=%ANSI_OVERLINE_OFF%
        set      OVERLINE=%OVERLINE_ON%

        set ANSI_DOUBLE_UNDERLINE=%ANSI_ESCAPE%21m
        set ANSI_DOUBLE_UNDERLINE_ON=%ANSI_DOUBLE_UNDERLINE%
        set ANSI_DOUBLE_UNDERLINE_OFF=%ANSI_ESCAPE%24m
        set      DOUBLE_UNDERLINE_ON=%ANSI_DOUBLE_UNDERLINE_ON%
        set      DOUBLE_UNDERLINE_OFF=%ANSI_DOUBLE_UNDERLINE_OFF%
        set      DOUBLE_UNDERLINE=%DOUBLE_UNDERLINE_ON%

            set ANSI_UNDERLINE_DOUBLE=%ANSI_DOUBLE_UNDERLINE%
            set ANSI_UNDERLINE_DOUBLE_ON=%ANSI_DOUBLE_UNDERLINE_ON%
            set ANSI_UNDERLINE_DOUBLE_OFF=%ANSI_DOUBLE_UNDERLINE_OFF%
            set      UNDERLINE_DOUBLE_ON=%DOUBLE_UNDERLINE_ON%
            set      UNDERLINE_DOUBLE_OFF=%DOUBLE_UNDERLINE_OFF%
            set      UNDERLINE_DOUBLE=%DOUBLE_UNDERLINE%

        set ANSI_BLINK_SLOW=%ANSI_ESCAPE%5m
        set ANSI_BLINK_SLOW_ON=%ANSI_BLINK_SLOW%
        set ANSI_BLINK_SLOW_OFF=%ANSI_ESCAPE%25m
        set      BLINK_SLOW_ON=%ANSI_BLINK_SLOW_ON%
        set      BLINK_SLOW_OFF=%ANSI_BLINK_SLOW_OFF%
        set      BLINK_SLOW=%BLINK_SLOW_ON%

        set ANSI_BLINK_FAST=%ANSI_ESCAPE%6m
        set ANSI_BLINK_FAST_ON=%ANSI_BLINK_FAST%
        set ANSI_BLINK_FAST_OFF=%ANSI_ESCAPE%25m
        set      BLINK_FAST_ON=%ANSI_BLINK_FAST_ON%
        set      BLINK_FAST_OFF=%ANSI_BLINK_FAST_OFF%
        set      BLINK_FAST=%BLINK_FAST_ON%

        set ANSI_BLINK=%ANSI_BLINK_FAST%
        set ANSI_BLINK_ON=%ANSI_BLINK_FAST_ON%
        set ANSI_BLINK_OFF=%ANSI_BLINK_FAST_OFF%
        set      BLINK_ON=%ANSI_BLINK_ON%
        set      BLINK_OFF=%ANSI_BLINK_OFF%
        set      BLINK=%BLINK_ON%

        set ANSI_REVERSE=%ANSI_ESCAPE%7m
        set ANSI_REVERSE_ON=%ANSI_REVERSE%
        set ANSI_REVERSE_OFF=%ANSI_ESCAPE%27m
        set      REVERSE_ON=%ANSI_REVERSE_ON%
        set      REVERSE_OFF=%ANSI_REVERSE_OFF%
        set      REVERSE=%REVERSE_ON%

        set ANSI_CONCEAL=%ANSI_ESCAPE%8m
        set ANSI_CONCEAL_ON=%ANSI_CONCEAL%
        set ANSI_CONCEAL_OFF=%ANSI_ESCAPE%28m
        set      CONCEAL_ON=%ANSI_CONCEAL_ON%
        set      CONCEAL_OFF=%ANSI_CONCEAL_OFF%
        set      CONCEAL=%CONCEAL_ON%
        set      INVISIBLE_ON=%ANSI_CONCEAL_ON%
        set      INVISIBLE_OFF=%ANSI_CONCEAL_OFF%
        set      INVISIBLE=%CONCEAL_ON%

        set ANSI_STRIKETHROUGH=%ANSI_ESCAPE%9m
        set ANSI_STRIKETHROUGH_ON=%ANSI_STRIKETHROUGH%
        set ANSI_STRIKETHROUGH_OFF=%ANSI_ESCAPE%29m
        set      STRIKETHROUGH_ON=%ANSI_STRIKETHROUGH_ON%
        set      STRIKETHROUGH_OFF=%ANSI_STRIKETHROUGH_OFF%
        set      STRIKETHROUGH=%STRIKETHROUGH_ON%
            set OVERSTRIKE_ON=%STRIKETHROUGH_ON%
            set OVERSTRIKE_OFF=%STRIKETHROUGH_OFF%
            set OVERSTRIKE=%OVERSTRIKE_ON%

        REM wow it even supports the vt100 2-line-tall (double-height) and wide (double-wide) text!
                set WIDE=%ESCAPE%#6
                    set WIDE_ON=%WIDE%
                    set WIDELINE=%WIDE%
                    set WIDE_LINE=%WIDE%
                    set WIDE_OFF=%ESCAPE%#5
                    set ANSI_WIDE_ON=%WIDE%
                    set ANSI_WIDELINE=%WIDE%
                    set ANSI_WIDE_LINE=%WIDE%
                    set ANSI_WIDE_OFF=%ESCAPE%#5
                set BIG_TEXT_LINE_1=%ESCAPE%#3
                set BIG_TEXT_LINE_2=%ESCAPE%#4
                    set BIG_TOP=%BIG_TEXT_LINE_1%
                    set BIG_TOP_ON=%BIG_TOP%
                    set BIG_BOT=%BIG_TEXT_LINE_2%
                    set BIG_BOT_ON=%BIG_BOT%
                    set BIG_BOTTOM=%BIG_BOT%
                    set BIG_BOTTOM_ON=%BIG_BOTTOM%
                    REM this/these is/are guess(es):
                        set BIG_TEXT_END=%ESCAPE%#0
                        set BIG_OFF=%BIG_TEXT_END%
                        set BIG_TEXT_OFF=%BIG_OFF%
                        set BIG_TOP_OFF=%BIG_OFF%
                        set BIG_BOT_OFF=%BIG_OFF%

rem ———————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————

rem ANSI: colors 
        echos %@RANDCURSOR[]
        rem custom rgb colors for foreground/background
             set ANSI_RGB_PREFIX=%ANSI_ESCAPE%38;2;
             set ANSI_RGB_SUFFIX=m
             function        ANSI_RGB=`%@CHAR[27][38;2;%1;%2;%3m`
                 function     ANSI_FG=`%@CHAR[27][38;2;%1;%2;%3m`           %+ rem alias
                 function ANSI_RGB_FG=`%@CHAR[27][38;2;%1;%2;%3m`           %+ rem alias
                 function ANSI_FG_RGB=`%@CHAR[27][38;2;%1;%2;%3m`           %+ rem alias
             function     ANSI_RGB_BG=`%@CHAR[27][48;2;%1;%2;%3m`               
                 function     ANSI_BG=`%@CHAR[27][48;2;%1;%2;%3m`           %+ rem alias
                 function ANSI_BG_RGB=`%@CHAR[27][48;2;%1;%2;%3m`           %+ rem alias
        rem random rgb colors for foreground/background
             function         RAND_BG=`%@CHAR[27][48;2;%@RANDOM[55,255];%@RANDOM[42,255];%@RANDOM[42,255]m`
                 function      RANDBG=`%@CHAR[27][48;2;%@RANDOM[55,255];%@RANDOM[42,255];%@RANDOM[42,255]m`
                 function ANSI_RANDBG=`%@CHAR[27][48;2;%@RANDOM[55,255];%@RANDOM[42,255];%@RANDOM[42,255]m`
             function         RAND_FG=`%@CHAR[27][38;2;%@RANDOM[55,255];%@RANDOM[42,255];%@RANDOM[42,255]m`
                 function      RANDFG=`%@CHAR[27][38;2;%@RANDOM[55,255];%@RANDOM[42,255];%@RANDOM[42,255]m`
                 function ANSI_RANDFG=`%@CHAR[27][38;2;%@RANDOM[55,255];%@RANDOM[42,255];%@RANDOM[42,255]m`
             function  ANSI_RANDCOLOR=`%@CHAR[27][38;2;%@RANDOM[55,255];%@RANDOM[42,255];%@RANDOM[42,255]m%@CHAR[27][48;2;%@RANDOM[55,255];%@RANDOM[42,255];%@RANDOM[42,255]m`
                 function   RANDCOLOR=`%@CHAR[27][38;2;%@RANDOM[55,255];%@RANDOM[42,255];%@RANDOM[42,255]m%@CHAR[27][48;2;%@RANDOM[55,255];%@RANDOM[42,255];%@RANDOM[42,255]m`
                 function    RANDFGBG=`%@CHAR[27][38;2;%@RANDOM[55,255];%@RANDOM[42,255];%@RANDOM[42,255]m%@CHAR[27][48;2;%@RANDOM[55,255];%@RANDOM[42,255];%@RANDOM[42,255]m`
                 function    RANDBGFG=`%@CHAR[27][38;2;%@RANDOM[55,255];%@RANDOM[42,255];%@RANDOM[42,255]m%@CHAR[27][48;2;%@RANDOM[55,255];%@RANDOM[42,255];%@RANDOM[42,255]m`
                 function    RANDBOTH=`%@CHAR[27][38;2;%@RANDOM[55,255];%@RANDOM[42,255];%@RANDOM[42,255]m%@CHAR[27][48;2;%@RANDOM[55,255];%@RANDOM[42,255];%@RANDOM[42,255]m`
        rem "soft constants" to be maintained both here and in copy-move-post.py for softer/readable random values
            set MIN_RGB_VALUE_FG=88
            set MAX_RGB_VALUE_FG=255
            set MIN_RGB_VALUE_BG=12
            set MAX_RGB_VALUE_BG=40
            rem but for my command line general usage i noticed i want the backgrounds to be a bit brighter, lol: 
            rem           (make sure it's not possible for these values to exceed 255)
                set EMPHASIS_BG_EXPANSION_FACTOR=1.4
                set MIN_RGB_VALUE_BG=%@FLOOR[%@EVAL[%MIN_RGB_VALUE_BG*%EMPHASIS_BG_EXPANSION_FACTOR%]]
                Set MAX_RGB_VALUE_BG=%@FLOOR[%@EVAL[%MAX_RGB_VALUE_BG*%EMPHASIS_BG_EXPANSION_FACTOR%]]

        rem copy of "random rgb colors for foreground/background" section above but using soft constants
             function         RAND_BG_SOFT=`%@CHAR[27][48;2;%@RANDOM[%[MIN_RGB_VALUE_BG],%[MAX_RGB_VALUE_BG]];%@RANDOM[%[MIN_RGB_VALUE_BG],%[MAX_RGB_VALUE_BG]];%@RANDOM[%[MIN_RGB_VALUE_BG],%[MAX_RGB_VALUE_BG]]m`
                 function      RANDBG_SOFT=`%@CHAR[27][48;2;%@RANDOM[%[MIN_RGB_VALUE_BG],%[MAX_RGB_VALUE_BG]];%@RANDOM[%[MIN_RGB_VALUE_BG],%[MAX_RGB_VALUE_BG]];%@RANDOM[%[MIN_RGB_VALUE_BG],%[MAX_RGB_VALUE_BG]]m`
                 function ANSI_RANDBG_SOFT=`%@CHAR[27][48;2;%@RANDOM[%[MIN_RGB_VALUE_BG],%[MAX_RGB_VALUE_BG]];%@RANDOM[%[MIN_RGB_VALUE_BG],%[MAX_RGB_VALUE_BG]];%@RANDOM[%[MIN_RGB_VALUE_BG],%[MAX_RGB_VALUE_BG]]m`
             function         RAND_FG_SOFT=`%@CHAR[27][38;2;%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]];%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]];%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]]m`
                 function      RANDFG_SOFT=`%@CHAR[27][38;2;%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]];%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]];%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]]m`
                 function ANSI_RANDFG_SOFT=`%@CHAR[27][38;2;%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]];%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]];%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]]m`
             function  ANSI_RANDCOLOR_SOFT=`%@CHAR[27][38;2;%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]];%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]];%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]]m%@CHAR[27][48;2;%@RANDOM[%[MIN_RGB_VALUE_BG],%[MAX_RGB_VALUE_BG]];%@RANDOM[%[MIN_RGB_VALUE_BG],%[MAX_RGB_VALUE_BG]];%@RANDOM[%[MIN_RGB_VALUE_BG],%[MAX_RGB_VALUE_BG]]m`
                 function   RANDCOLOR_SOFT=`%@CHAR[27][38;2;%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]];%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]];%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]]m%@CHAR[27][48;2;%@RANDOM[%[MIN_RGB_VALUE_BG],%[MAX_RGB_VALUE_BG]];%@RANDOM[%[MIN_RGB_VALUE_BG],%[MAX_RGB_VALUE_BG]];%@RANDOM[%[MIN_RGB_VALUE_BG],%[MAX_RGB_VALUE_BG]]m`
                 function    RANDFGBG_SOFT=`%@CHAR[27][38;2;%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]];%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]];%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]]m%@CHAR[27][48;2;%@RANDOM[%[MIN_RGB_VALUE_BG],%[MAX_RGB_VALUE_BG]];%@RANDOM[%[MIN_RGB_VALUE_BG],%[MAX_RGB_VALUE_BG]];%@RANDOM[%[MIN_RGB_VALUE_BG],%[MAX_RGB_VALUE_BG]]m`
                 function    RANDBGFG_SOFT=`%@CHAR[27][38;2;%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]];%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]];%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]]m%@CHAR[27][48;2;%@RANDOM[%[MIN_RGB_VALUE_BG],%[MAX_RGB_VALUE_BG]];%@RANDOM[%[MIN_RGB_VALUE_BG],%[MAX_RGB_VALUE_BG]];%@RANDOM[%[MIN_RGB_VALUE_BG],%[MAX_RGB_VALUE_BG]]m`
                 function    RANDBOTH_SOFT=`%@CHAR[27][38;2;%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]];%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]];%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]]m%@CHAR[27][48;2;%@RANDOM[%[MIN_RGB_VALUE_BG],%[MAX_RGB_VALUE_BG]];%@RANDOM[%[MIN_RGB_VALUE_BG],%[MAX_RGB_VALUE_BG]];%@RANDOM[%[MIN_RGB_VALUE_BG],%[MAX_RGB_VALUE_BG]]m`

             rem copy of the ones above but without underscores
                 function        RANDBGSOFT=`%@CHAR[27][48;2;%@RANDOM[%[MIN_RGB_VALUE_BG],%[MAX_RGB_VALUE_BG]];%@RANDOM[%[MIN_RGB_VALUE_BG],%[MAX_RGB_VALUE_BG]];%@RANDOM[%[MIN_RGB_VALUE_BG],%[MAX_RGB_VALUE_BG]]m`
                 function        RANDBGSOFT=`%@CHAR[27][48;2;%@RANDOM[%[MIN_RGB_VALUE_BG],%[MAX_RGB_VALUE_BG]];%@RANDOM[%[MIN_RGB_VALUE_BG],%[MAX_RGB_VALUE_BG]];%@RANDOM[%[MIN_RGB_VALUE_BG],%[MAX_RGB_VALUE_BG]]m`
                 function    ANSIRANDBGSOFT=`%@CHAR[27][48;2;%@RANDOM[%[MIN_RGB_VALUE_BG],%[MAX_RGB_VALUE_BG]];%@RANDOM[%[MIN_RGB_VALUE_BG],%[MAX_RGB_VALUE_BG]];%@RANDOM[%[MIN_RGB_VALUE_BG],%[MAX_RGB_VALUE_BG]]m`
                 function        RANDFGSOFT=`%@CHAR[27][38;2;%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]];%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]];%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]]m`
                 function        RANDFGSOFT=`%@CHAR[27][38;2;%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]];%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]];%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]]m`
                 function    ANSIRANDFGSOFT=`%@CHAR[27][38;2;%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]];%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]];%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]]m`
                 function ANSIRANDCOLORSOFT=`%@CHAR[27][38;2;%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]];%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]];%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]]m%@CHAR[27][48;2;%@RANDOM[%[MIN_RGB_VALUE_BG],%[MAX_RGB_VALUE_BG]];%@RANDOM[%[MIN_RGB_VALUE_BG],%[MAX_RGB_VALUE_BG]];%@RANDOM[%[MIN_RGB_VALUE_BG],%[MAX_RGB_VALUE_BG]]m`
                 function     RANDCOLORSOFT=`%@CHAR[27][38;2;%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]];%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]];%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]]m%@CHAR[27][48;2;%@RANDOM[%[MIN_RGB_VALUE_BG],%[MAX_RGB_VALUE_BG]];%@RANDOM[%[MIN_RGB_VALUE_BG],%[MAX_RGB_VALUE_BG]];%@RANDOM[%[MIN_RGB_VALUE_BG],%[MAX_RGB_VALUE_BG]]m`
                 function      RANDFGBGSOFT=`%@CHAR[27][38;2;%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]];%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]];%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]]m%@CHAR[27][48;2;%@RANDOM[%[MIN_RGB_VALUE_BG],%[MAX_RGB_VALUE_BG]];%@RANDOM[%[MIN_RGB_VALUE_BG],%[MAX_RGB_VALUE_BG]];%@RANDOM[%[MIN_RGB_VALUE_BG],%[MAX_RGB_VALUE_BG]]m`
                 function      RANDBGFGSOFT=`%@CHAR[27][38;2;%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]];%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]];%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]]m%@CHAR[27][48;2;%@RANDOM[%[MIN_RGB_VALUE_BG],%[MAX_RGB_VALUE_BG]];%@RANDOM[%[MIN_RGB_VALUE_BG],%[MAX_RGB_VALUE_BG]];%@RANDOM[%[MIN_RGB_VALUE_BG],%[MAX_RGB_VALUE_BG]]m`
                 function      RANDBOTHSOFT=`%@CHAR[27][38;2;%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]];%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]];%@RANDOM[%[MIN_RGB_VALUE_FG],%[MAX_RGB_VALUE_FG]]m%@CHAR[27][48;2;%@RANDOM[%[MIN_RGB_VALUE_BG],%[MAX_RGB_VALUE_BG]];%@RANDOM[%[MIN_RGB_VALUE_BG],%[MAX_RGB_VALUE_BG]];%@RANDOM[%[MIN_RGB_VALUE_BG],%[MAX_RGB_VALUE_BG]]m`

            rem example usage for random foreground: echos %@RANDFG[]
            rem example usage for random background: echos %@RANDBG[]


        rem Foreground Colors —— todo bright purple
            set ANSI_BLACK=%ANSI_ESCAPE%30m
            set ANSI_GRAY=%ANSI_ESCAPE%90m
            set ANSI_GREY=%ANSI_ESCAPE%90m
            set ANSI_WHITE=%ANSI_ESCAPE%37m
            set ANSI_PINK=%@ANSI_RGB[215,112,123]
            set ANSI_BRIGHT_PINK=%@ANSI_RGB[255,152,163]
            set ANSI_RED=%ANSI_ESCAPE%31m
            set ANSI_ORANGE=%@ANSI_RGB[235,107,0]
            set ANSI_BRIGHT_ORANGE=%@ANSI_RGB[255,175,0]
            set ANSI_YELLOW=%ANSI_ESCAPE%33m
            set ANSI_GREEN=%ANSI_ESCAPE%32m
            set ANSI_CYAN=%ANSI_ESCAPE%36m
            set ANSI_BLUE=%ANSI_ESCAPE%34m
            set ANSI_PURPLE=%@ANSI_RGB[128,0,128]
            set ANSI_MAGENTA=%@ANSI_RGB[170,0,170]
            set ANSI_MAGENTA_OFFICIAL=%ANSI_ESCAPE%35m
            set ANSI_BRIGHT_BLACK=%ANSI_GREY%
            set ANSI_BRIGHT_RED=%ANSI_ESCAPE%91m
            set ANSI_BRIGHT_GREEN=%ANSI_ESCAPE%92m
            set ANSI_BRIGHT_YELLOW=%ANSI_ESCAPE%93m
            set ANSI_BRIGHT_BLUE=%ANSI_ESCAPE%94m
            set ANSI_BRIGHT_MAGENTA=%ANSI_ESCAPE%95m
            set ANSI_BRIGHT_CYAN=%ANSI_ESCAPE%96m
            set ANSI_BRIGHT_WHITE=%ANSI_ESCAPE%97m
                set ANSI_WHITE_BRIGHT=%ANSI_ESCAPE%97m
                set ANSI_PINK_BRIGHT=%ANSI_BRIGHT_PINK%
                set ANSI_RED_BRIGHT=%ANSI_ESCAPE%91m
                set ANSI_ORANGE_BRIGHT=%ANSI_BRIGHT_ORANGE%
                set ANSI_YELLOW_BRIGHT=%ANSI_ESCAPE%93m
                set ANSI_GREEN_BRIGHT=%ANSI_ESCAPE%92m
                set ANSI_CYAN_BRIGHT=%ANSI_ESCAPE%96m
                set ANSI_BLUE_BRIGHT=%ANSI_ESCAPE%94m
                set ANSI_MAGENTA_BRIGHT=%ANSI_ESCAPE%95m
                set ANSI_COLOR_BLACK=%ANSI_ESCAPE%30m
                set ANSI_COLOR_GRAY=%ANSI_ESCAPE%90m
                set ANSI_COLOR_GREY=%ANSI_ESCAPE%90m
                set ANSI_COLOR_WHITE=%ANSI_ESCAPE%37m
                set ANSI_COLOR_PINK=%ANSI_PINK%
                set ANSI_COLOR_RED=%ANSI_ESCAPE%31m
                set ANSI_COLOR_ORANGE=%ANSI_ORANGE%
                set ANSI_COLOR_YELLOW=%ANSI_ESCAPE%33m
                set ANSI_COLOR_GREEN=%ANSI_ESCAPE%32m
                set ANSI_COLOR_CYAN=%ANSI_ESCAPE%36m
                set ANSI_COLOR_BLUE=%ANSI_ESCAPE%34m
                set ANSI_COLOR_PURPLE=%ANSI_PURPLE%
                set ANSI_COLOR_MAGENTA=%ANSI_MAGENTA%
                set ANSI_COLOR_MAGENTA_OFFICIAL=%ANSI_ESCAPE%35m
                set ANSI_COLOR_BRIGHT_BLACK=%ANSI_COLOR_GREY%
                set ANSI_COLOR_BRIGHT_WHITE=%ANSI_ESCAPE%97m
                set ANSI_COLOR_BRIGHT_PINK=%ANSI_BRIGHT_PINK%
                set ANSI_COLOR_BRIGHT_RED=%ANSI_ESCAPE%91m
                set ANSI_COLOR_BRIGHT_ORANGE=%ANSI_BRIGHT_ORANGE%
                set ANSI_COLOR_BRIGHT_YELLOW=%ANSI_ESCAPE%93m
                set ANSI_COLOR_BRIGHT_GREEN=%ANSI_ESCAPE%92m
                set ANSI_COLOR_BRIGHT_BLUE=%ANSI_ESCAPE%94m
                set ANSI_COLOR_BRIGHT_CYAN=%ANSI_ESCAPE%96m
                set ANSI_COLOR_BRIGHT_MAGENTA=%ANSI_ESCAPE%95m
                    set ANSI_COLOR_WHITE_BRIGHT=%ANSI_ESCAPE%97m
                    set ANSI_COLOR_PINK_BRIGHT=%ANSI_BRIGHT_PINK%
                    set ANSI_COLOR_RED_BRIGHT=%ANSI_ESCAPE%91m
                    set ANSI_COLOR_ORANGE_BRIGHT=%ANSI_BRIGHT_ORANGE%
                    set ANSI_COLOR_YELLOW_BRIGHT=%ANSI_ESCAPE%93m
                    set ANSI_COLOR_GREEN_BRIGHT=%ANSI_ESCAPE%92m
                    set ANSI_COLOR_CYAN_BRIGHT=%ANSI_ESCAPE%96m
                    set ANSI_COLOR_BLUE_BRIGHT=%ANSI_ESCAPE%94m
                    set ANSI_COLOR_MAGENTA_BRIGHT=%ANSI_ESCAPE%95m
        rem Background Colors
            set ANSI_BACKGROUND_BLACK=%@ANSI_BG[0,0,0]
            set ANSI_BACKGROUND_BLACK_NON_EXPERIMENTAL=%ANSI_ESCAPE%40m
            set ANSI_BACKGROUND_RED=%ANSI_ESCAPE%41m
            set ANSI_BACKGROUND_GREEN=%ANSI_ESCAPE%42m
            set ANSI_BACKGROUND_YELLOW=%ANSI_ESCAPE%43m
            set ANSI_BACKGROUND_BLUE=%ANSI_ESCAPE%44m
            set ANSI_BACKGROUND_MAGENTA=%ANSI_ESCAPE%45m
            set ANSI_BACKGROUND_CYAN=%ANSI_ESCAPE%46m
            set ANSI_BACKGROUND_WHITE=%ANSI_ESCAPE%47m
            set ANSI_BACKGROUND_GREY=%ANSI_ESCAPE%100m
            set ANSI_BACKGROUND_GRAY=%ANSI_ESCAPE%100m
            set ANSI_BACKGROUND_BRIGHT_RED=%ANSI_ESCAPE%101m
            set ANSI_BACKGROUND_BRIGHT_GREEN=%ANSI_ESCAPE%102m
            set ANSI_BACKGROUND_BRIGHT_YELLOW=%ANSI_ESCAPE%103m
            set ANSI_BACKGROUND_BRIGHT_BLUE=%ANSI_ESCAPE%104m
            set ANSI_BACKGROUND_BRIGHT_MAGENTA=%ANSI_ESCAPE%105m
            set ANSI_BACKGROUND_BRIGHT_CYAN=%ANSI_ESCAPE%106m
            set ANSI_BACKGROUND_BRIGHT_WHITE=%ANSI_ESCAPE%107m
                rem Aliases:
                    set ANSI_BG_BLACK=%ANSI_BACKGROUND_BLACK%
                    set ANSI_BG_BLACK_NON_EXPERIMENTAL=%ANSI_BACKGROUND_BLACK_NON_EXPERIMENTAL%
                    set ANSI_BG_RED=%ANSI_BACKGROUND_RED%
                    set ANSI_BG_GREEN=%ANSI_BACKGROUND_GREEN%
                    set ANSI_BG_YELLOW=%ANSI_BACKGROUND_YELLOW%
                    set ANSI_BG_BLUE=%ANSI_BACKGROUND_BLUE%
                    set ANSI_BG_MAGENTA=%ANSI_BACKGROUND_MAGENTA%
                    set ANSI_BG_CYAN=%ANSI_BACKGROUND_CYAN%
                    set ANSI_BG_WHITE=%ANSI_BACKGROUND_WHITE%
                    set ANSI_BG_GREY=%ANSI_BACKGROUND_GREY%
                    set ANSI_BG_GRAY=%ANSI_BACKGROUND_GRAY%
                    set ANSI_BG_BRIGHT_RED=%ANSI_BACKGROUND_BRIGHT_RED%
                    set ANSI_BG_BRIGHT_GREEN=%ANSI_BACKGROUND_BRIGHT_GREEN%
                    set ANSI_BG_BRIGHT_YELLOW=%ANSI_BACKGROUND_BRIGHT_YELLOW%
                    set ANSI_BG_BRIGHT_BLUE=%ANSI_BACKGROUND_BRIGHT_BLUE%
                    set ANSI_BG_BRIGHT_MAGENTA=%ANSI_BACKGROUND_BRIGHT_MAGENTA%
                    set ANSI_BG_BRIGHT_CYAN=%ANSI_BACKGROUND_BRIGHT_CYAN%
                    set ANSI_BG_BRIGHT_WHITE=%ANSI_BACKGROUND_BRIGHT_WHITE%


rem ———————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————



rem ANSI: erasing
    echos %@RANDCURSOR[]
    rem Clear Screen: \u001b[{n}J clears the screen
    rem                     n=0 clears from cursor until end of screen,
    rem                     n=1 clears from cursor to beginning of screen
    rem                     n=2 clears entire screen
    rem Clear Line: \u001b[{n}K clears the current line
    rem                   n=0 clears from cursor to end of line
    rem                   n=1 clears from cursor to start of line
    rem                   n=2 clears entire line
            set ANSI_ERASE_CURRENT_LINE=%ANSI_ESCAPE%K                      %+ rem erases in line
                set ANSI_ERASE_LINE=%ANSI_ERASE_CURRENT_LINE%               %+ rem alias
                set ANSI_CLEAR_LINE=%ANSI_ERASE_CURRENT_LINE%               %+ rem alias
                set ANSI_LINE_ERASE=%ANSI_ERASE_CURRENT_LINE%               %+ rem alias
                set ANSI_LINE_CLEAR=%ANSI_ERASE_CURRENT_LINE%               %+ rem alias
            set ANSI_ERASE_TO_END_OF_LINE=%ANSI_ESCAPE%0K                   %+ rem erases from cursor until end of line
                set ANSI_ERASE_TO_END=%ANSI_ERASE_TO_END_OF_LINE%
                set ANSI_CLEAR_TO_END=%ANSI_ERASE_TO_END_OF_LINE%
                set ANSI_ERASE_TO_EOL=%ANSI_ERASE_TO_END_OF_LINE%
                set ANSI_CLEAR_TO_EOL=%ANSI_ERASE_TO_END_OF_LINE%
                set     ANSI_LINE_FIX=%ANSI_ERASE_TO_END_OF_LINE%
                set      ANSI_LINEFIX=%ANSI_LINE_FIX%
                set          ANSI_EOL=%ANSI_LINE_FIX%
            set ANSI_ERASE_TO_BEG_OF_LINE=%ANSI_ESCAPE%1K                   %+ rem erases from cursor until end of line
                set ANSI_CLEAR_TO_BEG_OF_LINE=%ANSI_ERASE_TO_BEG_OF_LINE%
                set ANSI_ERASE_TO_BEG=%ANSI_ERASE_TO_BEG_OF_LINE%
                set ANSI_CLEAR_TO_BEG=%ANSI_ERASE_TO_BEG_OF_LINE%
                set ANSI_ERASE_TO_BOL=%ANSI_ERASE_TO_BEG_OF_LINE%
                set ANSI_CLEAR_TO_BOL=%ANSI_ERASE_TO_BEG_OF_LINE%
                set ANSI_ERASE_TO_BEGINNING_OF_LINE=%ANSI_ERASE_TO_BEG_OF_LINE%
                set ANSI_CLEAR_TO_BEGINNING_OF_LINE=%ANSI_ERASE_TO_BEG_OF_LINE%

            set ANSI_ERASE_TO_END_OF_SCREEN=%ANSI_ESCAPE%J                  %+ rem erases from cursor until end of the page
            set      ERASE_TO_END_OF_SCREEN=%ANSI_ESCAPE%J                  %+ rem erases from cursor until end of the page
            set   ANSI_ERASE_TO_END_OF_PAGE=%ANSI_ESCAPE%J                  %+ rem erases from cursor until end of the page
            set        ERASE_TO_END_OF_PAGE=%ANSI_ESCAPE%J                  %+ rem erases from cursor until end of the page
            set           ANSI_ERASE_TO_EOP=%ANSI_ESCAPE%J                  %+ rem erases from cursor until end of the page
            set                ERASE_TO_EOP=%ANSI_ESCAPE%J                  %+ rem erases from cursor until end of the page
            set     ANSI_ERASE_UP_TO_CURSOR=%ANSI_ESCAPE%1J                 %+ rem erases from start of page up to cursor! weird!
            set      ANSI_ERASE_ENTIRE_PAGE=%ANSI_ESCAPE%2J                 %+ rem erases entire screen
            set             ANSI_ERASE_PAGE=%ANSI_ESCAPE%2J                 %+ rem erases entire screen
            set                  ERASE_PAGE=%ANSI_ESCAPE%2J                 %+ rem erases entire screen
            set    ANSI_ERASE_ENTIRE_SCREEN=%ANSI_ESCAPE%2J                 %+ rem erases entire screen
            set           ANSI_ERASE_SCREEN=%ANSI_ESCAPE%2J                 %+ rem erases entire screen
            set                ERASE_SCREEN=%ANSI_ESCAPE%2J                 %+ rem erases entire screen
            set                    ANSI_CLS=%ANSI_ESCAPE%2J                 %+ rem erases entire screen

            rem UNIMPLEMENTED: L   Erase in Line   (ESC [ Ps K). Erases some or all of the Active Line according to the parameter.
            rem UNIMPLEMENTED: EF  Erase in Field  (ESC [ Pn N). Erases some or all of the Active Field according to the parameter.
            rem UNIMPLEMENTED: EA  Erase in Area   (ESC [ Ps O). Erases some or all of the Active Qualified Area according to the parameter.
            rem UNIMPLEMENTED: ECH Erase Character (ESC [ Pn X). Erases the following Pn characters, starting with the character at the cursor. The host may also erase a specified number of characters (up to 255).
            rem                                     ESC [ P	    Deletes  1 character
            rem                                     ESC [ 12 P	Deletes 12 characters


        rem truly esoteric stuff —— I believe this toggles whether the background color bleeds to the right of the screen when you hit enter
                    set ERASE_COLOR_MODE_ON=%ANSI_ESCAPE%?117h  
                    set ERASE_COLOR_MODE_OFF=%ANSI_ESCAPE%?117l


rem ———————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————

REM DEC drawing font support:
            set                   ANSI_FONT_DRAWING_ON=%[ESCAPE](0
            set                   ANSI_FONT_DRAWING_OFF=%ESCAPE%(B
            set ANSI_DRAWING_OFF=%ANSI_FONT_DRAWING_OFF%
            set      DRAWING_OFF=%ANSI_FONT_DRAWING_OFF%
            set  ANSI_DRAWING_ON=%ANSI_FONT_DRAWING_ON%
            set       DRAWING_ON=%ANSI_FONT_DRAWING_ON%
            set          DRAWING=%ANSI_FONT_DRAWING_ON%

            rem drawing font characters:
                    set DRAWING_FONT_CORNER_LOWER_RIGHT=j
                    set DRAWING_FONT_CORNER_UPPER_RIGHT=k
                    set DRAWING_FONT_CORNER_UPPER_LEFT=l
                    set DRAWING_FONT_CORNER_LOWER_LEFT=m
                    set DRAWING_FONT_PLUS=n
                    set DRAWING_FONT_DASH=q
                    set DRAWING_FONT_ROW_LEFT=t
                    set DRAWING_FONT_ROW_RIGHT=u
                    set DRAWING_FONT_COL_BOTTOM=v
                    set DRAWING_FONT_COL_BOT=v
                    set DRAWING_FONT_COL_TOP=w
                    set DRAWING_FONT_LINE_HORIZONTAL=q
                    set DRAWING_FONT_LINE_HORIZ=q
                    set DRAWING_FONT_LINE_VERTICAL=x
                    set DRAWING_FONT_LINE_VERT=x

rem ———————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————

REM ANSI: margin-setting / anti-scroll areas
        echos %@RANDCURSOR[]
        rem Cordoning off rows:
                rem Want to   lock the top  5 rows from scrolling?  echos @%ANSI_LOCK_TOP_ROWS[5]
                        function      ANSI_LOCK_TOP_ROWS=`%@CHAR[27]7%@CHAR[27][s%@CHAR[27][%@EVAL[%1+1];%[_rows]r%@CHAR[27]8%@CHAR[27][u`
                        function ANSI_UNLOCK_LOCKED_ROWS=`%@CHAR[27]7%@CHAR[27][s%@CHAR[27][0;%[_rows]r%@CHAR[27]8%@CHAR[27][u`
                        set      ANSI_UNLOCK_LOCKED_ROWS=`%@CHAR[27]7%@CHAR[27][s%@CHAR[27][0;%[_rows]r%@CHAR[27]8%@CHAR[27][u`
                rem Want to unlock all locked rows for  scrolling?  echos %ANSI_UNLOCK_ROWS%   or  echos %@ANSI_UNLOCK_ROWS[]
                        function        ANSI_UNLOCK_ROWS=`%@CHAR[27]7%@CHAR[27][s%@CHAR[27][0;%[_rows]r%@CHAR[27]8%@CHAR[27][u`
                        set             ANSI_UNLOCK_ROWS=`%@CHAR[27]7%@CHAR[27][s%@CHAR[27][0;%[_rows]r%@CHAR[27]8%@CHAR[27][u`
                        rem aliases:
                                function         ANSI_UNLOCK_ROW=`%@CHAR[27]7%@CHAR[27][s%@CHAR[27][0;%[_rows]r%@CHAR[27]8%@CHAR[27][u`
                                set              ANSI_UNLOCK_ROW=`%@CHAR[27]7%@CHAR[27][s%@CHAR[27][0;%[_rows]r%@CHAR[27]8%@CHAR[27][u`

        rem Cordoning off columns:
                rem Want to lock *columns* at the *sides*? That's funkier! First we have to determine the string to enable it:
                        set    ANSI_LOCK_COLUMNS_ENABLE=%ANSI_CSI%?69h
                rem Then, we incorporate that enabling screen into our function to lock BOTH sides an equal amount based on a single parameter:
                rem BUT A CATCH! You most likely want to do an echos %ANSI_POSITION_SAVE% and RESTORE before and after...
                        function ANSI_LOCK_SIDE_COLUMNS=`%@CHAR[27][?69h%@CHAR[27][%1;%@EVAL[%_COLUMNS-%1]s` %+ rem EXAMPLE: echos %@ANSI_LOCK_SIDE_COLUMNS[5]
                        function      ANSI_LOCK_COLUMNS=`%@CHAR[27][?69h%@CHAR[27][%1;%@EVAL[%_COLUMNS-%1]s` %+ rem EXAMPLE: echos %@ANSI_LOCK_SIDE_COLUMNS[5]
                        function    ANSI_LOCK_SIDE_COLS=`%@CHAR[27][?69h%@CHAR[27][%1;%@EVAL[%_COLUMNS-%1]s` %+ rem EXAMPLE: echos %@ANSI_LOCK_SIDE_COLUMNS[5]
                        function         ANSI_LOCK_COLS=`%@CHAR[27][?69h%@CHAR[27][%1;%@EVAL[%_COLUMNS-%1]s` %+ rem EXAMPLE: echos %@ANSI_LOCK_SIDE_COLUMNS[5]
                rem And when we want to unlock it, use the "?69l" code:                                      %+ rem EXAMPLE: echos %ANSI_UNLOCK_COLUMNS%
                        set   ANSI_LOCK_COLUMNS_DISABLE=%ANSI_CSI%?69l
                        set ANSI_LOCKED_COLUMNS_DISABLE=%ANSI_CSI%?69l
                        set         ANSI_UNLOCK_COLUMNS=%ANSI_CSI%?69l
                        set         ANSI_COLUMNS_UNLOCK=%ANSI_CSI%?69l
                        set          ANSI_RESET_COLUMNS=%ANSI_CSI%?69l
                        set           ANSI_COLUMS_RESET=%ANSI_CSI%?69l
                        set            ANSI_UNLOCK_COLS=%ANSI_CSI%?69l
                        set            ANSI_COLS_UNLOCK=%ANSI_CSI%?69l
                        set             ANSI_RESET_COLS=%ANSI_CSI%?69l
                        set             ANSI_COLS_RESET=%ANSI_CSI%?69l

        rem Unlocking everything:
                rem ANSI_UNLOCK=%@ANSI_UNLOCK_ROWS[0,%_ROWS]%ANSI_COLS_RESET% —— was not sufficient because the # of rows could be a pane that is smaller now but enlarged later, which would leave non-scrollable lines at the bottom. But 9999 also was not sufficient. Do with and without row argument to cover all bases.
                rem ANSI_UNLOCK=%@ANSI_UNLOCK_ROWS[0,999999]%@ANSI_UNLOCK_ROWS[]%ANSI_COLS_RESET%
                rem ANSI_UNLOCK=%ANSI_COLS_RESET%%@ANSI_UNLOCK_ROWS[]%@ANSI_UNLOCK_ROWS[0,999999]
                set ANSI_UNLOCK=%ANSI_COLS_RESET%%@ANSI_UNLOCK_ROWS[]%@ANSI_UNLOCK_ROWS[0,999999]
                SET ANSI_UNLOCK_TOP=%@ANSI_UNLOCK_ROWS[]
                SET ANSI_UNLOCK_ROWS=%@ANSI_UNLOCK_ROWS[]
                SET ANSI_UNLOCK_MARGINS=%ANSI_LOCK_COLUMNS_DISABLE%
                SET ANSI_UNLOCK_ALL=%ANSI_LOCK_COLUMNS_DISABLE%%@ANSI_UNLOCK_ROWS[]

        rem Cordining off an area (row_start,row_end,col_start,col_end)
                function      CORDON=`%@CHAR[27]7%@CHAR[27][s%@CHAR[27][%1;%[2]r%@CHAR[27]8%@CHAR[27][u`
                                  rem %@CHAR[27]7%@CHAR[27][s%@CHAR[27][%@EVAL[%1+1];%[_rows]r%@CHAR[27]8%@CHAR[27][u`
        rem A proof-of-concept function that makes us end up with cordoned off columns on both sides in a random color without disturbing your cursor location very much ... Very dramatic:
                function ANSI_COLOR_SIDE_COLS=`%ANSI_SAVE_POSITION%%@ANSI_RANDBG[]%ANSI_CLS%%@ANSI_LOCK_COLS[%1]%ANSI_RESTORE_POSITION%%@ANSI_MOVE_UP[2]%@ANSI_MOVE_RIGHT[%1]`

rem ———————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————

REM ANSI: unsupported in Windows Terminal:
        set      UNSUPPORTED_SET_UNDERLINE_COLOR=%ANSI_CSI%58;2;255,0,0m %+ REM set underline color to red
        set               UNSUPPORTED_NUMLOCK_ON=%ANSI_CSI%?108h
        set              UNSUPPORTED_NUMLOCK_OFF=%ANSI_CSI%?108l
        set             UNSUPORTED_RUN_ALL_TESTS=%ANSI_CSI%4;0y
        set        UNSUPPORTED_ANSI_DEFAULT_FONT=%ANSI_CSI%10m
        set          UNSUPPORTED_ANSI_ALT_FONT_1=%ANSI_CSI%11m
        set          UNSUPPORTED_ANSI_ALT_FONT_2=%ANSI_CSI%12m
        set          UNSUPPORTED_ANSI_ALT_FONT_3=%ANSI_CSI%13m
        set          UNSUPPORTED_ANSI_ALT_FONT_4=%ANSI_CSI%14m
        set          UNSUPPORTED_ANSI_ALT_FONT_5=%ANSI_CSI%15m
        set          UNSUPPORTED_ANSI_ALT_FONT_6=%ANSI_CSI%16m
        set          UNSUPPORTED_ANSI_ALT_FONT_7=%ANSI_CSI%17m
        set          UNSUPPORTED_ANSI_ALT_FONT_8=%ANSI_CSI%18m
        set          UNSUPPORTED_ANSI_ALT_FONT_9=%ANSI_CSI%19m
        set              UNSUPPORTED_ANSI_GOTHIC=%ANSI_CSI%20m
        set                   UNSUPPORTED_FRAMED=%ANSI_CSI%51m
        set                UNSUPPORTED_ENCIRCLED=%ANSI_CSI%52m
        set       UNSUPPORTED_FRAME_ENCIRCLE_OFF=%ANSI_CSI%54m
        function   UNSUPPORTED_SET_WARN_BELL_VOL=`%@CHAR[27][%1 t`              %+ rem 1/0/None=Off, 2-4=low, 5-8=high
        function UNSUPPORTED_SET_MARGIN_BELL_VOL=`%@CHAR[27][%1 u`              %+ rem 1=Off, 2-4=low, None,0,5-8=high
        function  ANSI_MOVE_TO_COORDINATE_UNSUPP=`%@CHAR[27][%1,%2H`            %+ rem Windows Terminal 2024 doesn't support this official code................
        function  ANSI_MOVE_TO_COORDINATE=`%@CHAR[27][%1H%@CHAR[27][%2G`        %+ rem    .........so instead, we reduce into 2 separate commands internally 😎
        function             ANSI_MOVE_TO=`%@CHAR[27][%1H%@CHAR[27][%2G`        %+ rem alias

        set UNSUPPORTED_MAP_A_TO_Z=%ANSI_DCS%"y1/7A/7A/7A/7A/7A/7A/-%ANSI_ST%   %+ rem Windows Terminal 2024 doesn't seem to support this 😢


rem ———————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————


REM ANSI: Custom Character Generation using ANSI & sixels —— so far just have Trumpets & Pentagrams

    rem     This sets up the trumpet (& reverse trumpet), pentagram (& pentacle), used in c:\bat\set-emojis.bat
                    REM Original advice given to me from ANSI guru:
                    REM         Step 1: DECDLD seq to define custom charset (aka soft font) w/four characters: "()*+" [ascii 40-44] representing the trumpet glyphs.
                    REM         Step 2: To activate charset, use SCS sequence w/id "@", i.e. "\x1B( @" [note that there's a space before the @!]
                    REM                 Then you can output left trumpet w/ *( & right w/ )+.
                    REM         Step 3: To return to regular text, you MUST switch back to charset with SCS sequence "\x1B(B"

    rem Various iterations of getting to our trumpets (first 3 remarks), then to our trumpets+pentacles (remarks 4 and beyond) —— you have to define them all in one sequence
            REM 1)  printf "\eP0;8;1;10;0;2;20;0{ @???~}{wo_?/[MFJp@@@@@/GCA@??????/??????????;?_ow{}~???/@@@@@pJFM[/??????@ACG/??????????;??????????/??_ogKYr}{/?_ow\\NVb`O/@B@???????;??????????/{}rYKgo_??/O`bVN\\wo_?/???????@B@\e\\"    %+ rem 10   x 20  character - max size on Windows Terminal is 16x32, which might be a little better than 10x20. Although be aware that that's not one of the standard sizes, so it may not work on other terminals. If it's just for personal use, though, you probably won't care.
            REM 2)    %ESCAPE%P0;8;1;10;0;2;20;0{ @???~}{wo_?/[MFJp@@@@@/GCA@??????/??????????;?_ow{}~???/@@@@@pJFM[/??????@ACG/??????????;??????????/??_ogKYr}{/?_ow\\NVb`O/@B@???????;??????????/{}rYKgo_??/O`bVN\\wo_?/???????@B@;1111111111/HHHHHHHHHH/zzzzzzzzzz/??????????%ESCAPE%
            REM 3)    %ESCAPE%P0;8;1;10;0;2;20;0{ @???~}{wo_?/[MFJp@@@@@/GCA@??????/??????????;?_ow{}~???/@@@@@pJFM[/??????@ACG/??????????;??????????/??_ogKYr}{/?_ow\\NVb`O/@B@???????;??????????/{}rYKgo_??/O`bVN\\wo_?/???????@B@;?_OGCCAaYM/}BEIQayFAA/BKO_oM`PIE/____@@AAAA%ESCAPE%
            REM 4)    it's a dang pentacle not a pentagram _?/[MFJp@@@@@/GCA@??????/??????????;?_ow{}~???/@@@@@pJFM[/??????@ACG/??????????;??????????/??_ogKYr}{/?_ow\\NVb`O/@B@???????;??????????/{}rYKgo_??/O`bVN\\wo_?/???????@B@;?_OGCCAaYM/}BEIQayFAA/BKO_oM`PIE/____@@AAAA@B@;YaACCGO_??/AFyaQIEB}?/IP`Mo_OKB?/AAA@@?????%ESCAPE%   %+ REM ———————————————————— this is when the pentagrams/pentacles were added:
            REM 5)    %ESCAPE%P0;8;1;10;0;2;20;0{ @???~}{wo_?/[MFJp@@@@@/GCA@??????/??????????;?_ow{}~???/@@@@@pJFM[/??????@ACG/??????????;??????????/??_ogKYr}{/?_ow\\NVb`O/@B@???????;??????????/{}rYKgo_??/O`bVN\\wo_?/???????@B@;?_OGCCAaYM/}BEIQayFAA/BKO_oM`PIE/____@@AAAA@B@;YaACCGO_??/AFyaQIEB}?/IP`Mo_OKB?/AAA@@?????%ESCAPE%   
            rem doing pentagram %pentagram%
            rem            echos %@CHAR[27]P0;8;1;10;0;2;20;0{ @???~}{wo_?/[MFJp@@@@@/GCA@??????/??????????;?_ow{}~???/@@@@@pJFM[/??????@ACG/??????????;??????????/??_ogKYr}{/?_ow\\NVb`O/@B@???????;??????????/{}rYKgo_??/O`bVN\\wo_?/???????@B@;?_OGCCAaYM/}BEIQayFAA/BKO_oM`PIE/____@@AAAA@B@;YaACCGO_??/AFyaQIEB}?/IP`Mo_OKB?/AAA@@?????@B@;?_OG[cIQaA/}@?_OJ{CAB/BMRaAAANqa/????@@AAAB@B@;aQIc[GO_??/BC{JO_?@}?/qNAAAaRMB?/AAA@@?????%ESCAPE%
            rem done pentagram %pentagram%
            REM not converted to size yet echo  { !???~}{wo_?/[MFJp@@@@@/GCA@??????/??????????;?_ow{}~???/@@@@@pJFM[/??????@ACG/??????????;??????????/??_ogKYr}{/?_ow\\NVb`O/@B@???????;??????????/{}rYKgo_??/O`bVN\\wo_?/???????@B@;?_OGCCAaYM/}BEIQayFAA/BKO_oM`PIE/____@@AAAA@B@;YaACCGO_??/AFyaQIEB}?/IP`Mo_OKB?/AAA@@?????@B@;?_OG[cIQaA/}@?_OJ{CAB/BMRaAAANqa/????@@AAAB@B@;aQIc[GO_??/BC{JO_?@}?/qNAAAaRMB?/AAA@@?????%ESCAPE%           
           
            set CREATE_PENTAGRAM=%@CHAR[27]P0;8;1;10;0;2;20;0{ @???~}{wo_?/[MFJp@@@@@/GCA@??????/??????????;?_ow{}~???/@@@@@pJFM[/??????@ACG/??????????;??????????/??_ogKYr}{/?_ow\\NVb`O/@B@???????;??????????/{}rYKgo_??/O`bVN\\wo_?/???????@B@;?_OGCCAaYM/}BEIQayFAA/BKO_oM`PIE/____@@AAAA@B@;YaACCGO_??/AFyaQIEB}?/IP`Mo_OKB?/AAA@@?????@B@;?_OG[cIQaA/}@?_OJ{CAB/BMRaAAANqa/????@@AAAB@B@;aQIc[GO_??/BC{JO_?@}?/qNAAAaRMB?/AAA@@?????%ESCAPE%
            echos %create_pentagram
            rem 🐛🐛🐛🐛🐛🐛🐛🐛🐛🐛🐛 BUG ALERT! Something breaks the pentagram, so we repeat this echos statement at the end of environm.btm to force it to exist in those situations where it breaks 🐛🐛🐛🐛🐛🐛🐛🐛🐛🐛🐛


   rem Combining custom characters to make custom emojis:  trumpet= *( announce )+    pentacle ,-   pentagram  ./
            set             EMOJI_TRUMPET=%@CHAR[55356]%@CHAR[57274]
            set   EMOJI_TRUMPET_COLORABLE=%ESCAPE%( @*(%ESCAPE%(B
            set     EMOJI_TRUMPET_FLIPPED=%ESCAPE%( @)+%ESCAPE%(B
            set            EMOJI_PENTACLE=%ESCAPE%( @,-%ESCAPE%(B
            set EMOJI_PENTAGRAM_UNCOLORED=%ESCAPE%( @./%ESCAPE%(B

   rem Adding fluorishes to our custom emoji:
            set           EMOJI_PENTAGRAM=%ANSI_RED%%ESCAPE( @./%ESCAPE%(B%ANSI_RESET%        %+ rem Make a red version of our pentagram emoji 
            set  EMOJI_PENTAGRAM_BLINKING=%blink_on%%EMOJI_PENTAGRAM%%blink_off%%ANSI_RESET%  %+ rem Now  add blinking  to our pentagram emoji 

   rem Adding aliases for our custom emoji:
            set                  PENTACLE=%EMOJI_PENTACLE%
            set                 PENTAGRAM=%EMOJI_PENTAGRAM%
            set        PENTAGRAM_BLINKING=%EMOJI_PENTAGRAM_BLINKING%
            set  EMOJI_BLINKING_PENTAGRAM=%EMOJI_PENTAGRAM_BLINKING%
            set        BLINKING_PENTAGRAM=%EMOJI_PENTAGRAM_BLINKING%
            set       UNCOLORED_PENTAGRAM=%EMOJI_PENTAGRAM_UNCOLORED%
            set       PENTAGRAM_UNCOLORED=%EMOJI_PENTAGRAM_UNCOLORED%
            set           PLAIN_PENTAGRAM=%EMOJI_PENTAGRAM_UNCOLORED%
            set           PENTAGRAM_PLAIN=%EMOJI_PENTAGRAM_UNCOLORED%
            rem EMOJIPENTAGRAMBLINKINGOLD=%@ANSI_FG[160,0,00]%reverse_on%%blink_on%%EMOJI_PENTAGRAM%%blink_off%%reverse_off%
            
    rem Various experiments:
            REM experiment: echo %ESCAPE%P0;8;1;10;0;2;20;0{ @???~}{wo_?/5#17;2;31;9;5#18;2;31;9;5#19;2;33;9;5#20;2;36;10;5#21;2;37;10;5#22;2;39;10;5#23;2;42;11;5#24;2;42;11;5#25;2;44;11;6#26;2;46;11;5#27;2;47;12;6#28;2;50;13;6#29;2;51;13;6#30;2;53;13;6#31;2;56;14;7#32;2;58;14;6#33;2;56;14;7#34;2;59;15;7#35;2;60;15;7#36;2;62;15;7#37;2;64;16;7#38;2;66;16;7#39;2;68;16;7#40;2;69;17;7#41;2;71;16;7#42;2;71;17;7#43;2;73;18;8#44;2;75;18;8#45;2;76;18;7#46;2;76;18;8#47;2;78;18;8#48;2;78;19;8#49;2;79;19;8#50;2;80;19;8#51;2;82;20;8#52;2;84;20;8#53;2;85;20;8#54;2;86;20;9#55;2;87;20;9#56;2;88;21;9#57;2;90;21;9#58;2;92;22;9#59;2;93;22;9#60;2;93;22;9#61;2;94;22;9#1~nFNFN!6BFFNFFn$#2?O#4G#22O#0G?!6C?G???O$#23??o#41_#12O!6?G#3G#15O#18O#4G_$#52!4?_#58_?o___#55O?_#45_#26O#2G$#29!5?O??G#30G#24G#36?O#32??_#7O$#59!6?_???O_$#10!6?G#21G#60OO??_$#51!6?O-#1~_#16B#60w`?A?O!4?P_#27@#0Aw$#3?O!4?O#52_!7?O#1@F$#0?F#29C#58C??@BF~F@@#17C#53C#28A#4C$#2?G#35_#53@#55GA!4?O#10O#13G#42??C#6_$#38??G#56A#25C#59@?Cg??A?_W#49_#8G$#40??O#49?A#47_!7?A#51?G#9O$#61!4?O#22G!6?O$#19!5?C#48C!6?G$#36!5?O#26_!5?C$#11!6?G#43O#57??g?A?B$#50!7?G#20???G#37_$#30!11?_$#54!11?C-#1~{ww_!6?_?ooo|~$#0?BC?O__!5?_??GA$#7??A#58@!4?@@???D#3G#2C$#22??@#18C!5?C#5_#27C?G#34?@$#44???A??@#4_#8__#46Q#16A#15O??A$#59!4?@C#28O!7?C$#19!4?G#49G!4?G#33O#55G?A$#54!4?C#52@?G?O#50?@#31A$#61!4?A#43A?O#57AA#47??@$#10!5?O#60G@??@G?A@$#13!6?A???C#56?C$#36!6?C#14C#17C#38G$#37!7?A#39G$#51!8?O-#1!8BAA!8B$#0!8?@@-%ESCAPE%\
            REM c:\cygwin\bin\printf.exe "\e( @\e[33m*(*(*(\e(B \e[36m This is an important message \e( @\e[33m)+ )+ )+ , , - - \e(B\e[m\n"

            rem a joke: ~DDD??~___~??~```??~KJ`??@ACWCA@??~```~??~___~


rem ———————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————


REM ANSI: testing —— and the magic way to know whether we are in insert mode or not:
        echos %@RANDCURSOR[]
        set          TEST_SCREEN_ALIGNMENT=%ESCAPE%#8    %+ rem "Screen alignment display"
        set ANSI_IDENTIFY_HOST_TO_TERMINAL=%ESCAPE%Z     %+ rem for me just returns "[?61;6;7;21;22;23;24;28;32;42c"
        set      IDENTIFY_HOST_TO_TERMINAL=%ESCAPE%Z     %+ rem for me just returns "[?61;6;7;21;22;23;24;28;32;42c"
        set        DEVICE_ATTRIBUTES_QUERY=%ESCAPE%Z     %+ rem for me just returns "[?61;6;7;21;22;23;24;28;32;42c"
        set   ANSI_DEVICE_ATTRIBUTES_QUERY=%ESCAPE%Z     %+ rem for me just returns "[?61;6;7;21;22;23;24;28;32;42c"
        set       ANSI_SOFT_TERMINAL_RESET=%ANSI_CSI%!p
        set            SOFT_TERMINAL_RESET=%ANSI_CSI%!p
        set                  SET_INSERT_ON=%ANSI_CSI%!p  %+ rem is really SOFT_TERMINAL_RESE but sets insert to on which is useful
        set             ANSI_SET_INSERT_ON=%ANSI_CSI%!p  %+ rem is really SOFT_TERMINAL_RESE but sets insert to on which is useful
        set            HARD_TERMINAL_RESET=%ESCAPE%c     %+ rem not recommended
        set       ANSI_HARD_TERMINAL_RESET=%ESCAPE%c     %+ rem not recommended

rem ———————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————

REM TODO try when have a keyboard with LED lights on it:
        rem DECKLHIM—Keyboard LED's Host Indicator Mode
        rem DECKLHIM controls the state of the keyboard LED's host indicator mode.
        rem Default: Reset.
        rem CSI ? 1 1 0 h -  set: keyboard led's host indicator mode
        rem CSI ? 1	1 0 l- Reset: keyboard LED's host indicator mode.
        rem DECLL controls keyboard LEDs independently of any keyboard state. The use of LEDs for this purpose conflicts with their use as keyboard state indicators. DECKLHIM selects a mode of how the keyboard LEDs are to be used: as keyboard indicators; or host indicators. If host indicators is selected, then the DECLL sequence can be used to control the keyboard LEDs.
        rem For DECLL to function, DECKLHIM must be set. See DECLL for the implications of using DECLL to control the keyboard LEDs independently of any keyboard state.


rem ———————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————

REM test strings that demonstrate all this ANSI functionality
        set ANSI_TEST_STRING=concealed:'%CONCEAL_ON%conceal%CONCEAL_off%' %ANSI_RED%R%ANSI_ORANGE%O%ANSI_YELLOW%Y%ANSI_GREEN%G%ANSI_CYAN%C%ANSI_BLUE%B%ANSI_MAGENTA%V%ANSI_WHITE% Hello, world. %BOLD%Bold!%BOLD_OFF% %FAINT%Faint%FAINT_OFF% %ITALICS%Italics%ITALIC_OFF% %UNDERLINE%underline%UNDERLINE_OFF% %OVERLINE%overline%OVERLINE_OFF% %DOUBLE_UNDERLINE%double_underline%DOUBLE_UNDERLINE_OFF% %REVERSE%reverse%REVERSE_OFF% %BLINK_SLOW%blink_slow%BLINK_SLOW_OFF% [non-blinking] %BLINK_FAST%blink_fast%BLINK_FAST_OFF% [non-blinking] %blink%blink_default%blink_off% [non-blinking] %STRIKETHROUGH%strikethrough%STRIKETHROUGH_OFF%
        set ANSI_TEST_STRING_2=%BIG_TEXT_LINE_1%big% %ANSI_RESET% Normal One%PENTAGRAM%
        set ANSI_TEST_STRING_3=%BIG_TEXT_LINE_2%big% %ANSI_RESET% Normal Two%PENTAGRAM%
        set ANSI_TEST_STRING_4=%WIDE_LINE%A wide line!%PENTAGRAM%

rem ———————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————

REM colors for our messaging system, in TCC command, ANSI_COLOR_{type} environment varaibles, and a hex code as well if used for custom cursor colors
        set COLOR_ADVICE=        color bright magenta on        black  %+ set ANSI_COLOR_ADVICE=%ANSI_RESET%%ANSI_BRIGHT_MAGENTA%%ANSI_BACKGROUND_BLACK%%+ 
        SET COLOR_ALARM=         color bright white   on        red    %+ set ANSI_COLOR_ALARM=%ANSI_RESET%%ANSI_BRIGHT_WHITE%%ANSI_BACKGROUND_RED%                         %+ set COLOR_ERROR=%COLOR_ALARM% %+ set ANSI_COLOR_ERROR=%ANSI_COLOR_ALARM% %+ set COLOR_FATAL_ERROR=%COLOR_ERROR% %+ SET ANSI_COLOR_FATAL_ERROR=%ANSI_COLOR_ALARM% %+ set COLOR_ERROR_FATAL=%COLOR_FATAL_ERROR% %+ set ANSI_COLOR_ERROR_FATAL=%ANSI_COLOR_FATAL_ERROR%
                                                                          set      COLOR_ALARM_HEX=FF0000
        SET COLOR_COMPLETION=    color bright white   on        green  %+ set ANSI_COLOR_COMPLETION=%ANSI_RESET%%ANSI_BRIGHT_WHITE%%ANSI_BACKGROUND_GREEN%                  %+ set COLOR_CELEBRATION=%COLOR_COMPLETION% %+ set ANSI_COLOR_CELEBRATION=%ANSI_COLOR_COMPLETION%
        SET COLOR_DEBUG=         color        green   on        black  %+ set ANSI_COLOR_DEBUG=%ANSI_RESET%%ANSI_BRIGHT_GREEN%%ANSI_BACKGROUND_BLACK%
        SET COLOR_IMPORTANT=     color bright cyan    on        black  %+ set ANSI_COLOR_IMPORTANT=%ANSI_RESET%%ANSI_BRIGHT_CYAN%%ANSI_BACKGROUND_BLACK%
        SET COLOR_IMPORTANT_LESS=color        cyan    on        black  %+ set ANSI_COLOR_IMPORTANT_LESS=%ANSI_RESET%%ANSI_CYAN%%ANSI_BACKGROUND_BLACK%                      %+ set COLOR_LESS_IMPORTANT=%COLOR_IMPORTANT_LESS% %+ set ANSI_COLOR_LESS_IMPORTANT=%ANSI_COLOR_IMPORTANT_LESS%
        SET COLOR_INPUT=         color bright white   on        black  %+ set ANSI_COLOR_INPUT=%ANSI_RESET%%ANSI_BRIGHT_WHITE%%ANSI_BACKGROUND_BLACK%                       %+ rem  had this set from inception til 2023
        SET COLOR_GREP=          color bright yellow  on        green  %+ set ANSI_COLOR_GREP=%ANSI_RESET%%ANSI_BRIGHT_YELLOW%%ANSI_BACKGROUND_GREEN%                      
        rem COLOR_LOGGING=       color bright blue    on        black  %+ set ANSI_COLOR_LOGGING=%ANSI_RESET%%ANSI_BRIGHT_BLUE%%ANSI_BACKGROUND_BLACK%                      %+ rem  For logging temp filenames to screen, etc.
        SET COLOR_LOGGING=       COLOR        cyan    on        red    %+ set ANSI_COLOR_LOGGING=%ANSI_RESET%%ANSI_CYAN%%ANSI_BACKGROUND_RED%%OVERSTRIKE_ON%%ITALICS_ON%    %+ rem  For logging temp filenames to screen, etc.
        SET COLOR_NORMAL=        color        white   on        black  %+ set ANSI_COLOR_NORMAL=%ANSI_RESET%
        SET COLOR_PAUSE=         color        cyan    on        black  %+ set ANSI_COLOR_PAUSE=%ANSI_RESET%%ANSI_CYAN%%ANSI_BACKGROUND_BLACK%
        rem COLOR_PROMPT=        color        yellow  on        black  %+ set ANSI_COLOR_PROMPT=%ANSI_RESET%%ANSI_YELLOW%%ANSI_BACKGROUND_BLACK%                            %+ rem tried changing to bright red on 20230605
        SET COLOR_PROMPT=        color bright red     on        black  %+ set ANSI_COLOR_PROMPT=%ANSI_RESET%%ANSI_BRIGHT_RED%%ANSI_BACKGROUND_BLACK%                        
        set COLOR_REMOVAL=       color bright red     on        black  %+ set ANSI_COLOR_REMOVAL=%ANSI_RESET%%ANSI_BRIGHT_RED%%ANSI_BACKGROUND_BLACK%                       
        SET COLOR_RUN=           color        yellow  on        black  %+ set ANSI_COLOR_RUN=%ANSI_RESET%%ANSI_YELLOW%%ANSI_BACKGROUND_BLACK%                               
        SET COLOR_SUCCESS=       color bright green   on        black  %+ set ANSI_COLOR_SUCCESS=%ANSI_RESET%%ANSI_BRIGHT_GREEN%%ANSI_BACKGROUND_BLACK%                     
                                                                          set      COLOR_SUCCESS_HEX=00FF00
        rem COLOR_SUBTLE=        color bright black   on        black  %+ set ANSI_COLOR_SUBTLE=%ANSI_RESET%%ANSI_BRIGHT_BLACK%%ANSI_BACKGROUND_BLACK%                      
        SET COLOR_SUBTLE=        color bright black   on        black  %+ set ANSI_COLOR_SUBTLE=%ANSI_RESET%%ANSI_BRIGHT_BLACK%                                             %+ rem 20240405 experimenting with leaving the default background collr in place for these
        SET COLOR_UNIMPORTANT=   color        blue    on        black  %+ set ANSI_COLOR_UNIMPORTANT=%ANSI_RESET%%ANSI_BLUE%%ANSI_BACKGROUND_BLACK%                         
        rem COLOR_WARNING=       color bright yellow  on        black  %+ set ANSI_COLOR_WARNING=%ANSI_RESET%%ANSI_BRIGHT_YELLOW%%ANSI_BACKGROUND_BLACK%                    %+ rem from inception 'til 20230529
        SET COLOR_WARNING=       color bright yellow  on        blue   %+ set ANSI_COLOR_WARNING=%ANSI_RESET%%ANSI_BRIGHT_YELLOW%%ANSI_BACKGROUND_BLUE%                     %+ rem 20230529-
        rem COLOR_WARNING_LESS=  color        yellow  on        black  %+ set ANSI_COLOR_WARNING_LESS=%ANSI_RESET%%ANSI_YELLOW%%ANSI_BACKGROUND_BLACK%                      %+ set COLOR_WARNING_SOFT=%COLOR_WARNING_LESS% %+ REM inception-20230605
        SET COLOR_WARNING_LESS=  color bright yellow  on        black  %+ set ANSI_COLOR_WARNING_LESS=%ANSI_RESET%%ANSI_BRIGHT_YELLOW%%ANSI_BACKGROUND_BLACK%               %+ set COLOR_WARNING_SOFT=%COLOR_WARNING_LESS% %+ set ANSI_COLOR_WARNING_SOFT=%ANSI_COLOR_WARNING_LESS% %+ REM 2020606-

rem ———————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————

rem 1) Custom colors for GREP   —— makes finding your matches a LOT useable
rem 2) Custom colors for HILITE —— a separate command for grep that simply highlights matches (and shows ALL lines), super useful

    REM original probably still good for Carolyn
            set GREP_COLOR_NORMAL=mt=1;33;42           %+  set GREP_COLOR_HILITE=1;41;37              %+ set GREP_COLOR=%GREP_COLOR_NORMAL%  %+ REM this one is deprecated

    REM adding blinking 20230802        
            set GREP_COLOR_NORMAL=mt=42;5;185          %+  set GREP_COLOR_HILITE=1;41;37              %+ set GREP_COLOR=%GREP_COLOR_NORMAL%  %+ REM this one is deprecated
            set GREP_COLORS_NORMAL=fn=1;33:ln=1;36;44  %+  set GREP_COLORS_HILITE=fn=1;34:ln=1;37;44  %+ set GREP_COLORS=%GREP_COLOR_NORMAL% %+ REM do NOT change set GREP_COLORS= to be GREP_COLORS_NORMAL with an S, those are the highlight colors actually

    REM Options we are no longer using:
            rem SET LC-ALL=C  ——— setting LC-ALL=C actually gives an 86% speed grep increase [as of 2015ish on computer Thailog] 
            rem                   at the expense of not being able to grep 2-byte-per-char type unicode files but in 2023/05/04 
            rem                   it was decided unicode is way too ubiquitous to skip proper processing, even for an 86% speedup

rem ———————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————

rem Function to strip ansi from strings —— regex to strip ansi is '(\x9B|\x1B\[)[0-?] *[ -\/]*[@-~]' 
rem This is loaded in our environm.btm as well, but we like to double-check when running set-ansi:
    call c:\bat\load-TCC-plugins.bat
    rem ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ does (1): plugin /L c:\bat\4wt.dll
    rem ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ does (2): plugin /L c:\bat\StripAnsi.dll —— which is the function we sometimes need, but don't have without the DLL:
    :StripAnsiTest
        if "%1" == "stripansitest" (
            echo.
            echos %ANSI_BLINK_ON%[Strip-ansi Test:]``
            echos %@STRIPANSI[%ANSI_DOUBLE_UNDERLINE%%ANSI_COLOR_MAGENTA%Hello %ANSI_COLOR_GREEN%world!]
            echos [/EndTest]%ANSI_BLINK_OFF% If "Hello World" isn't underlined, the test succeeded!
            echo.
        )

rem ———————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————

rem We're done!
        echos %@RANDCURSOR[]
        set      COLORS_HAVE_BEEN_SET=1     %+ rem "At first we were like..."
        set ANSI_COLORS_HAVE_BEEN_SET=1     %+ rem "....then we were like..."
        :AlreadyDone

rem ———————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————

rem If we're running our tests, do them now that we are done:
        if "%1" == "test" (
            echo.
            echo %ANSI_TEST_STRING_4%
            echo %ANSI_TEST_STRING%
            echo %ANSI_TEST_STRING_2%
            echo %ANSI_TEST_STRING_3%
            echo %newline%%newline%%emoji_nine_oclock%Normal line%ansi_reset%
            echo %WIDE_LINE%%emoji_nine_oclock%wide line%@ANSI_BG_RGB[0,0,0]
            call bigecho %emoji_nine_oclock%tall line
        )

rem ———————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————



REM  unexplored: Set text colour to index n in a 256-colour palette (e.g. \x1b[38;5;34m)


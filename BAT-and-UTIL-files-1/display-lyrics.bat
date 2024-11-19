@on break cancel
@Echo OFF

rem Validate environment:
        iff 1 ne %validated_display_lyrics% then
                call validate-environment-variables filemask_audio faint_on wrench blink_on blink_off faint_off cursor_reset ansi_color_important ansi_color_reset ansi_reset ANSI_ERASE_TO_END_OF_LINE check COLOR_SUCCESS_HEX COLOR_alarm_HEX
                call validate-is-function           set_cursor_color_by_hex ansi_move_to_col
                call validate-in-path               set-tmp-file eyed3 sed grep 
                set  validated_display_lyrics=1
        endiff
        
rem Deal with wildcard parameters by expanding them and recursing through them:
        iff "%@RegEx[[\*\?],%*]" eq "1" then
                for %%tmpfile in (%*) do (if "%@RegEx[%@EXT[%tmpfile],%filemask_audio]" eq "1"  (call display-lyrics "%tmpfile%"))
                goto :END
        endiff

rem Set our file to probe:
        set file_to_probe=%*

rem To retain control over our cursor color longer, we output to a temp file insted of STDOUT:
        (call set-tmp-file) >&>nul

        
rem Anti-hang-anxiety output while it runs:
        echos %faint_on%%wrench% %blink_on%Probing file for lyrics: %italics_on%%file_to_probe%...%italics_off%%blink_off%%faint_off%%@SET_cursor_color_by_hex[FFff00]

rem Probe the file for the lyrics:
        rem ((eyed3 %* |:u8 sed -e "s/Lyrics:/%ansi_color_important%Lyrics:/g" -e "s/UserTextFrame/%ANSI_COLOR_RESET%UserTextFrame/g"     -e "/Lyrics/,/UserTextFrame/ { /^Lyrics:/b; /^UserTextFrame/b; s/^/%ansi_color_important%LYRICS: / }"  |:u8 *grep LYRICS: |:u8 *grep -v UserTextFrame |:u8 *grep -v Lyrics:) |:u8 fast_cat ) |:u8 fast_cat
             (eyed3 %* |:u8 sed -e "s/Lyrics:/%ansi_color_important%Lyrics:/g" -e "s/UserTextFrame/%ANSI_COLOR_RESET%UserTextFrame/g"     -e "/Lyrics/,/UserTextFrame/ { /^Lyrics:/b; /^UserTextFrame/b; s/^/%ansi_color_important%LYRICS: / }"  |:u8 *grep LYRICS: |:u8 *grep -v UserTextFrame |:u8 *grep -v Lyrics: >:u8%tmpfile%) 

rem Figure out size/existence of our lyrics:
        set lyrics_size=%@FILESIZE[%tmpfile%]
        if not exist %tmpfile% set lyrics_size=0
        
rem Give gentle no-lyrics-found message which will remain on the screen if no lyrics are found, but be overwritten otherwise:
        echos %@ANSI_MOVE_TO_COL[0]%faint_on%
        iff 0 eq %lyrics_size then
                echos %@ANSI_CURSOR_COLOR_CHANGE_HEX[%COLOR_ALARM_HEX%]- No lyrics found. 
        else
                echos %@ANSI_CURSOR_COLOR_CHANGE_HEX[%COLOR_SUCCESS_HEX%]%ansi_color_success%%check% Lyrics found! %check%
        endiff
        echos                          %faint_off%%ansi_reset%%ANSI_ERASE_TO_END_OF_LINE%

rem Output the possibly-empty file, either showing its contents or leaving our no-lyrics-found message on the screen:
        iff 1 ne %DISPLAY_TAGS_PREFIX_NAME% then
                echos %@ANSI_MOVE_TO_COL[0]
                call fast_cat %tmpfile%
        else
                echos %@ANSI_MOVE_TO_COL[0]
               (call fast_cat %tmpfile% |:u8 insert-before-each-line "%ansi_color_magenta%%@UNQUOTE[%file_to_probe]%2$:%ansi_color_normal%" ) |:u8 fast_cat

        endiff
        
rem Reset the cursor:
        :END
        echos %ANSI_RESET%%CURSOR_RESET%



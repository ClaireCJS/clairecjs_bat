@Echo Off

rem Validate environment, but only once:
        iff 1 ne %ESET_VALIDATED% then
                call validate-environment-variables EMOJI_PENCIL ANSI_CURSOR_CHANGE_TO_BLOCK_BLINKING ANSI_COLOR_PROMPT ANSI_COLOR_NORMAL CURSOR_RESET
                call validate-is-function           CURSOR_COLOR
                call validate-in-path               eset
                set ESET_VALIDATED=1
        endiff

rem Emojify & colorfy the prompt, and change the cursor to the largest blinkiest bright yellow so we see it:
        echos %EMOJI_PENCIL%%@CURSOR_COLOR[yellow]%ANSI_CURSOR_CHANGE_TO_BLOCK_BLINKING%%ANSI_COLOR_PROMPT% ``

rem Gentle audio prompt —— the lowest audible beep and the shortest duration:
        call beep lowest 1

rem Do the actual eset command:
        *eset %*

rem Reset the color & cursor back to normal:
        echos %ANSI_COLOR_NORMAL%%CURSOR_RESET%


 
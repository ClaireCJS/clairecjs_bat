@loadbtm on
@echo off
@on break cancel


rem Validate environment just once:
        iff 1 ne %VALIDATED_GTCPSNG then
                call validate-in-path edit-currently-playing-attrib-with-automark
                set VALIDATED_GTCPSNG=1
        endiff


rem Disable opening the text editor automaticaly (but store previous value): {could probably use setlocal here but i just don't like it}
        set  EC_OPT_NOEDITOR_OLD=%EC_OPT_NOEDITOR%
        set  EC_OPT_NOEDITOR=1
        
rem Disable moving up the folder tree if in a playlist-determinant-specific or alternate-subdir such as "changer", "cheese", "channgerrecent", etc:
        set  EC_DO_NOT_GO_UP_1_DIR=1



rem Actually edit the currently-playing attrib.lst and/or [depending on options] just go to the folder of the currently-playing song:
        rem call edit-currently-playing-attrib-with-automark %* 
        call edit-currently-playing-attrib %*



rem Re-enable original setting for moving up the folder tree if in a playlist-determinant-specific or alternate-subdir such as "changer", "cheese", "channgerrecent", etc:
        set  EC_DO_NOT_GO_UP_1_DIR=0

rem Restore previous value for whether we opening the text editor automaticaly:
        set  EC_OPT_NOEDITOR=0
        set  EC_OPT_NOEDITOR=%EC_OPT_NOEDITOR_OLD%



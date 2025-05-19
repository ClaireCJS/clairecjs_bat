@loadbtm on
@Echo Off

rem side-note: worst-named BAT ever hahahahahhaha

rem Purpose:  To find the SRT of the currently-playing song, convert it to LRC, get it into the clipboard, and bring us to MiniLyrics window

rem Why? Minilyrics sometimes overrides local files with archive, so creating local transcriptions fail to override what MIniLyrics will pick up
rem      In that case, you gotta stupidly paste it in! 

rem [or go deleting in the archive, which is a bit too destructive and automatic for my taste, or maybe just too hard to implement]



rem Validate environment (once):
        iff "1" != "%validated_eccsrt2lrc2clip%" then        
                call validate-in-path               LaunchKey.exe sleep.bat activate setdos important.bat print-message.bat load_to_clipboard.py srt2lrc.py go-to-currently-playing-song-dir.bat 
                call validate-environment-variables ansi_colors_have_been_set
                set  validated_eccsrt2lrc2clip=1
        endiff


rem First figure out what song is playing and go there:
        call go-to-currently-playing-song-dir.bat 
        rem  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ sets (unquoted) CURRENT_SONG_FILENAME to full path of song
        rem  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ sets (unquoted) CURRENT_SONG_FILE to just the filename

rem Figure out the names of our files and make sure they are here:
        if not exist "%CURRENT_SONG_FILENAME%" .or. not exist "%CURRENT_SONG_FILE%" call validate-environment-variables CURRENT_SONG_FILENAME CURRENT_SONG_FILE

        set THE_SRT=%@UNQUOTE[%@NAME[%CURRENT_SONG_FILE%].srt]
        set THE_LRC=%@UNQUOTE[%@NAME[%CURRENT_SONG_FILE%].lrc]
        
        if not exist "%THE_SRT%" .and. not exist "%CURRENT_SONG_FILE%"  (goto :END)
        set  OUR_FILE=%THE_SRT%
        set USING_LRC=0
        iff not exist "%THE_SRT%" then
                set OUR_FILE=%THE_LRC%
                set USING_LRC=1
        endiff                
        if "1" == "%USING_LRC%" (goto :LRC_Exists_Already)

rem Then convert all SRTs to LRC:
        iff not exist *.srt then
                echo %ansi_color_error%No subtitle files to convert!%ansi_reset%
                goto :END
        endiff
        srt2lrc.py go %*


rem Make sure we actually made the LRC file:
        call validate-environment-variable OUR_FILE

rem If the LRC exists already, give it the proper treatment (open in editor, copy to clipboard)
        :LRC_Exists_Already
        rem This failed with unicode characters/emoji: type     "%THE_LRC%" >:u8 clip:
        rem So we compensated with manually doing it: rem %EDITOR% "%THE_LRC%"
        rem But then we wrote a program to load the clipboard properly
                load_to_clipboard.py "%THE_LRC%"


rem Let us know:
        call important "LRC copied to clipboard %blink_on%BUT COPY MANUALLY IF ANY SPECIAL CHARACTERS%blink_off%"
 
rem Front MiniLyrics so it's easier to find:
        activate "minilyrics"

rem Send Ctrl-E to MiniLyrics to open up the lyric editor:
        setdos /x-58
        LaunchKey ^e
        setdos /x0

rem Wait a couple second
        call sleep 2

rem Activate the lyrics editor
        activate "Lyrics Editor"

rem Send Ctrl-V to paste clipboard into there:
        setdos /x-58
        LaunchKey %escape_character%^e

rem Wait a second
        call sleep 1

rem Save the lyrics?
        LaunchKey %escape_character%^s
:END

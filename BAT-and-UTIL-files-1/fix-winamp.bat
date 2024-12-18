@on break cancel
@Echo off

REM AutoIt (freeware tool) can find these correct coordinates
REM ShoWin.exe tool can find these too, but it doesn't seem to count window decorations for minilyrics
REM     so 2020,0,600,600 becomes 2031,20,591,566 which is an offset of +11,+20,-9,-33 which is quite confusing





set ARG=%1
if "%1" eq "" .or. "%1" eq "alt" .or. "%1" eq "normal" (goto :%MachineName%)
               goto :%ARG%
			   goto :Default
               call warning "'%1' is not a label or valid parameter"
               goto :END


    ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


    :Default
        call warning "no default behavior defined!"
    goto :END

	:Demona
	:Demona20231101
        rem by 20241012 most of these were not working reight and removed just to prevent incorrect things from happening...
        call important_less "Fixing WinAmp window positions %blink_on%[CURRENTLY NEUTERED]%blink_off%"
        REM activate "minilyrics" POS=2025,10,590,590              
        REM activate "minilyrics" POS=-907,-1085,700,670
        REM winamp 5.9.2: activate "minilyrics"      pos=-1117,-1085,0700,670
        REM activate "Floating Lyrics" pos=00820,-1065,1500,250
        REM after switching window scaling to 150%... making upper-right 4K...and changing to modern skin.. which doesn't let you move it, only resize it
        rem activate "minilyrics"      pos=,,1120,1010
        rem activate "Floating Lyrics" pos=1075,-1070,2430,225
        rem activate ""       pos=01030,-0800,0410,410 
        rem activate "album art"       pos=01926,-0660,0410,410 %+ REM suddenly mid-day 2023/07/11 only this works
        rem activate "album art"       pos=01030,-0800,0410,410 %+ REM but then later it was right!
	goto :END

    :20230714
        echo %ansi_color_important_less%%emoji_hammer% Fixing WinAmp window positions...%emoji_hammer%
        REM activate "minilyrics" POS=2025,10,590,590              
        REM activate "minilyrics" POS=-907,-1085,700,670
        REM winamp 5.9.2:
            rem activate "minilyrics"             pos=-1117,-1085,0700,670   -- went bad around 2023/08/10
                rem 20241217: all these MiniLyrics-related ones are part of fix-minilyrics.bat now
                rem activate "minilyrics"             pos=-1059,-1085,0700,670
                rem :ctivate "Floating Lyrics"        pos=00820,-1065,1500,250
                rem activate "Floating Lyrics"        pos=00830,-1065,1560,250
                    activate "Winamp Playlist Editor" pos=-0130,-1072,0600,600
                    activate "album art"              pos=01941,-0695,0450,450

        rem vvvvvvvvvvvvvvvvvvvvvvvv *** normal album art ***
        rem if "alt" ne "%FIX_WINAMP_MODE%"                   (activate "album art" pos=1430,-800,410,410) %+ rem *** normal ***
        rem if "alt" eq "%FIX_WINAMP_MODE" .or. "alt" eq "%1" (activate "album art" pos=1926,-660,410,410) %+ rem *** alt ***
        rem                                                   (activate "album art" pos=1030,-800,410,410) %+ REM monitors: 4,2/3,1 20230715
        rem                                                    activate "album art" pos=1754,-798,410,410     %+ REM 20230717
        rem ^^^^^^^^^^^^^^^^^^^^^^^^ *** alt album art ***               suddenly mid-day 2023/07/11 only this works

            if "alt"    eq "%FIX_WINAMP_MODE" .or. "alt" eq "%1" (set FIX_WINAMP_MODE=alt)
            if "normal" eq "%1"                                  (set FIX_WINAMP_MODE=normal)

   
	goto :END

	:Thailog
    :VGA
    :13
        call important "Moving MiniLyrics to default display (the small VGA monitor)"
        :ctivate "minilyrics"  POS=2025,10,590,590              
        activate "minilyrics"  POS=2020, 0,600,600              
    goto :END
         
    :4K
    :55
        call important "Moving MiniLyrics to the 55'' 4K tv on the upper-right..."
        activate "minilyrics"  POS=2973,-2160,2115,2115         
    goto :END

    :52
        call important "Moving MiniLyrics to the 52'' 1080p TV by Carolyn's computer... Small, next to Winamp"
        activate "minilyrics"  POS=-42,-1080,725,725            
    goto :END

    ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::




:END
    rem Return focus
        rem nope keystack alt-shift-tab

    %COLOR_NORMAL%


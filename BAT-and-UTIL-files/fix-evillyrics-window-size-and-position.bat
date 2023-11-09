@Echo OFF

set WHAT_WE_ARE_MOVING=EvilLyrics
set WINDOW_NAME_MOVING=EvilLyrics



rem the freeware tool AutoIt can find these correct coordinates
rem our ShoWin.exe tool can find these too, but it doesn't seem to count window decorations for %WINDOW_NAME_MOVING%
rem     so 2020,0,600,600 becomes 2031,20,591,566 which means applying an offset of +11,+20,-9,-33 -- quite confusing




%COLOR_IMPORTANT_LESS%
if "%1" eq "" (goto :Default)
               goto :%1
    call warning   "'%1' is not a label or valid parameter."


    ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
    :VGA
    :13
        echo * Moving %WHAT_WE_ARE_MOVING% to default display (the small VGA monitor)
        activate "%WINDOW_NAME_MOVING%"  POS=1911,-9,818,618              
        goto :END
         
    :Default
    :4K
    :55
        echo * Moving %WHAT_WE_ARE_MOVING% to the 55" 4K tv on the upper-right...
        activate "%WINDOW_NAME_MOVING%"  POS=2090,-1080,780,1060          
        goto :END

    :52
        echo * Moving %WHAT_WE_ARE_MOVING% to the 52" 1080p TV by Carolyn's computer... Small, next to Winamp
        activate "%WINDOW_NAME_MOVING%"  POS=-686,-1076, 651,1006         
        goto :END
    ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::




:END
    %COLOR_NORMAL%

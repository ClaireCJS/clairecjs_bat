@loadbtm on
@Echo off
@on break cancel

:USAGE:  launch-monitor-to-react-after-program-closes videolan.vlc "call unpause"
:USAGE:   ...would run the command "call unpause" once the process VLCPlayer is no longer running

rem for YEARS:
        rem call helper-start %BAT%\monitor-to-react-after-program-closes.bat %1 %2 EXITAFTER

rem 2025/03/26 β:
        rem *start "monitor" /min %BAT%\monitor-to-react-after-program-closes.bat %1 %2 EXITAFTER

        rem set minmimize=1
        rem call helper-start %BAT%\monitor-to-react-after-program-closes.bat %1 %2 EXITAFTER
        rem set minmimize=0

        rem *start "monitor"   /MIN /POS=-1000,-1000,0,0 "C:\tcmd\TCC.EXE" C:\BAT\monitor-to-react-after-program-closes.bat vlc "call unpause" EXITAFTER

        rem set minimize=0
        rem call helper-start %BAT%\monitor-to-react-after-program-closes.bat %1 %2 EXITAFTER
        rem unset /q minimize

echo on
        rem *start "VLC Monitor" /MIN /POS=-1000,-1000,0,0 "C:\tcmd\TCC.EXE" C:\BAT\monitor-to-react-after-program-closes.bat vlc\.exe "call unpause" EXITAFTER
        rem *start "VLC Monitor" /MIN "C:\tcmd\TCC.EXE" C:\BAT\monitor-to-react-after-program-closes.bat vlc\.exe        "call unpause" EXITAFTER
            *start "VLC Monitor"      "C:\tcmd\TCC.EXE" C:\BAT\monitor-to-react-after-program-closes.bat "vlc.*vlc\.exe" "call unpause" EXITAFTER

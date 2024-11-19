@on break cancel
:::: USAGE:  launch-monitor-to-react-after-program-closes videolan.vlc "call unpause"
::::         ...would run the command "call unpause" once the process VLCPlayer is no longer running

call helper-start %BAT%\monitor-to-react-after-program-closes.bat %1 %2 EXITAFTER



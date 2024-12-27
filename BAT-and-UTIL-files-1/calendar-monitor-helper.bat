@Echo off
 on break cancel
 title Calendar Monitor
 python %BAT%\ingest_ics.py monitor
 if "%1" != "noexit" exit


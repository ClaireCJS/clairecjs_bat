@echo off
@on break cancel



rem Stop Last.FM:
        rem kill /f last*
        rem  call KillifRunning LASTFM~1 LASTFM~1
        taskend /f LASTFM~1




rem Start Last.FM:
        call lastfm-start



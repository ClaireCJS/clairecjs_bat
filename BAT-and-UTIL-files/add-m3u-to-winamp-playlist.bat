@echo off

::: This is for playing m3u winamp playlists.
::: These may have absolute-path filenames, i.e. d:\mp3\Metallica\Sucks.mp3
::: But on another computer, this drive is not D:!
::: This script pipes the playlist through my remap script, 
:::     which relies heavily on the %{REMAP%MACHINENAME} variable 
:::           (%REMAPSTORM, %REMAPMIST, etc, whaever %MACHINAME is set to...)
:::     which is defined in my environm.btm that sets the environment.

if "%1" eq "learned.m3u" (
    call warning "Are you sure?!?!?!"
    pause>nul
    pause>nul
)



set OLDPLAYLIST="%@FILENAME[%1]"
set NEWPLAYLIST="%@STRIP[%=",%TEMP\%OLDPLAYLIST]"
set WINAMP="%ProgramFiles%\WINAMP\WINAMP.EXE"
call validate-environment-variables OLDPLAYLIST WINAMP
call validate-in-path remap
call checktemp
echo %ANSI_COLOR_DEBUG%*** OLDPLAYLIST IS %OLDPLAYLIST,NEWPLAYLIST IS %NEWPLAYLIST


(type %1 |:u8 remap) >:u8%NEWPLAYLIST


%WINAMP% /ADD %NEWPLAYLIST
echo %ANSI_COLOR_SUCCESS%* Enqueued




goto :END




%COLOR_NORMAL%

@loadbtm on
@echo off
@on break cancel

::: This is for playing m3u winamp playlists.
::: These may have absolute-path filenames, i.e. d:\mp3\Metallica\Sucks.mp3
::: But on another computer, this drive is not D:!
::: This script pipes the playlist through my remap.pl script, 
:::     which relies heavily on the %{REMAP%MACHINENAME} variable 
:::           (%REMAPSTORM, %REMAPMIST, etc, whaever %MACHINAME is set to...)
:::     which is defined in my environm.btm that sets the environment.


rem CONFIGURATION:
        set PLAYER=vlc
        set PLAYER_PROCESS_REGEX=vlc


rem OVERRIDE PLAYLIST: If we run this in our *OFFICIAL* playlists folder, override to our PLAYLIST.bat instead:
        if "%@TRUENAME[.]" eq "%MP3OFFICIAL%\lists" (playlist.bat %*) %+ REM no "call" - we’re passing control directly over to this BAT instead!

rem OVERRIDE INTERFACE:
        if "%1" eq "winamp" (call play-m3u-with-winamp %* %+ goto :END)



rem WARN USER:
        @call warning "About to play %1 with vlcplayer"
        @pause



rem SETUP:
        call checktemp
        set OLDPLAYLIST="%@FILENAME[%1]"                     
        call less_important "OLDPLAYLIST IS “%OLDPLAYLIST%”, NEWPLAYLIST IS “%NEWPLAYLIST%”"
        set NEWPLAYLIST="%@STRIP[%=",%TEMP\%OLDPLAYLIST]"
        (type %OLDPLAYLIST% |:u8 remap.pl) >%NEWPLAYLIST


rem PLAY THE NEWLY-GENERATED PLAYLIST:
        (call paus)>nul                                                                               %+ REM pause music
        %color_important%
        type %newplaylist%
        %color_normal%
        call %PLAYER% %NEWPLAYLIST%                                                                   %+ REM run vlc player
echo        call launch-monitor-to-react-after-program-closes %PLAYER_PROCESS_REGEX% "call unpause"   %+ REM unpause music when done but give command line back
        call launch-monitor-to-react-after-program-closes %PLAYER_PROCESS_REGEX% "call unpause"   %+ REM unpause music when done but give command line back
        window restore                            


goto :END
        :Verify
                %COLOR_PROMPT% %+ echo Are you sure?!?!?! %+ pause>nul %+ pause>nul
        return
:END

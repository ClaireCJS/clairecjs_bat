@Echo off

:DESCRIPTION: Generate all audio playlists. This is a wrapper around our generate-filelists-by-attribute.pl script. 
:DESCRIPTION: index-mp3-helper is meant to be the called script, but sometimes during debugging we go straight to here for quicker testing of generate-filelists-by-attribute.pl

::::: SETUP:
    %COLOR_RUN%       
    timer /2 on

rem NO LONGER NECESSARY: ::::: PROCESS COMMAND-LINE OPTIONS:
rem NO LONGER NECESSARY:     if "%1" eq "/Q" .or. "%1" eq "quick" .or. "%1" eq "/quick" (goto :Quick)
rem NO LONGER NECESSARY: 
rem NO LONGER NECESSARY: ::::: FLUSH FILENAMES:
rem NO LONGER NECESSARY:     :COLOR_IMPORTANT% %+ echo Flushing mp3 collection 1 filenames...        :done in index-mp3-helper nowadays
rem NO LONGER NECESSARY:     :COLOR_RUN%       %+    dir /b /s %MP3    >%MP3%\filelist.txt           :done in index-mp3-helper nowadays
rem NO LONGER NECESSARY:     :COLOR_IMPORTANT% %+ echo Flushing mp3 collection 2 (new) filenames...  :no longer necessary as newmp3 is now within mp3
rem NO LONGER NECESSARY:     :COLOR_RUN%       %+    dir /b /s %NEWMP3 >nul                          :no longer necessary as newmp3 is now within mp3                
rem NO LONGER NECESSARY:     :COLOR_IMPORTANT% %+ echo Flushing video collection 1 filenames...      :no longer necessary as that indexing is now a separate process
rem NO LONGER NECESSARY:     :COLOR_RUN%       %+    dir /b /s %VID    >nul                          :no longer necessary as that indexing is now a separate process

::::: DO THE ACTUAL INDEX:
    :Quick
    call important "Running audio playlist generator"

	rem Perl -CSDA flag makes it process unicode but causes failures in tag reading and MAJOR slow down, so don't do that
    %COLOR_NORMAL%    
    perl %BAT%\generate-filelists-by-attribute.pl -g -i%BAT%\generate-filelists-by-attribute-audio.ini

::::: CLEANUP:
    %COLOR_RUN%       
    timer /2 off


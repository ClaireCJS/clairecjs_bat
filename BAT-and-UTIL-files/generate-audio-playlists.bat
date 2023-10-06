

@echo off

::::: Generate all audio playlists
::::: This bat simply does a dir /b of my indexable areas in order to flush the
::::: cache with the file locations so that generate-file lists-by-attribute
::::: runs a little faster.  The total time is probably still the same.

::::: SETUP:
    %COLOR_RUN%       %+ timer /2 

::::: PROCESS COMMAND-LINE OPTIONS:
    if "%1" eq "/Q" .or. "%1" eq "quick" .or. "%1" eq "/quick" (goto :Quick)

::::: FLUSH FILENAMES:
    :COLOR_IMPORTANT% %+ echo Flushing mp3 collection 1 filenames...        :done in index-mp3-helper nowadays
    :COLOR_RUN%       %+    dir /b /s %MP3    >%MP3%\filelist.txt           :done in index-mp3-helper nowadays
    :COLOR_IMPORTANT% %+ echo Flushing mp3 collection 2 (new) filenames...  :no longer necessary as newmp3 is now within mp3
    :COLOR_RUN%       %+    dir /b /s %NEWMP3 >nul                          :no longer necessary as newmp3 is now within mp3                
    :COLOR_IMPORTANT% %+ echo Flushing video collection 1 filenames...      :no longer necessary as that indexing is now a separate process
    :COLOR_RUN%       %+    dir /b /s %VID    >nul                          :no longer necessary as that indexing is now a separate process

::::: DO THE ACTUAL INDEX:
    :Quick
    %COLOR_IMPORTANT% %+ echo Running audio playlist generator...
	::::::::::::::::::::::::: perl -CSDA flag makes it process unicode but causes failures in tag reading and MAJOR slow down
    %COLOR_NORMAL%    %+ perl %BAT%\generate-filelists-by-attribute.pl -g -i%BAT%\generate-filelists-by-attribute-audio.ini

::::: CLEANUP:
    %COLOR_RUN%       %+ timer /2


@call list-flac-replaygain-tags.bat %*

rem OLD LEGACY WAY:
rem
rem @on break cancel
rem @echo off
rem 
rem ::::: This was 200 but it wasn't high enough! We were getting false negatives because 
rem ::::: the replaygain tags were beyond the 200th line. Setting it to 300 fixed it.
rem ::::: No wait. 400. lol.
rem set HEAD_LINES=400
rem 
rem 
rem if exist *.flac goto :yes
rem             %COLOR_IMPORTANT% %+ echo * No flac files exist. %+ %COLOR_NORMAL%
rem             goto :END
rem :yes
rem 
rem 
rem ::::This is faster but the output isn't as organized and it's easier to not notice a missing one:
rem ::metaflac --list *.flac|:u8gr REPLAYGAIN
rem 
rem for %tmpFile in (*.flac) do gosub processfile "%tmpFile"
rem    
rem goto :END
rem    
rem        :processFile [file]
rem    		%COLOR_IMPORTANT% %+ echo. %+ echo *** %file ***
rem    		%COLOR_RUN%       %+ (((metaflac   --list %file) |:u8 head -%HEAD_LINES%) |:u8 *grep -a -i REPLAYGAIN)
rem        :return
rem    
rem    
rem goto :END
rem 
rem 
rem 
rem 
rem 
rem 
rem :END
rem 

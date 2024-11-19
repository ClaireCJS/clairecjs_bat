@on break cancel
@echo off

::::: This was 200 but it wasn't high enough! We were getting false negatives because 
::::: the replaygain tags were beyond the 200th line. Setting it to 300 fixed it.
::::: No wait. 400. lol.
set HEAD_LINES=400


if exist *.flac goto :yes
            %COLOR_IMPORTANT% %+ echo * No flac files exist. %+ %COLOR_NORMAL%
            goto :END
:yes


::::This is faster but the output isn't as organized and it's easier to not notice a missing one:
::metaflac --list *.flac|:u8gr REPLAYGAIN

for %tmpFile in (*.flac) do gosub processfile "%tmpFile"
   
goto :END
   
       :processFile [file]
   		%COLOR_IMPORTANT% %+ echo. %+ echo *** %file ***
   		%COLOR_RUN%       %+ (((metaflac   --list %file) |:u8 head -%HEAD_LINES%) |:u8 *grep -a -i REPLAYGAIN)
       :return
   
   
goto :END






:END


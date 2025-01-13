@loadbtm on
@echo off
 on break cancel
if     exist  %1  goto :fine
if not isdir "%1" goto :nodir


:fine
       set               CHUNK=3313353708
 echo call backup-thing %CHUNK% %*
      call backup-thing %CHUNK% %*






:nodir
 echo ERROR: Folder "%1" does not exist.
goto :end



:end

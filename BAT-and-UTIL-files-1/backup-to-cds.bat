@echo off
 on break cancel
if exist %1 goto :fine
if not isdir "%1" goto :nodir

:fine
set CHUNK=732954624 
 echo call backup-thing 732954624 %*
      call backup-thing 732954624  %*






:nodir
echo ERROR: Folder "%1" does not exist.
goto :end

:end

@echo off
 on break cancel
if exist %1 goto :fine
if not isdir "%1" goto :nodir

:fine
set CHUNK=1175000000
 echo call backup-thing 1175000000 %*
      call backup-thing 1175000000 %*






:nodir
echo ERROR: Folder "%1" does not exist.
goto :end

:end

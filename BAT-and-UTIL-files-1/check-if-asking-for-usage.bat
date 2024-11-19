@Echo OFF
 on break cancel

:USAGE: call check-if-asking-for-usage %*
:DESCRIPTION: Set the flag ASKING_FOR_USAGE=1 if they are passing any parameter that seems to ask for usage
:DESCRIPTION: Note that this will not cover the case of passing no parameters at all, by design.

set ASKING_FOR_USAGE=0

if "%1" eq  "/h"    (set ASKING_FOR_USAGE=1)
if "%1" eq  "-h"    (set ASKING_FOR_USAGE=1)
if "%1" eq "--h"    (set ASKING_FOR_USAGE=1)
if "%1" eq  "/?"    (set ASKING_FOR_USAGE=1)
if "%1" eq  "-?"    (set ASKING_FOR_USAGE=1)
if "%1" eq "--?"    (set ASKING_FOR_USAGE=1)
if "%1" eq  "/help" (set ASKING_FOR_USAGE=1)
if "%1" eq  "-help" (set ASKING_FOR_USAGE=1)
if "%1" eq "--help" (set ASKING_FOR_USAGE=1)

set RAMDISK_DRIVE=%1
if "%@READY[%RAMDISK_DRIVE%]" eq "0" (color bright green on blue %+ echo * WARNING: DRIVE %RAMDISK_DRIVE%: IS NOT ACTUALLY READY?!?! %+ color white on black)
        
        call imdisk.bat -d -m %RAMDISK_DRIVE%:
        call imdisk.bat -D -m %RAMDISK_DRIVE%:

if "1"           eq "%EXITAFTER%" exit
if "%@UPPER[%1]" eq  "EXITAFTER"  exit
if "%@UPPER[%2]" eq  "EXITAFTER"  exit
if "%@UPPER[%3]" eq  "EXITAFTER"  exit

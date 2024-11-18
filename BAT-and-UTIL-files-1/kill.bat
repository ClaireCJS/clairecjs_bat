@Echo OFF

                 set TARGET=%1$
if "%1" eq "/f" (set TARGET=%2$)

if "%target%" eq "bandicam" (set TARGET=bdcam)

echo taskend /f %TARGET%
     taskend /f %TARGET%

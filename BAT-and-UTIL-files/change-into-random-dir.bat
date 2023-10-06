@Echo off

call fixtmp>nul

dir /ba:d >:u8 dir.txt

rem :set randir=%@EXECSTR[dir /ba:d|randline]
rem :set randir=%@EXECSTR[@randline<dir.txt]
rem >:u8 run.bat
rem echos cd ">:u8 run.bat

set MAKE_IT_CD=1
call randline.pl<dir.txt >>:u8 run.bat
set MAKE_IT_CD=0

if not exist run.bat (pause)
call run.bat
*del ..\run.bat>nul


rem %COLOR_IMPORTANT% %+ echo * It's %RANDIR% %+ %COLOR_NORMAL%
rem *del dir.txt
rem :if not isdir "%randir" goto :nodir
rem %COLOR_DEBUG% %+ echo cd "%randir" %+ %COLOR_NORMAL%
rem :cd "%randir"
rem unset /q randir

goto :END

            :nodir
                %COLOR_WARNING% %+ echo. %+ echo. %+ echo. %+ echo. %+ echo. %+ echo. %+ echo. %+ echo Sorry, no directories here! %+ %COLOR_NORMAL%
            goto :END

:END
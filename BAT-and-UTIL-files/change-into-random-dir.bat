@Echo off

call fixtmp>nul

call set-tmpfile
set RANDIR_SCRIPT_TO_RUN=%[tmpfile].bat

dir /ba:d >:u8 dir.txt

rem :set randir=%@EXECSTR[dir /ba:d|randline]
rem :set randir=%@EXECSTR[@randline<dir.txt]
rem >:u8 %RANDIR_SCRIPT_TO_RUN%
rem echos cd ">:u8 %RANDIR_SCRIPT_TO_RUN%

set MAKE_IT_CD=1
    call randline.pl<dir.txt >>:u8 %RANDIR_SCRIPT_TO_RUN%
set MAKE_IT_CD=0

if not exist %RANDIR_SCRIPT_TO_RUN% (pause)
call         %RANDIR_SCRIPT_TO_RUN%
*del         %RANDIR_SCRIPT_TO_RUN%>nul


rem %COLOR_IMPORTANT% %+ echo * It's %RANDIR% %+ %COLOR_NORMAL%
rem *del dir.txt
rem :if not isdir "%randir" goto :nodir
rem %COLOR_DEBUG% %+ echo cd "%randir" %+ %COLOR_NORMAL%
rem :cd "%randir"
rem unset /q randir

goto :END

            :nodir
                echo. %+ echo. %+ echo. %+ echo. %+ echo. %+ echo. %+ echo. %+ call warning "Sorry, no directories here!"
            goto :END

:END
@Echo OFF

::::: PRE-SETUP:
    pushd . 
    call now                                            %+ REM .//sets %YYYYMMDD for use in %OUR_END_DATE%

::::: CONSTANTS (1):
    SET WHAT_WE_ARE_TRACKING=something
    set WHAT_WE_ARE_TRACKING_UNITS_USED=things          %+ REM //values such as "$" "lbs"
    set OUR_START_DATE=%YYYYMMDD%                       %+ REM //probably should be hard-coded in most situations
    SET DEFAULT_START_DATE_CLAIRE=20120301              %+ REM //when Claire  runs it, it's this start date
    SET DEFAULT_START_DATE_CAROLYN=20120301             %+ REM //when Carolyn runs it, it's this start date
    set OUR_DIR=%PUBCL%\delme                           %+ if not isdir "%OUR_DIR%" (mkdir /s "%OUR_DIR%")
    set TRACKING_FILE=%OUR_DIR%\graph-data-%WHAT_WE_ARE_TRACKING%.dat
    set OUR_FILE=%TRACKING_FILE%    
    call validate-environment-variables OUR_DIR USERNAME
    set TARGET_GRAPH_DIR=%OUR_DIR%\%WHAT_WE_ARE_TRACKING%-graphs 
    set OUR_NAME=%USERNAME%                             %+ if "%OUR_NAME%" eq "claire" (set OUR_NAME=claire)
    if "%1%" eq "DEFINE_CONSTANTS_ONLY" (goto :END_DEFINING_CONSTANTS)

::::: SETUP:
    cls
    "%OUR_DIR%\"
    set OUR_END_DATE=%YYYY%%MM%%@EVAL[DD+1]
    %color_debug% %+ echo * OUR_NAME is %OUR_NAME%
    if not exist "%TARGET_GRAPH_DIR%" (mkdir /s "%TARGET_GRAPH_DIR%")

::::: DISPLAY THE VALUES (our grep has grep coloring, which we like to remove)
    (grep -i %KNOWN_NAME% "%TRACKING_FILE%"|:u8strip-ansi)

::::: CONSTANTS:
    set     TARGET=%TARGET_GRAPH_DIR%\%WHAT_WE_ARE_TRACKING%-graph-%OUR_NAME-%_DATETIME.png
    set TEMPOUTPUT=_tempoutput-%_PID.txt
    set LINE_COLOR=red              %+ REM color for Claire

::::: PARTNER VARIATIONS:
     if "%OUR_NAME%" eq "carolyn"                     (set OUR_START_DATE=%DEFAULT_START_DATE_CAROLYN%  %+  LINE_COLOR=purple  )  %+ REM //Carolyn likes purple better! Keep this!
    :if "%OUR_NAME%" eq "claire" .and. "%1" ne "full" (set OUR_START_DATE=%DEFAULT_START_DATE_CLAIRE%)  %+ REM //EXAMPLE of overriding per person


::::: COMMAND-LINE VARIATIONS: GIVE START DATE:
    if "%1" ne "" .and. "%1" ne "full" (set OUR_START_DATE=%1)


::::: SORT OUT ONE PERSON'S WEIGHINGS INTO A TEMP FILE:5
     head -1            "%OUR_FILE%"   >%TEMPOUTPUT%
    (grep -i %OUR_NAME% "%OUR_FILE%") >>%TEMPOUTPUT%

:pause 

::::: GNUPLOT STUFF:
        :: set term pngcairo is what antialiases things, but also makes the dotted ine background less intense, and the font goofier
      gnuplot << eor
           set term pngcairo
           set terminal png size 1900,1060 font "Helvetica,30"
           set output '%TARGET%'
           set style data line
           set datafile separator ","
           set xlabel "date"
           set ylabel "%WHAT_WE_ARE_TRACKING% (%WHAT_WE_ARE_TRACKING_UNITS_USED%)"
           set xdata time
           #et xtics format "%%b\n%%Y"
           set xtics format "%%b %%d\n%%Y"
           set timefmt "%%Y%%m%%d%%H%%M"
           set xrange ["%OUR_START_DATE%":"%OUR_END_DATE%"]
           #et xrange [%OUR_START_DATE%:%OUR_END_DATE%]
           set title "%KNOWNNAME%'s %WHAT_WE_ARE_TRACKING% history"
           set grid
           plot "%TEMPOUTPUT%" using 2:3 lt rgb "%LINE_COLOR%" title "%KNOWNNAME%'s %WHAT_WE_ARE_TRACKING%" 
eor
REM        >>>>>>>>>>>>>>>>>>>>>>>>>



::::: DONE
    :END
    echo yr|cp "%TARGET%" "c:\%WHAT_WE_ARE_TRACKING%.last-graph.png"
    call killIfRunning i_view32 i_view32  %+ REM kill image viewer so that when we view the newly-generated image, we don't get confused
    if exist "%TARGET%" .and. %@FILESIZE["%TARGET%"] gt 0 ("%TARGET%") %+ REM view newly created graph with i_view32 -- unless it's a 0-byte file, then don't do that
    if exist %TEMPOUTPUT% (*del /q %TEMPOUTPUT%)                       %+ REM get rid of our temporary file
    popd

:END_DEFINING_CONSTANTS
:END_ERROR

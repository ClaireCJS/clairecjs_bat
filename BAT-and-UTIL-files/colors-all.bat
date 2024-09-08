@Echo OFF


for %%fg in (0 8 4 12) (for /L %%bg in (0,1,15) (gosub cell %bg% %fg% %+ gosub cell %bg% %@EVAL[%fg%+1] %+ gosub cell %bg% %@EVAL[%fg%+2] %+ gosub cell %bg% %@EVAL[%fg%+3]%+ echo.) %+ echo.)
for %%bg in (0 8 4 12) gosub do2rows %bg%



goto :END

    :do2rows [bg]
        for %%fg in (0 1 2 3 4 5 6 7) (gosub do1Row %fg% %bg% %+ gosub do1Row %@EVAL[%fg%+8] %bg%)
        echo.
    return

    :do1row [fg bg]
        gosub cell %fg%        %bg%    
        gosub cell %fg% %@EVAL[%bg%+1] 
        gosub cell %fg% %@EVAL[%bg%+2] 
        gosub cell %fg% %@EVAL[%bg%+3] 
        echo.
    return

    :cell [fg bg]
        color %fg%  on %bg%  %+ echos    *** {%@FORMAT[02,%FG%],%@FORMAT[02,%BG%]} ***   `` 
        color white on black %+ echos  ``
    return


:END

call colortool -c


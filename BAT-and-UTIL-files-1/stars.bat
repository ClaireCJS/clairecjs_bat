@loadBTM on
@Echo OFF
@on break cancel

:DESCRIPTION: to display the various %STAR% values we have in our environment


rem At least validate the ones we know of at the time of writing this script
        iff "1" != "%validated_stars_bat%" then
                call validate-environment-variables star star1 star2 star3 star4 star5 star6 star7 star8 star9 star10 star_glitch
                set  validated_stars_bat=1
        endiff

rem MAIN:
        echo.
        for %%starnum in ("" 1 2 3 4 5 6 7 8 9 10) gosub display_star %starnum%
        goto :END


:display_star [starnum]
        rem     echo  %%Star%@UNQUOTE[%starnum%]%%%tab%= %[star%@UNQUOTE[%starnum%]]
        call bigecho "`%%`Star%@UNQUOTE[%starnum%]`%%`%@ANSI_MOVE_TO_COL[10]= %[star%@UNQUOTE[%starnum%]]"
return


:END


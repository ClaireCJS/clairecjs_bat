@Echo OFF
@on break cancel
:why? setlocal
    set EXTRA_NAME=%*                     %+ rem BUT THIS NEXT GETS PASSED lol
    rn "%@EXECSTR[d/odt/b|:u8tail -1]" 
:endlocal

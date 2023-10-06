@Echo OFF
:why? setlocal
    set EXTRA_NAME=%*                     %+ rem BUT THIS NEXT GETS PASSED lol
    rn "%@EXECSTR[d/odt/b|tail -1]" 
:endlocal

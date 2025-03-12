@Echo off

rem Disambiguation/overloading of “as” command once we ended up needing to use the unis “as.exe” after using “as.bat” for 10+ yrs:

iff "%username%" == "claire" .or. "%username%" == "carolyn" then
        call as-user.bat %*
else
        as.exe %*
endiff


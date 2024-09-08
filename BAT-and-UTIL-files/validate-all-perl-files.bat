@Echo OFF

call validate-in-path perl errorlevel.bat important.bat

call warning "This validates our per files, but you have to actually read over the screen for errors, as Perl -C doesn't return an errorlevel if compilation failed. Sorry!"
pause


for %pl in (*.pl;*.pm) gosub ValidatePerl "%pl"
goto :END


    :ValidatePerl [perl_file_to_validate]
        echo.
        echo.
        call important "Validating Perl file '%italics_on%%perl_file_to_validate%%italics_off%'"
        perl -c %perl_file_to_validate%
        call errorlevel "File failed perl -c validation" %+ REM well this was pointless. perl -c doesn't return an errorlevel if compilation failed. oh well!
    return



:END
@Echo OFF

:: one thing we have to do is remove "&" from the name of the current folder, because "&" messes up the query string

call google wikipedia %@REPLACE[&,,%@NAME[%_CWD]]


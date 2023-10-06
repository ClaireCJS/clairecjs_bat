@Echo OFF
:call zip-helper-zip-all-of-extension-into-separate-zips EXE
:call zip-all-folders 
set OLDVAL=%AUTO_DEL_DIR%
    set AUTO_DEL_DIR=1
    for %e in (*.exe) do call zip "%e"
set AUTO_DEL_DIR=%OLDVAL%



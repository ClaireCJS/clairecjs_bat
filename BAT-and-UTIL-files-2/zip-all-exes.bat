@Echo OFF
 on break cancel
:call zip-helper-zip-all-of-extension-into-separate-zips EXE
:call zip-all-folders 

for %e in (*.exe) do call zip "%e"




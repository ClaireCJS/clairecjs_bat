@Echo OFF
for /a:d %mydir in ([0-9]*-*) do (echos %@RANDFG[] %+ ren "%mydir%" "%@REPLACE[-,_,%mydir%]")

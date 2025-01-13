@loadbtm on
@Echo OFF
@on break cancel

set MSG=%@UNQUOTE[%1]
if "%1" == "" set MSG=*** Success!!! ***

 call print-message success "%MSG%" %2$


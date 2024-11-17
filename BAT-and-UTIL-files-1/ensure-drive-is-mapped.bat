@Echo OFF

if "%1" eq ""             (call error      "Need to pass a drive letter to %0!")
if  "1" ne "%@READY[%1%]" (call map-drives %1%                                 )


@Echo OFF

set        MZBFN_PARAM1=%@UNQUOTE[%1]
if "" eq "%MZBFN_PARAM1%" (call fatal_error "Must provide filename to create!")
if exist "%MZBFN_PARAM1%" (call       error "Cannot create zero byte file named '%emphasis%%MZBFN_PARAM1%%deemphasis%%ansi_color_fatal_error%' because it already exists")
        >"%MZBFN_PARAM1%"


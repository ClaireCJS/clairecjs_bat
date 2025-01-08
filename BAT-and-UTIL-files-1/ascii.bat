@Echo Off

:USAGE: ascii {beginning_ascii_code} {ending_ascii_code} {“clean”}

set beg=%1
set end=%2

if  ""  == "%beg%" set beg=1
if  ""  == "%end%" set end=1
if "%3" != "clean" set clean_ascii=0
if "%3" == "clean" set clean_ascii=1

do ii=%beg% to %end% by 1 ( 
        if  "0" == "%clean_ascii%" echos %@RANDFG_soft[]
        set  gout=%@EXECSTR[grep "\[%ii\]" c:\bat\emoji.env]
        set   msg=%%%%%%%%%%%%%%%%@char[%ii%]: %@CHAR[%ii] %@if["" ne "%gout%",%tab%used%underline_off%: %@UNQUOTE[%@ReReplace[[\s\t],,"%gout%"]],]
        if "0" != "%clean_ascii%"  (
                echo %@unquote[%@stripansi["%msg%"]]
        ) else (
                echo %big_top%%@unquote[%@stripansi["%msg%"]]
                echo %big_bot%%@unquote[%@stripansi["%msg%"]]
        )
)

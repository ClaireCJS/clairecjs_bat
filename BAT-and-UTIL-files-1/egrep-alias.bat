@Echo off

iff not defined egrep then
                                set  egrep=%[UTIL]\egrep32.exe
        if not exist "%egrep%" (set  egrep=c:\util\egrep32.exe)
        if not exist "%egrep%" (set  egrep=c:\cygwin\bin\egrep.exe)
        if not exist "%egrep%" (call fatal_error "%italics_on%egrep.exe%italics_off% cannot be located")
endiff

%EGREP% %*


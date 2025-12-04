@Echo OFF


rem Fetch parameters:
        set PARAM1=%@ReReplace[\\$,,%@UNQUOTE[%1]]                                      %+ rem Remove trailing backslash so %@NAME[] function works the way we want it to
        set PARAM2=%@UNQUOTE[%2]


rem Validate environment once per session:
        iff "1" != "%validated_cpdir%" then
                call validate-in-path fatal_error ask-command
                set  validated_cpdir=1
        endiff


rem Validate usage:
        if "" != "%PARAM2%" (call fatal_error "cpdir works with one and only 1 parameter, the folder name" %+ goto :END)


rem Create command:
        set CPDIR_COMMAND=copy /s “%PARAM1%” “%@NAME[%PARAM1%]”

rem Ask to do it:
        call ask-command %CPDIR_COMMAND%




:END
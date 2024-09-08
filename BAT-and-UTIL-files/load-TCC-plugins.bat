@Echo OFF
 set PLUGIN_TCC_BASE=%BAT%
 path=%path%;%PLUGIN_TCC_BASE%

        if not defined       PLUGIN_4WT_LOADED (set       PLUGIN_4WT_LOADED=0)
        if not defined PLUGIN_STRIPANSI_LOADED (set PLUGIN_STRIPANSI_LOADED=0)

        set PLUGIN_4WT=%PLUGIN_TCC_BASE%\4wt.dll
        set PLUGIN_STRIPANSI=%PLUGIN_TCC_BASE%\StripAnsi.dll 
        call validate-environment-variables PLUGIN_TCC_BASE PLUGIN_4WT PLUGIN_STRIPANSI

        rem We've moved away from using our PLUGIN_xxx_LOADED environment variables as a testing method. More of tracking only.
        rem Instead, devise a negative test to check for each plugin not being loaded
        if "%_HWNDWT" == "" (
            call print-if-debug "Loading TCC plugin: %italics_on%4WT%italics_off%"
            set PLUGIN_4WT_LOADED=1
            plugin /l %PLUGIN_4WT% >&>nul
        )
   
        if not plugin stripansi (
            call print-if-debug "Loading TCC plugin: %italics_on%StripAnsi%italics_off%"
            set PLUGIN_STRIPANSI_LOADED=1
            plugin /l %PLUGIN_STRIPANSI% >nul
        )

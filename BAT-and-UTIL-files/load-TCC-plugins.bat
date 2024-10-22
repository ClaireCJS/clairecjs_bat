@Echo Off

 set PLUGIN_TCC_BASE=%BAT%

 rem ^^^^ If this is a folder already in our path, then we don't need this next line:
 rem path=%path%;%PLUGIN_TCC_BASE%

        if not defined       PLUGIN_4WT_LOADED (set       PLUGIN_4WT_LOADED=0)
        if not defined PLUGIN_STRIPANSI_LOADED (set PLUGIN_STRIPANSI_LOADED=0)

        set PLUGIN_4WT=%PLUGIN_TCC_BASE%\4wt.dll
        set PLUGIN_STRIPANSI=%PLUGIN_TCC_BASE%\StripAnsi.dll 
        call validate-environment-variables PLUGIN_TCC_BASE PLUGIN_4WT PLUGIN_STRIPANSI

        rem We've moved away from using our PLUGIN_xxx_LOADED environment variables as a testing method. More of tracking only.
        rem Instead, devise a negative test to check for each plugin not being loaded
        iff "%_HWNDWT" == ""  .or. "%1" == "force" then
            call print-if-debug "Loading TCC plugin: %italics_on%4WT%italics_off%"
            set PLUGIN_4WT_LOADED=1
            if isplugin 4WT .or. "%1" == "force" (plugin /u %PLUGIN_4WT% >&>nul)
                                                  plugin /l %PLUGIN_4WT% >&>nul
        endiff
   
        iff not plugin stripansi .or. "%1" == "force" then
            call print-if-debug "Loading TCC plugin: %italics_on%StripAnsi%italics_off%"
            set PLUGIN_STRIPANSI_LOADED=1
            if isplugin stripansi .or. "%1" == "force" (plugin /u %PLUGIN_STRIPANSI% >nul)
                                                        plugin /l %PLUGIN_STRIPANSI% >nul

            rem Define an alias for %@STRIPANSI because of how often we incorrectly call it:
            rem Astoundindly, this has proven non-interoprable: 
            rem     function STRIP_ANSI=`%@STRIPANSI[%1$]`
            rem So instead, let's warn them that this is wrong:
            function STRIP_ANSI=`ERROR: @STRIP_ANSI CALLED WITH %1$ -- NEED TO USE %%@STRIPANSI[%1$] instead`
        endiff

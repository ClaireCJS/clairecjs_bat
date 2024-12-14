@on break cancel
@Echo OFF

rem Make sure %BAT% is defined, in case we are manually running this early:
        iff not defined PLUGIN_TCC_BASE then
                iff not defined BAT then
                        set PLUGIN_TCC_BASE=c:\bat\
                else
                        set PLUGIN_TCC_BASE=%BAT%
                endiff
endiff
rem ^^^^ If PLUGIN_TCC_BASE is a folder already in our path, then we don't need to do anything
rem But if it isn't, there is a line we need to uncomment later, look for it...




rem Reset environment variables tracking if plugins are loaded:
        if not defined       PLUGIN_4WT_LOADED (set        PLUGIN_4WT_LOADED=0)
        if not defined PLUGIN_STRIPANSI_LOADED (set  PLUGIN_STRIPANSI_LOADED=0)


rem Make sure our path is set:
        if  1  ne  %PATH_GENERATED             (call c:\bat\setpath.bat)
        rem If PLUGIN_TCC_BASE is a folder already in our path, then we don't need to do anything
        rem But if it isn't, we also need to do this:
        rem path=%path%;%PLUGIN_TCC_BASE%

rem Set our plugin file locations:
        set PLUGIN_4WT=%PLUGIN_TCC_BASE%\4wt.dll
        set PLUGIN_STRIPANSI=%PLUGIN_TCC_BASE%\StripAnsi.dll 

rem Verify the plugin files exist:
        call validate-environment-variables PLUGIN_TCC_BASE PLUGIN_4WT PLUGIN_STRIPANSI
        call validate-plugin StripANSI



rem ************ LOAD EACH PLUGIN: ************
rem ************ LOAD EACH PLUGIN: ************
rem ************ LOAD EACH PLUGIN: ************
rem ************ LOAD EACH PLUGIN: ************
rem ************ LOAD EACH PLUGIN: ************


rem         We've moved away from using our PLUGIN_xxx_LOADED environment variables as a testing method. 
rem         Those environment variables are for tracking only, and not guaranteed to be accurate.      [though in practice they willb e]

rem         Instead, we devise a test that relies on plugin functionality to validate each plugin as being NOT loaded, prior to loading


rem                 For each plugin, we check it's functionality via a test that only works if it is loaded
rem                 We only proceed if that test fails, or if the "force" option was added ("call load-tcc-plugins FORCE")
rem                 We then print a debug message saying that we're about to laod it
rem                 We then set our environment variable tracking that we've done this
rem                 We then double-check if it is loaded with the "if isplugin" native TCC functionality (or if the "force" option was added)
rem                 At this point we've self-tested AND used TCC's test, so the dang thing should defniitely be unloaded
rem                 But if it's not, we unload it
rem                 And the, finally, do we actually do what this whole script is about: Loading the plugin.


        rem 4WT plugin:
                iff "%_HWNDWT" == ""  .or. "%1" == "force" then
                    call print-if-debug "Loading TCC plugin: %italics_on%4WT%italics_off%"
                    set PLUGIN_4WT_LOADED=1
                    if isplugin 4WT .or. "%1" == "force" (plugin /u %PLUGIN_4WT% >&>nul)
                                                          plugin /l %PLUGIN_4WT% >&>nul
                endiff


        
        rem StripAnsi plugin:
                iff not plugin stripansi .or. "%1" == "force" then
                    call print-if-debug "Loading TCC plugin: %italics_on%StripAnsi%italics_off%"
                    set PLUGIN_STRIPANSI_LOADED=1
                    if isplugin stripansi .or. "%1" == "force" (plugin /u %PLUGIN_STRIPANSI% >nul)
                                                                plugin /l %PLUGIN_STRIPANSI% >nul

                    rem Define an alias for %@STRIPANSI because of how often we incorrectly call it:
                    rem Astoundindly, this has not worked:
                    rem     function STRIP_ANSI=`%@STRIPANSI[%1$]`
                    rem So instead, let's warn them that this is wrong:
                            function STRIP_ANSI=`echo ERROR: @STRIP_ANSI CALLED WITH %1$ -- NEED TO USE @STRIPANSI[%1$] without underscore instead %+ *pause`
                endiff

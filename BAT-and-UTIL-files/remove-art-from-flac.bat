@Echo On

rem This is achieved by the framework of add-art-to-flac-helper.bat, except with a signal to remove instead of add:

rem We call add-art-to-flac-helper instead of add-art-to-flac because the full add process requires removing first
rem which means that adding-without-removing is only accomplished in the helper bat (as the main one removes, then adds)


    set PARAMS_RAFF=%*
    call add-art-to-flac-helper %PARAMS_RAFF% REMOVE



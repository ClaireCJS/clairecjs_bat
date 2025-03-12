@Echo OFF

REM set                         SEQUENCE=%util2%\ColorTool\schemes\demona-default-win10_darkblack_*.ini
    set                         SEQUENCE=%util%\ColorTool\schemes\demona-default-win10_darkblack_rgb_seq_1_*.ini
    call set-randfile          %SEQUENCE%
    set        PALLETE_PROFILE=%RANDFILE%
    call ColorTool.bat --quiet %RANDFILE%
    :all ColorTool.bat         %RANDFILE%




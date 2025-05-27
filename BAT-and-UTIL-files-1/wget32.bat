@loadBTM ON
@Echo off
@on break cancel



rem Set color to logging color:
                   %COLOR_LOGGING%
        echos %ANSI_COLOR_LOGGING%



rem Cosmetic decorator pre-parameters:
        if defined WGET_DECORATOR    echos %WGET_DECORATOR
        if defined WGET_DECORATOR_ON echos %WGET_DECORATOR_ON

rem Default decorator pre-parameters if none are defined:
        if not defined WGET_DECORATOR .and. not defined WGET_DECORATOR_ON echos %FAINT_ON%%overstrike_on%


rem Actually do the wget command:
        wget32.exe %*


rem Cosmetic decorator post-parameters:
        if     defined WGET_DECORATOR_OFF echos %WGET_DECORATOR_OFF

rem Default decorator post-parameters if none are defined:
        if not defined WGET_DECORATOR_OFF echos %FAINT_Off%%overstrike_off%



rem Reset color back to normal:
                   %COLOR_NORMAL%
        echos %ANSI_COLOR_NORMAL%

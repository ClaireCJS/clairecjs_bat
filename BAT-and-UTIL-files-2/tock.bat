@Echo OFF
@on break cancel


rem OLD: echo %ANSI_RESET%
rem OLD: tock.py

rem NEW:
         call reset-ansi %*


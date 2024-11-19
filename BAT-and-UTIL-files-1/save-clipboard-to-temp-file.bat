@Echo OFF
@on break cancel

::::: VALIDATE ENVIRONMENT:
        call validate-environment-variables COLOR_LOGGING COLOR_NORMAL

::::: PARAMETER NAME, OR DEFAULT NAME?:
        set FNAME=%1 %+ if "%1" eq "" set FNAME=clipboard-save-%_DATETIME

::::: GET NAME:
        call set-tmp-file 
        set CLIPBOARD_SAVED_TO=%TMPFILE_DIR%\%FNAME-%TMPFILE_FILENAME%

::::: SAVE CLIPBOARD:
        type <clip: >%CLIPBOARD_SAVED_TO%
        call validate-environment-variable CLIPBOARD_SAVED_TO TMPFILE_FILENAME

::::: LET THEM KNOW:
        %COLOR_LOGGING% %+ echos * Clipboard saved to %%CLIPBOARD_SAVED_TO%% == "%CLIPBOARD_SAVED_TO%" `` 
        %COLOR_NORMAL%  %+ echo.


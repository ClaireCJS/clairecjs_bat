@Echo OFF
@on break cancel
set SCRIPT=%1
set NUMEXPR_MAX_THREADS=25
call validate-environment-variable SCRIPT UMEXPR_MAX_THREADS
pyinstaller --onefile %SCRIPT%
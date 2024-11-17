@Echo Off
set RFFID_PARAMS=%*
call validate-in-path set-first-file
call                  set-first-file %*>nul
set ERROR=0
call validate-env-var     FIRST_FILE "%blink_on%Sorry, there were no files of type: %italics_on%%underline_on%%RFFID_PARAMS%%italics_off%%underline_off%, so we can't run the first one%blink_off%"
if %ERROR eq 1 goto :Nope



                      set MY_START=
if %RFFID_START eq 1 (set MY_START=start)

%MY_START% "%FIRST_FILE%"  %+ REM we usually don't use 'start' here because we want our command-line handlers to override our GUI-handlers because there are programs that can permanently screw up a windows install if you run them in a GUI and associate it as the default program by accident. I'm looking at you, Irfanview




:Nope

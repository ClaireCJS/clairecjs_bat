@Echo OFF

call validate-in-path set-first-file
call                  set-first-file %*
call validate-env-var     FIRST_FILE
                        "%FIRST_FILE%"  %+ REM we don't use 'start' here because we want our command-line handlers to override our GUI-handlers because there are programs that can permanently screw up a windows install if you run them in a GUI and associate it as the default program by accident. I'm looking at you, Irfanview

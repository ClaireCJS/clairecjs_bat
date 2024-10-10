@Echo off

call validate-in-path removal important_less success sleep chrome.bat
call validate-environment-variable color_run 

call REMOVAL        "Killing Chrome..."    %+ kill /f Chrome*
call important_less "Waiting 2 seconds..." %+ call sleep 2
call success        "Starting Chrome..."   %+ rem http://www.krazydad.com/gustavog/FlickRandom.pl?user=ClioCJS
%COLOR_RUN%                                %+ call chrome.bat
call important_less "Waiting 4 seconds..." %+ call sleep 4










rem ———————————————————————————————————————————————————————————————————————————————————
rem 2015ish: echo Experiment: NOT doing "window restore" - does evillyrics still focus?
rem 2015ish:                  window restore evilly~1
rem ———————————————————————————————————————————————————————————————————————————————————


@Echo off

%COLOR_REMOVAL%        %+ echo Killing Chrome...    %+ kill /f Chrome*
%COLOR_IMPORTANT_LESS% %+ echo Waiting 2 seconds... %+ call sleep 2
%COLOR_SUCCCESS%       %+ echo Starting Chrome...   %+ rem http://www.krazydad.com/gustavog/FlickRandom.pl?user=ClioCJS
%COLOR_RUN%            %+ call chrome
%COLOR_IMPORTANT_LESS% %+ echo Waiting 4 seconds...
%COLOR_NORMAL%         %+ call sleep 4




:   echo Experiment: NOT doing "window restore" - does evillyrics still focus?
:   :experiment: window restore evilly~1


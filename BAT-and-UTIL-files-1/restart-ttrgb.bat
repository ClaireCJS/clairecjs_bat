@Echo OFF
@on break cancel

rem TTRGB is the program that controls our computer's cases lights

call isRunning               TTRGB
if  %isRunning eq 1 (kill /f TTRGB* %+ call wait 3)
call                         TTRGB





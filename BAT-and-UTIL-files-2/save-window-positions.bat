@Echo off
@on break cancel

set PARAMS=%*



set                                DisplayFusionCommand="C:\Program Files (x86)\DisplayFusion\DisplayFusionCommand.exe"
call validate-environment-variable DisplayFusionCommand 
call validate-in-path              important.bat




call important "Saving window positions %italics%%PARAMS%%italics_off%"
    %COLOR_RUN%
        if "%1" eq "" (%DisplayFusionCommand% -functionrun "Save Window Positions")
        if "%1" ne "" (%DisplayFusionCommand% -windowpositionprofilesave %PARAMS% %+ set LAST_SAVED_WINDOW_POSITION=%*)
    %COLOR_NORMAL%


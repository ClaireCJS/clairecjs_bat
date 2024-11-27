@Echo OFF
 on break cancel

rem Validate environment:
        call validate-environment-variable EMOJI_FIRE "run %italics_on%set-emoji.bat%italics_off% to define emojis"

rem Grab parameters:
        set CAP_PARAMS=%1

rem Store pre-run variable values:
        set NO_PAUSE_TEMP=%NO_PAUSE%
        set NO_PUSH_WARNING_TEMP=%NO_PUSH_WARNING%

        rem Set run variable values:
                set NO_PAUSE=0                      %+ rem decided i no longer want to default to not-pausing cause it doesn't give an opportunity to update the commit reason
                set NO_PUSH_WARNING=1               %+ rem decided i no longer want to default to the warning that a commit doesn't do a push {in case i forget that it's 2 steps}, because when running this script, it is already acknowledged as a two-step process in the name, "commit AND push.bat"

        rem 🎉🎉🎉 COMMIT *AND* PUSH, BABY! 🎉🎉🎉
                call commit %CAP_PARAMS%            %+ echo. %+ call divider
                call push   %CAP_PARAMS%         

rem Restore pre-run variable values:
        set NO_PAUSE=%NO_PAUSE_TEMP%
        set NO_PUSH_WARNING=%NO_PUSH_WARNING_TEMP%


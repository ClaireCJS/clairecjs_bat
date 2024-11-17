@echo off


rem This is the equivalent of "call validate-environment-variable PASSWORD" except with an option to hand-edit the variable value


if defined PASSWORD (goto :good)


:bad
        %COLOR_ERROR%
        echo  ``
        echo  ``
        echo ERROR!!!!!!!!!!!!!!
        echo  ``

        %COLOR_WARNING%
        echo You do not have %%PASSWORD defined!
        echo It should be the password to your shell account.
        echo This is required; please set this now.

        %COLOR_ADVICE%
        echo Make sure you do it right the first time; no second chances.
        pause
        echo  ``
        echo  ``
        echo  ``

        %COLOR_RUN%
        set PASSWORD=?
        eset PASSWORD

        %COLOR_SUCCESS%
        echo You have set the password to '%password.
        pause
goto :end

:good
:end


@Echo off


rem
rem     Passthrough BAT file for aliasing 'copy' to havfe the behavior we want:
rem
rem     1) Piping through our postprocessor to colorize/decorate our copies (if OS >= Windows 10)
rem     2) adding /Nt to not update JPSTREE.IDX because we don't feel that's worth it
rem     3) adding /RCT [new 2024 option] to compress over SMB shares for faster copies
rem

title Copying %*

rem New option coming down the pipeline:
                               set RCT=
        if "%_VerMajor" gt 31 (set RTC=/RTC ``)

rem Grab the passed parameters:
         set COPYBATPARAMS=%*
         
rem Generate the copy command:
        set LAST_COPY_COMMAND=*copy /Nt %RTC% /G /R /K /L /Z %COPYBATPARAMS%

rem Prettify with our post-processor, unless it's an older computer with an older OS:
        iff "%OS%" eq "7" .or. "%OS%" eq "2K" then
                %LAST_COPY_COMMAND%                     
        else
                if 1 ne %VALIDATED_CP% then
                        call validate-in-path copy-move-post.py fast_cat
                        set VALIDATED_CP=1
                endiff
                (%LAST_COPY_COMMAND% |&:u8 copy-move-post.py) |:u8 fast_cat
        endiff        


:END

title %CHECK%Copied %*


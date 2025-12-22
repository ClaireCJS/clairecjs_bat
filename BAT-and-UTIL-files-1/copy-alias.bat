@loadbtm on
@Echo off
@on break cancel
 goto :begin


rem
rem     Passthrough BAT file for aliasing 'copy' to havfe the behavior we want:
rem
rem     1) Piping through our postprocessor to colorize/decorate our copies (if OS >= Windows 10)
rem     2) adding /Nt to not update JPSTREE.IDX because we don't feel that's worth it
rem     3) adding /RCT [new 2024 option] to compress over SMB shares for faster copies
rem


:begin
title Copying %*                                               %+ rem  Set Window Title

rem New option coming down the pipeline:
rem                             unset /q   RCT
rem        if "%_VerMajor" gt 31 (set RTC=/RTC ``)

rem Grab the passed parameters:
         set COPYBATPARAMS=%*
                  
rem Generate the copy command:
        rem LAST_COPY_COMMAND=*copy /Nt %RTC% /G /R /K /L /Z %COPYBATPARAMS% %+ rem 2025/12/21: i believe the “/R” option is what’s interrupting us with overwrite prompts whereas “/Z” w/o “/R”
        set LAST_COPY_COMMAND=*copy /Nt %RTC% /G    /K /L /Z %COPYBATPARAMS%

rem Decide if doing old/simple or new/colorful copy method:
        if "%OS%" == "10"                     (goto :default)
        if "%OS%" == "11"                     (goto :default)
        if "%OS%" != "7" .and. "%OS%" != "2K" (goto :default)
        
        :the_simple_way
                %LAST_COPY_COMMAND%               
        
        :default
        :the_modern_way
                rem Make sure we have what we need:
                        iff not defined VALIDATED_CP then                                            %+ rem speed optimization to not check value
                                call    validate-in-path copy-move-post.py       fast_cat
                                set     VALIDATED_CP=1
                        endiff

                rem Prettify with our post-processor, unless it's an older computer with an older OS:
                        rem ((%LAST_COPY_COMMAND%)    |&:u8    copy-move-post.py |:u8 fast_cat)
                        rem Piping to fast_cat to fix ANSI errors seems to need to be performed *outside* of this BAT to not
                        rem have ansi errors on the generated double-height lines. Not sure why that started happening:
                            rem  %LAST_COPY_COMMAND% |:u8  copy-move-post.py
                            iff 1 eq 1 then                            
                                 %LAST_COPY_COMMAND% |&:u8 copy-move-post.py
                            else                                 
                                 %LAST_COPY_COMMAND% |&:u8 copy-move-post.py) |:u8 fast_cat
                            endiff                                 


:END

rem Update title:
        title %CHECK%Copied %*



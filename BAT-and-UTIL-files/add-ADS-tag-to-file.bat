
@rem     Sets a tag to associate with a file, using Windows Alternate Data Streams for files. 

@rem     These tags copy over to new locations and "live" "within" the files themselves, so moving/copying doesn't change things.



@Echo Off
 on break cancel
 
goto :init

:usage
echo.
call divider
%COLOR_ADVICE%
set //UnicodeOutput=yes
text
:USAGE: add-ADS-tag-to-file {%filename} {tag_name} {tag_value or "read" or "remove"} ["verbose"] [verb]
:USAGE: 
:USAGE: WRITE MODE (3rd arg is not "read"): Sets the file's tag to the value given
:USAGE: 
:USAGE:         EXAMPLE: add-ADS-tag-to-file  filename.txt songlyrics.txt lyrics approved
:USAGE:                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ sets the 'lyrics' tag to 'approved'
:USAGE: READ MODE (3rd arg is "read"): Sets %%RECEIVED_VALUE%% to the file's tag's value
:USAGE: 
:USAGE:         EXAMPLE: add-ADS-tag-to-file filename.txt songlyrics.txt lyrics read
:USAGE:                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ sets RECEIVED_VALUE=approved
:USAGE:
:USAGE: REMOVE MODE (3rd arg is "remove"): Deletes/Removes/blanks out tag on file
:USAGE: 
:USAGE:         EXAMPLE: add-ADS-tag-to-file filename.txt songlyrics.txt lyrics remove
:USAGE:                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ removes the tag
:USAGE:
:USAGE: VERBOSE MODE: (4th arg is "verbose"):
:USAGE:
:USAGE:         Verifies what happens on-screen.
:USAGE:
:USAGE: VERBOSE MODE: (5th arg is provided):
:USAGE:
:USAGE:         Verifies what happens on-screen, using the verb clausse of the 5th arg
:USAGE:                   i.e. "Verified value of", "set value of", "removed value of", "set lyric status to", etc'
:USAGE:
:USAGE:         EXAMPLE: add-ADS-tag-to-file filename.txt songlyrics.txt lyrics remove verbose "begrudgingly removed"
:USAGE:         EXAMPLE: add-ADS-tag-to-file filename.txt songlyrics.txt lyrics approved verbose "Lyric approvel set to:"
:USAGE:
endtext
%COLOR_NORMAL%
if not defined DefaultUnicodeOutput set DefaultUnicodeOutput=no
set //UnicodeOutput=%DefaultUnicodeOutput%
call divider
return


:init



rem Get parameters:
        set   FILE_TO_USE=%@FULL[%@UNQUOTE[%1]]                        %+ rem file to use 
        set TAG_TO_MODIFY=%@UNQUOTE[%2]                                    %+ rem tag to use
        set     TAG_VALUE=%@UNQUOTE[%3]                                    %+ rem value to set tag to, or "read" to return the value in %RETRIEVED_TAG%
        set       PARAM_4=%4                                               %+ rem "verbose" if you want on-screen verification of what's happeneing
        set       PARAM_5=%@UNQUOTE[%5]                                    %+ rem  Verb to use in verbose output ("set", "deleted", "marked", "read", etc)



rem Validate environment once:
        iff 1 ne %validated_add_ads_tag_to_file% then
                call validate-environment-variables emphasis deemphasis italics_on italics_off ansi_color_green normal_arrow bold_on bold_off faint_on faint_off
                call validate-in-path                fatal_error warning 
                set  validated_add_ads_tag_to_file=1
        endiff

rem Validate parameters every time:
        if "%1" EQ ""                                       (gosub :usage %+ goto :END)
        call validate-environment-variable  File_To_Use    "1st arg to %0 must be a filename. 2nd optional arg must be a tag, 3rd arg must be 'read' or a value, 4th optional arg can be 'verbose'"
        call validate-environment-variable   Tag_To_Modify "2nd argument to %0 must a tag, NOT empty"
        call validate-environment-variable   Tag_Value     "3rd argument to %0 must a value, or 'read' ... NOT empty"
        if "%PARAM_4%" ne "" .and. "%PARAM_4%" ne "verbose" .and. "%PARAM_4%" ne "remove" (call    fatal_error    "There shouldn't be a 4th parameter of this value being sent to %0 {called by %_PBATCHNAME}, but you gave '%italics_on%%PARAM_4%%italics_off%'. Run without parameters to understand proper usage.")


rem Set default values for parameters:
        set VERBOSE=0
        if "%PARAM_4%"       eq "verbose" (set VERBOSE=1)         
        if "%TAG_TO_MODIFY%" eq        "" (set TAG_TO_MODIFY=tag)               %+ rem setting dummy value in case of failure
        if "%TAG_VALUE%"     eq        "" (set TAG_TO_MODIFY=value)             %+ rem setting dummy value in case of failure
        
rem Determine verb clause to use —— looks best if they are >8 chars each though!
        set VERB=Set value to:
        if "read"      eq "%TAG_VALUE%"          (set VERB=Retrieved value %faint_on%of%faint_off%:)
        if "remove"    eq "%TAG_VALUE%"          (set VERB=Removed value %faint_on%of%faint_off%:)
        if "%PARAM_5%" ne "" .and. 1 eq %VERBOSE (set VERB=%PARAM_5%)           %+ rem Fetch alternate-verb for verbose mode
        set VERB_LEN=%@LEN[%@STRIPANSI[%VERB%]]
        set SPACER=%@REPEAT[ ,%@ABS[%@EVAL[%VERB_LEN%-8]]]``


rem Read or set (depending on invocation) via windows alternate data streams:
        iff "read" eq "%TAG_VALUE%" then
        
                echo —————————————————— READ THE TAG  —————————————————— >nul
                rem Store the result of reading the tag into the environment variable we've decided to use as convention for this situation:
                        set RECEIVED_VALUE=%@ExecStr[type <"%FILE_TO_USE%:%TAG_TO_MODIFY%"]
                        set value_to_display_in_verbose_mode=%RECEIVED_VALUE%
                
                rem And a few aliaes of our results, for the invokee who doesn't quite remember how to use this:
                        set            RESULT=%RECEIVED_VALUE%
                        set          RECEIVED=%RECEIVED_VALUE%
                        set      RECEIVED_TAG=%RECEIVED_VALUE%
                        set RECEIVED_METADATA=%RECEIVED_VALUE%

                rem If we are in verbose mode, explain what we did:                                                 
                        gosub explain                        
                        
        elseiff "remove" eq "%TAG_VALUE%" then
        
                echo —————————————————— DELETE THE TAG  —————————————————— >nul
                rem Grab the value so we can say it was removed:
                        set  OLD_VALUE=%@ExecStr[type "%FILE_TO_USE%:%TAG_TO_MODIFY%"]
                        if "%OLD_VALUE%" eq ""       (set OLD_VALUE=%ansi_color_normal%%ansi_color_red%%@Repeat[%@CHAR[10875],3]%faint_on% none %faint_off%%@Repeat[%@CHAR[10876],3]%ansi_color_normal%)
                        if "%TAG_VALUE%" eq "remove" (set value_to_display_in_verbose_mode=%OLD_VALUE%)

                rem Delete/blank out/remove the tag from the file, but in a very safe way where we don't accidentally delete the file:
                        iff "%TAG_TO_MODIFY%" ne "" then
                                >"%FILE_TO_USE%:%TAG_TO_MODIFY%"
                        else
                                call fatal_error ("%TAG_TO_MODIFY is currently '%TAG_TO_MODIFY%' and absolutely should not be" %+ goto :END)
                        endiff

                rem If we are in verbose mode, explain what we did:                         
                        gosub explain
                
        else
        
                echo —————————————————— SET THE TAG  —————————————————— >nul
                rem Associate the tag+value pair into the file:
                        echo %TAG_VALUE%>"%FILE_TO_USE%:%TAG_TO_MODIFY%"

                rem Grab it right back out so our verbose output says the true value:
                        set value_to_display_in_verbose_mode=%@ExecStr[type <"%FILE_TO_USE%:%TAG_TO_MODIFY%"]
                        
                rem If we are in verbose mode, verify the write by reading it:
                        gosub explain
                        
        endiff


goto :END

        :explain
                rem If we are in verbose mode, explain what we did:
                        iff 1 eq %VERBOSE then
                                echo %CHECK% %VERB% %italics_on%%emphasis%%[value_to_display_in_verbose_mode]%deemphasis%%italics_off% 
                                echo %SPACER%%ansi_color_green%%normal_arrow%%ansi_color_normal%  %faint_on%for%faint_off% tag: %ansi_color_bright_red%%bold_on%%[TAG_TO_MODIFY]%bold_off%%ansi_normal%
                                echo %SPACER%%ansi_color_green%%normal_arrow%%ansi_color_normal%  %faint_on%in%faint_off% file: %@ANSI_FG_RGB[168,210,104]%[FILE_TO_USE]%ansi_color_normal%
                        endiff                                
        return

:END


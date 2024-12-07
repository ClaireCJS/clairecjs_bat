@Echo Off
on break cancel
goto :init


@rem     Sets a tag to associate with a file, using Windows Alternate Data Streams for files. 
@rem     These tags copy over to new locations and "live" "within" the files themselves, so moving/copying doesn't change things.

:usage
echo.
call divider
%COLOR_ADVICE%
set //UnicodeOutput=yes
text
:USAGE: add-ADS-tag-to-file {%filename} {tag_name} {tag_value or "read" or "remove"} ["verbose" or "brief" or "lyrics"] [verb]
:USAGE: 
:USAGE: 1st arg is the filename we are operating on
:USAGE: 2nd arg is the tag name we want to read/write/delete
:USAGE: 
:USAGE: WRITE MODE (3rd arg is not "read"): Sets the file's tag to the value given
:USAGE: 
:USAGE:         EXAMPLE: add-ADS-tag-to-file filename.txt songlyrics.txt lyrics approved
:USAGE:                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ sets the 'lyrics' tag to 'approved'
:USAGE: READ MODE (3rd arg is "read"): Sets %%RECEIVED_VALUE%% to the file's tag's value
:USAGE: 
:USAGE:         EXAMPLE: add-ADS-tag-to-file filename.txt songlyrics.txt lyrics read
:USAGE:                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ Sets RECEIVED_VALUE=approved, i.e. the value that was read for the tag 'lyrics'
:USAGE:
:USAGE: REMOVE MODE (3rd arg is "remove"): Deletes/Removes/blanks out tag on file
:USAGE: 
:USAGE:         EXAMPLE: add-ADS-tag-to-file filename.txt songlyrics.txt lyrics remove
:USAGE:                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ removes the 'lyrics' tag from the file
:USAGE:
:USAGE: VERBOSE/BRIEF/LYRICS MODE: (4th arg is "verbose" or "brief" or "lyrics"):
:USAGE:
:USAGE:         "verbose" —— Verifies what happens on-screen in a 3-line verbose way
:USAGE:         "brief" ———— Verifies what happens on-screen in a 1-line brief way
:USAGE:         "lyrics" ——— Verifies what happens on-screen in a 1-line brief way customized for lyric-file approval/disapproval
:USAGE:
:USAGE: VERBOSE MODE: (5th arg is ... a verb, direct object, and preposition):
:USAGE:
:USAGE:         Sets the verb clause of how we express the tag being set.
:USAGE:                   i.e. "Verified value of", "set value of", "removed value of", "set lyric status to", etc
:USAGE:         Has no effect in brief/lyrics mode.
:USAGE:
:USAGE:         EXAMPLE: add-ADS-tag-to-file filename.txt lyrics.txt lyrics  remove  verbose "begrudgingly removed"
:USAGE:         EXAMPLE: add-ADS-tag-to-file filename.txt lyrics.txt lyrics approved verbose "At %_datetime, Lyric approval set to:"
:USAGE:
:USAGE: SPACER MODE: set USE_SPACER=1              [make sure to set to 0 when done!!!]
:USAGE:
:USAGE:         For lyrics mode only. 
:USAGE:         Performs cosmetic spacing around lyric status so they line up when displaying for multiple files
:USAGE:


endtext
%COLOR_NORMAL%
if not defined DefaultUnicodeOutput set DefaultUnicodeOutput=no
set //UnicodeOutput=%DefaultUnicodeOutput%
call divider
return


:init



rem Get parameters:
        set   File_To_Change_Tag_Of=%@unquote[%@trueNAME[%@UNQUOTE[%1]]]             %+ rem file to use 
        set TAG_TO_MODIFY=%@UNQUOTE[%2]                                    %+ rem tag to use
        set     TAG_VALUE=%@UNQUOTE[%3]                                    %+ rem value to set tag to, or "read" to return the value in %RETRIEVED_TAG%
        set       PARAM_4=%4                                               %+ rem "verbose" if you want on-screen verification of what's happeneing
        set       PARAM_5=%@UNQUOTE[%5]                                    %+ rem  Verb to use in verbose output ("set", "deleted", "marked", "read", etc)


rem Validate environment once:
        iff 1 ne %validated_add_ads_tag_to_file% then
                call validate-environment-variables  emphasis deemphasis italics_on italics_off ansi_color_green normal_arrow bold_on bold_off faint_on faint_off check EMOJI_CROSS_MARK ansi_color_alarm ansi_color_celebration ansi_color_warning_soft EMOJI_MAGNIFYING_GLASS_TILTED_RIGHT EMOJI_RED_QUESTION_MARK
                call validate-in-path                fatal_error warning 
                set  validated_add_ads_tag_to_file=1
        endiff

rem Validate parameters every time:
        iff "%@RegEx[[\*\?],%File_To_Change_Tag_Of%]" eq "1" then
                call warning "Cannot use %0 on wildcards for 1ˢᵗ parameter!"
                goto :END
        endiff
        if "%1" EQ ""                                       (gosub :usage %+ goto :END)
        call validate-environment-variable File_To_Change_Tag_Of  "1ˢᵗ arg to %@unquote[%0] of '%italics_on%%@unquote[%1]%italics_off%' must be a filename that actually exists"
        call validate-environment-variable Tag_To_Modify          "2ⁿᵈ argument to %0 must a tag, NOT empty"
        call validate-environment-variable Tag_Value              "3ʳᵈ argument to %0 must a value, or 'read' ... NOT empty"
        if "%PARAM_4%" ne "" .and. "%PARAM_4%" ne "verbose" .and. "%PARAM_4%" ne "remove" .and. "%PARAM_4%" ne "brief" .and. "%PARAM_4%" ne "lyrics" .and. "%PARAM_4%" ne "lyric" (call fatal_error "There shouldn't be a 4th parameter of this value being sent to %0 {called by %_PBATCHNAME}, but you gave '%italics_on%%PARAM_4%%italics_off%'. Run without parameters to understand proper usage.")

rem Set default values for parameters:
        set VERBOSE=0
        set BRIEF_MODE=0
        set LYRIC_MODE=0
        rem echo tail=%*
        if "%PARAM_4%"       eq "lyric"   (set LYRIC_MODE=1)                    
        if "%PARAM_4%"       eq "lyrics"  (set LYRIC_MODE=1)                    
        if "%PARAM_4%"       eq "brief"   (set BRIEF_MODE=1)           
        if "%PARAM_4%"       eq "verbose" (set    VERBOSE=1)         
        if "%TAG_VALUE%"     eq        "" (set TAG_TO_MODIFY=value)             %+ rem setting dummy value in case of failure
        if "%TAG_TO_MODIFY%" eq        "" (set TAG_TO_MODIFY=tag  )             %+ rem setting dummy value in case of failure
        
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
                set OPERATIONAL_MODE=READ
                rem Store the result of reading the tag into the environment variable we've decided to use as convention for this situation:
                        set RECEIVED_VALUE=%@ExecStr[type <"%File_To_Change_Tag_Of%:%TAG_TO_MODIFY%" >&>nul]
                        set   RECEIVED_TAG=%TAG_TO_MODIFY%
                        set value_to_display_in_verbose_mode=%RECEIVED_VALUE%
                
                rem And a few aliases of our results, for the invokee who doesn't quite remember how to use this:
                        set            RESULT=%RECEIVED_VALUE%
                        set          RECEIVED=%RECEIVED_VALUE%
                        set RECEIVED_METADATA=%RECEIVED_VALUE%

                rem If we are in verbose mode, explain what we did:                                                 
                        gosub explain                        
                        
        elseiff "remove" eq "%TAG_VALUE%" then
        
                echo —————————————————— DELETE THE TAG  —————————————————— >nul
                set OPERATIONAL_MODE=DELETE
                rem Grab the value so we can say it was removed:
                        set  OLD_VALUE=%@ExecStr[type "%File_To_Change_Tag_Of%:%TAG_TO_MODIFY%"]
                        if "%OLD_VALUE%" eq ""       (set OLD_VALUE=%ansi_color_normal%%ansi_color_red%%@Repeat[%@CHAR[10875],3]%faint_on% none %faint_off%%@Repeat[%@CHAR[10876],3]%ansi_color_normal%)
                        if "%TAG_VALUE%" eq "remove" (set value_to_display_in_verbose_mode=%OLD_VALUE%)

                rem Delete/blank out/remove the tag from the file, but in a very safe way where we don't accidentally delete the file:
                        iff "%TAG_TO_MODIFY%" ne "" then
                                >"%File_To_Change_Tag_Of%:%TAG_TO_MODIFY%"
                        else
                                call fatal_error ("%TAG_TO_MODIFY is currently '%TAG_TO_MODIFY%' and absolutely should not be" %+ goto :END)
                        endiff

                rem If we are in verbose mode, explain what we did:                         
                        gosub explain
                
        else
        
                echo —————————————————— SET THE TAG  —————————————————— >nul
                set OPERATIONAL_MODE=SET
                rem Associate the tag+value pair into the file:
                        echo %TAG_VALUE%>"%File_To_Change_Tag_Of%:%TAG_TO_MODIFY%"

                rem Grab it right back out so our verbose output says the true value:
                        set value_to_display_in_verbose_mode=%@ExecStr[type <"%File_To_Change_Tag_Of%:%TAG_TO_MODIFY%"]
                        
                rem If we are in verbose mode, verify the write by reading it:
                        gosub explain
                        
        endiff


goto :END

        :explain
                rem If we are in verbose mode, explain what we did:
                        set tmp_value=%[value_to_display_in_verbose_mode]
                        if "" eq "%tmp_value%" (set tmp_value=%italics_on%%blink_on%(unset)%blink_off%%italics_off%)
                        set tmp_tag=%[TAG_TO_MODIFY]
                        set tmp_file2use=%[File_To_Change_Tag_Of]
                        set tmp_emoji2use=%CHECK%           

                        rem echo [verbose=%verbose,brief_mode=%brief_mode%,lyric_mode=%lyric_mode%]
                        
                        iff 1 eq %VERBOSE then
                                echo %tmp_emoji2use% %VERB% %italics_on%%emphasis%%tmp_value%%deemphasis%%italics_off% 
                                echo %SPACER%%ansi_color_green%%normal_arrow%%ansi_color_normal%  %faint_on%for%faint_off% tag: %ansi_color_bright_red%%bold_on%%tmp_tag%%bold_off%%ansi_normal%
                                echo %SPACER%%ansi_color_green%%normal_arrow%%ansi_color_normal%  %faint_on%in%faint_off% file: %@ANSI_FG_RGB[168,210,104]%tmp_file2use%%ansi_color_normal%
                        endiff                              
                        iff 1 eq %BRIEF_MODE then
                                echo %tmp_emoji2use% Set %bold_on%%tmp_tag%%bold_off% to %italics_on%%emphasis%%tmp_value%%deemphasis%%italics_off% for %faint_on%%italics_on%%tmp_file2use%%faint_off%%italics_off%
                        endiff
                        iff 1 eq %LYRIC_MODE then
                                set value_spacer=
                                set value_spacer_post=
                                set voodoo_spacer=
                                iff "%tmp_value%" == "NOT_APPROVED" .or. "%tmp_value%" == "NOT APPROVED" then
                                        set tmp_emoji2use=%EMOJI_CROSS_MARK%
                                        set tmp_color=%ansi_color_alarm%
                                elseiff "%tmp_value%" == "APPROVED" then
                                        if 1 eq %USE_SPACER (set value_spacer=    ``)
                                        set tmp_emoji2use=%CHECK%           
                                        set tmp_color=%ansi_color_celebration%
                                else                                        
                                        iff 1 eq %USE_SPACER then
                                                set value_spacer=      ``
                                                set value_spacer_post=``
                                                rem voodoo_spacer=%@ANSI_MOVE_LEFT[1]
                                                set voodoo_spacer= ``
                                        else                                                
                                                set value_spacer= ``
                                                set voodoo_spacer= ``
                                        endiff                                                
                                        set tmp_color=%ansi_color_warning_soft%
                                        set tmp_emoji2use=%EMOJI_EXCLAMATION_QUESTION_MARK%          
                                endiff
                                iff "%OPERATIONAL_MODE%" ne "READ" then
                                        echo %tmp_emoji2use% Set %bold_on%%italics_on%%tmp_tag%%italics_off%%bold_off% to %italics_on%%tmp_color%%tmp_value%%ansi_color_normal%%deemphasis%%italics_off% for %faint_on%%italics_on%%tmp_file2use%%faint_off%%italics_off%
                                else
                                        echo %EMOJI_MAGNIFYING_GLASS_TILTED_RIGHT% Lyrics are  %value_spacer%%tmp_emoji2use% %italics_on%%tmp_color%%tmp_value%%ansi_color_normal%%deemphasis%%italics_off%%voodoo_spacer%%tmp_emoji2use% %value_spacer_post% for: %faint_on%%italics_on%%tmp_file2use%%faint_off%%italics_off%
                                endiff
                        endiff
        return

:END


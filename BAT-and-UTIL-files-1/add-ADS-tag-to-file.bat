@loadbtm on
@Echo Off
@on break cancel
@setdos /x0
goto :init


@rem     Sets a tag to associate with a file, using Windows Alternate Data Streams for files. 
@rem     These tags copy over to new locations and "live" "within" the files themselves, so moving/copying doesn't change things.

:usage
echo.
gosub divider
%COLOR_ADVICE%
set //UnicodeOutput=yes
text
:USAGE: add-ADS-tag-to-file {%filename} {tag_name} {tag_value or "read" or "remove"} ["verbose" or "brief" or "lyrics"] [verb or "skip_validations"]
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
gosub divider
return


:init



rem Get parameters:
        set   File_To_Change_TagOOF=%@unquote[%@trueNAME["%@UNQUOTE["%1"]"]]               %+ rem file to use but %@TRUENAME[] fails on ;
        set   File_To_Change_Tag_Of=%@unquote[%@truename["%@replace[;,%%%%@char[59],%1]"]] %+ rem file to use that works with ; 
        rem echo BEFORE: File_To_Change_Tag_Of = %File_To_Change_Tag_Of%
        set   File_To_Change_Tag_Of=%@unquote["%@ReReplace[\\\\\?\\,,"%File_To_Change_Tag_Of%"]"]
        rem echo AFTER:  File_To_Change_Tag_Of = %File_To_Change_Tag_Of% %+ call sleep 2 %+ rem 

        set TAG_TO_MODIFY=%@UNQUOTE["%2"]                                      %+ rem tag to use
        set     TAG_VALUE=%@UNQUOTE["%3"]                                      %+ rem value to set tag to, or "read" to return the value in %RETRIEVED_TAG%
        set       PARAM_4=%4                                                   %+ rem "verbose" if you want on-screen verification of what's happeneing
        set       PARAM_5=%@UNQUOTE["%5"]                                      %+ rem  Verb to use in verbose output ("set", "deleted", "marked", "read", etc)

        rem   File_To_Change_Tag_Of  is “%File_To_Change_Tag_Of%” 
        rem   File_To_Change_Tag_Of2 is “%File_To_Change_Tag_Of2%” 


rem Validate environment once:
        iff "1" != "%validated_add_ads_tag_to_file%" then
                call validate-environment-variables  ansi_colors_have_been_set emoji_have_been_set
                call validate-in-path                fatal_error warning warning_soft print-message pause-for-x-seconds
                call validate-plugin                 StripANSI
                set  validated_add_ads_tag_to_file=1
        endiff

rem Validate parameters every time:
        iff "%@RegEx[[\*\?],"%@unquote["%File_To_Change_Tag_Of%"]"]" == "1" then
                call warning "Cannot use %0 on wildcards for 1ˢᵗ parameter!"
                call warning_soft "File_To_Change_Tag_Of of “%File_To_Change_Tag_Of%” doesn’t seem to work here"
                call pause-for-x-seconds 7200
                goto :END
        endiff
        if "%1" == "" (gosub :usage %+ goto :END)
        rem add-ADS-tag-to-file "2_08_Ikon - The Ballad Of Gilligan's Island.txt" "lyrics" read lyrics skip_validatoins
        if "%5" == "skip_validations" (goto :skip_validations_1)
        rem if not exist "%@UNQUOTE["%File_To_Change_Tag_Of%"]" call validate-environment-variable  File_To_Change_Tag_Of  "1ˢᵗ arg to %@unquote[%0] of '%italics_on%%@unquote[%1]%italics_off%' must be a filename that actually exists"
        if not exist "%@UNQUOTE["%File_To_Change_Tag_Of%"]" call validate-environment-variable  File_To_Change_Tag_Of  "1ˢᵗ arg to %@unquote[%0] of '%italics_on%%@unquote[%1]%italics_off%' must be a filename that actually exists"
        if "" == "%Tag_To_Modify" .or. "" == "%Tag_Value%"  call validate-environment-variables Tag_To_Modify Tag_Value              
        rem call validate-environment-variable Tag_To_Modify          "2ⁿᵈ argument to %0 must a tag, NOT empty"
        rem call validate-environment-variable Tag_Value              "3ʳᵈ argument to %0 must a value, or 'read' ... NOT empty"
        :skip_validations_1
        if "%PARAM_4%" != "" .and. "%PARAM_4%" != "verbose" .and. "%PARAM_4%" != "remove" .and. "%PARAM_4%" != "brief" .and. "%PARAM_4%" != "lyrics" .and. "%PARAM_4%" != "lyric" (call fatal_error "There shouldn't be a 4th parameter of this value being sent to %0 {called by %_PBATCHNAME}, but you gave '%italics_on%%PARAM_4%%italics_off%'. Run without parameters to understand proper usage.")
        
rem Set default values for parameters:
        set EXT=%@EXT[%File_To_Change_Tag_Of]
                set VERBOSE=0
        set BRIEF_MODE=0
        set LYRIC_MODE=0
        rem echo tail=%*
        if "%PARAM_4%"       == "lyriclessness"  (set LYRIC_MODE=1)                    
        if "%PARAM_4%"       == "lyricslessness" (set LYRIC_MODE=1)                    
        if "%PARAM_4%"       == "lyric"          (set LYRIC_MODE=1)                    
        if "%PARAM_4%"       == "lyrics"         (set LYRIC_MODE=1)                    
        rem DEBUG: echo lyric_mode=%lyric_mode% %emoji_cat%
        if "%PARAM_4%"       == "brief"          (set BRIEF_MODE=1)           
        if "%PARAM_4%"       == "verbose"        (set    VERBOSE=1)         
        if "%TAG_VALUE%"     ==        ""        (set TAG_TO_MODIFY=value)             %+ rem setting dummy value in case of failure
        if "%TAG_TO_MODIFY%" ==        ""        (set TAG_TO_MODIFY=tag  )             %+ rem setting dummy value in case of failure
        
        rem Lyric mode stuff:
                set ENTITY=Lyrics
                set VERB2=are
                if "%EXT%" == "lrc"  (set VERB2=is  %+ set ENTITY=Karaoke)
                if "%EXT%" == "srt"  (set VERB2=are %+ set ENTITY=Subtitles)
                if "%EXT%" == "txt"  (set VERB2=are %+ set ENTITY=Lyrics)
                if "%EXT%" == "mp3"  (set VERB2=is  %+ set ENTITY=Audio)
                if "%EXT%" == "flac" (set VERB2=is  %+ set ENTITY=Audio)
                if "%EXT%" == "wav"  (set VERB2=is  %+ set ENTITY=Audio)
                set emj1=%@CHAR[55357]%@CHAR[56546]
                set emj2=%@CHAR[55357]%@CHAR[56541]
        
        
rem Determine verb clause to use —— looks best if they are >8 chars each though!
        set VERB=Set value to:
        if "read"      == "%TAG_VALUE%"          (set VERB=Retrieved value %faint_on%of%faint_off%:)
        if "remove"    == "%TAG_VALUE%"          (set VERB=Removed value %faint_on%of%faint_off%:)
        if "%PARAM_5%" != "" .and. 1 eq %VERBOSE (set VERB=%PARAM_5%)                 %+ rem Fetch alternate-verb for verbose mode
        set VERB_LEN=%@LEN[%@STRIPANSI[%VERB%]]
        set SPACER=%@REPEAT[ ,%@ABS[%@EVAL[%VERB_LEN%-8]]]``

rem Read or set (depending on invocation) via windows alternate data streams:
        iff "read" == "%TAG_VALUE%" then
                echo —————————————————— READ THE TAG  —————————————————— >nul
                set OPERATIONAL_MODE=READ
                rem Store the result of reading the tag into the environment variable we've decided to use as convention for this situation:
                        set RECEIVED_VALUE=%@ExecStr[type "%File_To_Change_Tag_Of%:%TAG_TO_MODIFY%" >&>nul]
                        set   RECEIVED_TAG=%TAG_TO_MODIFY%
                        set value_to_display_in_verbose_mode=%RECEIVED_VALUE%
                
                rem And a few aliases of our results, for the invokee who doesn't quite remember how to use this:
                        set            RESULT=%RECEIVED_VALUE%
                        set          RECEIVED=%RECEIVED_VALUE%
                        set RECEIVED_METADATA=%RECEIVED_VALUE%

                rem If we are in verbose mode, explain what we did:                                                 
                        gosub explain                        
                        
        elseiff "remove" == "%TAG_VALUE%" then
        
                echo —————————————————— DELETE THE TAG  —————————————————— >nul
                set OPERATIONAL_MODE=DELETE
                rem Grab the value so we can say it was removed:
                        set  OLD_VALUE=%@ExecStr[type "%File_To_Change_Tag_Of%:%TAG_TO_MODIFY%"]
                        if "%OLD_VALUE%" == ""       (set OLD_VALUE=%ansi_color_normal%%ansi_color_red%%@Repeat[%@CHAR[10875],3]%faint_on% none %faint_off%%@Repeat[%@CHAR[10876],3]%ansi_color_normal%)
                        if "%TAG_VALUE%" == "remove" (set value_to_display_in_verbose_mode=%OLD_VALUE%)

                rem Delete/blank out/remove the tag from the file, but in a very safe way where we don't accidentally delete the file:
                        iff "%TAG_TO_MODIFY%" != "" then
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
                        set value_to_display_in_verbose_mode=%@ExecStr[type "%File_To_Change_Tag_Of%:%TAG_TO_MODIFY%"]
                        
                rem If we are in verbose mode, verify the write by reading it:
                        gosub explain
                        
        endiff


goto :END

        :explain
                rem DEBUG:
                        rem echo [OPERATIONAL_MODE=%OPERATIONAL_MODE%, lyric_mode=%lyric_mode%]
                
                rem If we are in verbose mode, explain what we did:
                        set tmp_value=%[value_to_display_in_verbose_mode]
                        iff "" == "%tmp_value%" then
                                set tmp_value=%italics_on%%blink_on%(unset)%blink_off%%italics_off%
                                set was_null=1
                        else
                                set was_null=0
                        endiff                                

                rem Initialize values                        
                        set tmp_tag=%[TAG_TO_MODIFY]
                        set tmp_file2use=%[File_To_Change_Tag_Of]
                        set ext2=%@unquote[%@EXT["%tmp_file2use"]]
                        set tmp_emoji2use=%CHECK%           

                rem DEBUG: echo [verbose=%verbose,brief_mode=%brief_mode%,lyric_mode=%lyric_mode%]
                        
                rem Verbose mode output:                        
                        iff 1 eq %VERBOSE then
                                echo %tmp_emoji2use% %VERB% %italics_on%%emphasis%%tmp_value%%deemphasis%%italics_off% 
                                echo %SPACER%%ansi_color_green%%normal_arrow%%ansi_color_normal%  %faint_on%for%faint_off% tag: %ansi_color_bright_red%%bold_on%%tmp_tag%%bold_off%%ansi_normal%%conceal_on%red42%conceal_off%
                                echo %SPACER%%ansi_color_green%%normal_arrow%%ansi_color_normal%  %faint_on%in%faint_off% file: %@ANSI_FG_RGB[168,210,104]%tmp_file2use%%ansi_color_normal%%conceal_on%red43%conceal_off%
                        endiff                              

                rem Brief mode output:                        
                        iff 1 eq %BRIEF_MODE then
                                echo %ansi_color_green%%tmp_emoji2use% Set %bold_on%%tmp_tag%%bold_off% to %italics_on%%emphasis%%tmp_value%%deemphasis%%italics_off% for %faint_on%%italics_on%%tmp_file2use%%faint_off%%italics_off%%conceal_on%red44%conceal_off%
                        endiff


                rem Lyrics mode output:                        
                        if "1" !=  "%LYRIC_MODE" goto :endif_353
                                set  value_spacer=
                                set  value_spacer_post=
                                set voodoo_spacer=
                                if 1 eq %WAS_NULL set tmp_value=NOT_APPROVED

                                iff "%tmp_value%" == "NOT_APPROVED" .or. "%tmp_value%" == "NOT APPROVED" .or. "%tmp_value%" == "" .or. 1 eq %WAS_NULL% then
                                        set tmp_emoji2use=%EMOJI_CROSS_MARK%
                                        set tmp_color=%ansi_color_alarm%
                                elseiff "%tmp_value%" == "APPROVED" then
                                        if 1 eq %USE_SPACER (set value_spacer=    ``)
                                        set tmp_value=%dot% APPROVED %dot%``
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
                                
                                if  "%OPERATIONAL_MODE%" != "READ" .and. "1" != "%LYRIC_MODE%" goto :then_block_278
                                                                                               goto :else_block_282
                                        :then_block_278
                                                echo %tmp_emoji2use% Set %bold_on%%italics_on%%tmp_tag%%italics_off%%bold_off% to %italics_on%%tmp_color%%tmp_value%%ansi_color_normal%%deemphasis%%italics_off% for %faint_on%%italics_on%%tmp_file2use%%faint_off%%italics_off%
                                        goto :endif_351
                                rem else
                                        :else_block_282
                                                rem it is a lyric mode:
                                                                      
                                                set hide_status=0
                                                if "%tag_to_modify%" == "lyriclessness" goto :then_block_286
                                                                                        goto :else_block_304
                                                        :then_block_286
                                                                set our_maybe_subtitle_1=%@unquote[%@NAME["%tmp_file2use%"]].lrc
                                                                set our_maybe_subtitle_2=%@unquote[%@NAME["%tmp_file2use%"]].srt
                                                                set our_maybe_lyrics=%@unquote[%@NAME["%tmp_file2use%"]].txt
                                                                iff     exist "%our_maybe_subtitle_1%" .or. exist "%our_maybe_subtitle_2%" then
                                                                        set EXTRA=%ansi_color_bright_green%Has karaoke! %ansi_color_normal%
                                                                        set hide_status=0
                                                                elseiff exist "%our_maybe_lyrics%" then                                                
                                                                        set hide_status=0
                                                                        set EXTRA=%ansi_color_bright_YELLOW%Has lyrics!%ansi_color_normal%%faint_on%..%faint_off%
                                                                else
                                                                        set hide_status=0
                                                                        set EXTRA=%ansi_color_red%No lyrics!...%ansi_color_normal%
                                                                endiff                                                        
                                                                set value_spacer=``
                                                                set EXTRA=%EXTRA% Lyriclessness is
                                                        goto :endif_328
                                                rem else
                                                        :else_block_304
                                                                rem echo [ext2=%ext2%]
                                                                if "%ext2%" == "lrc" .or. "%ext2%" == "srt" goto :block_302
                                                                                                            goto :block_314       
                                                                        :block_302
                                                                                set ENTITY=Karaoke 
                                                                                set VERB2=is
                                                                                set EXTRA=%@ansi_move_left[3]%ansi_color_green%%emj1% %ENTITY% %emj1% file.... %ansi_color_normal%
                                                                        goto :endif_323
                                                                rem else 
                                                                        :block_314
                                                                                if "%EXT2%" == "txt" (                                                        
                                                                                        set ENTITY=Lyrics
                                                                                        set EXTRA=%@ansi_move_left[3]%ansi_color_green%%emj2% %ENTITY% %emj2% file..... %ansi_color_normal%
                                                                                ) else (
                                                                                        set EXTRA=%ansi_color_green%%ENTITY% exist
                                                                                        if "is" == "%VERB2%" set EXTRA=%EXTRA%s
                                                                                        set EXTRA=%EXTRA%%ansi_color_normal%...
                                                                                )                                                                
                                                                        goto :endif_323
                                                                :endif_323
                                                                set EXTRA=%EXTRA%%ENTITY% %VERB2% 
                                                                set value_spacer=``
                                                        goto :endif_328
                                                :endif_328
                                                
                                                echos %EMOJI_MAGNIFYING_GLASS_TILTED_RIGHT% %EXTRA% %value_spacer%
                                                if "1" == "%HIDE_STATUS%" goto :then_block_332
                                                                          goto :else_block_337
                                                        :then_block_332
                                                                echos %@ANSI_MOVE_LEFT[18]%faint_on%....................................%faint_off%``
                                                        goto :end_block_344
                                                rem else
                                                        :else_block_337
                                                                echos  %tmp_emoji2use% %italics_on%%tmp_color%%tmp_value%%ansi_color_normal%%deemphasis%%italics_off%%voodoo_spacer%%tmp_emoji2use%
                                                        goto :end_block_344
                                                :end_block_344
                                                echos %value_spacer_post% for %@ansi_fg_rgb[182,118,182]%@ext["%tmp_file2use%"]
                                                echos %ansi_color_reset%: %@IF[%@len[%@ext[%tmp_file2use%]] lt 4, ,]%faint_on%%italics_on%
                                                if "0" != "%ADSTAG_DISPLAY_FOR_PATH%" echos %@path[%tmp_file2use%]
                                                echos %@unquote[%@name["%tmp_file2use%"]]
                                                echo .%faint_off%%italics_off%%@ansi_fg[124,124,124]%@ext[%tmp_file2use%]%faint_off%%italics_off%%conceal_on%☼%conceal_off%
                                        goto :endif_351
                                :endif_351
                        :endif_353
        return

:END

        goto :skip_subroutines
                :divider []
                        rem Use my pre-rendered rainbow dividers, or if they don’t exist, just generate a divider dynamically
                        set wd=%@EVAL[%_columns - 1]
                        set nm=%bat%\dividers\rainbow-%wd%.txt
                        iff exist %nm% then
                                echo typing it...  %+ *pause>nul
                                *type %nm%
                                if "%1" != "NoNewline" .and. "%2" != "NoNewline" .and. "%3" != "NoNewline" .and. "%4" != "NoNewline" .and. "%5" != "NoNewline"  .and. "%6" != "NoNewline" (echos %NEWLINE%%@ANSI_MOVE_TO_COL[1])
                        else
                                echo echo’ing it...  %+ *pause>nul
                                echo %@char[27][93m%@REPEAT[%@CHAR[9552],%wd%]%@char[27][0m
                        endiff
                return
        :skip_subroutines

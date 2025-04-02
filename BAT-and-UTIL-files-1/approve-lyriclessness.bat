@loadbtm on
@Echo Off
@on break cancel

rem CONFIGURE DEFAULTS:
        set config_are_you_sure_answer=yes
        set config_are_you_sure_wait=10
        if not defined PLAYER_COMMAND set PLAYER_COMMAND=call preview-audio-file                                %+ rem should probably be synced with the one defined in our main get-lyrics/karaoke scripts

rem Validate environment:
        iff "1" != "%validated_approve_lyriclessness_4%" then
                call validate-in-path               get-lyrics-for-file.btm approve-lyriclessness-for-file.bat AskYN warning_soft error fatal_error divider preview-audio-file.bat
                call validate-environment-variables config_are_you_sure_wait config_are_you_sure_answer  color_advice color_normal italics_on italics_off bat ansi_color_yellow ansi_color_bright_yellow ansi_color_bright_green ansi_color_prompt ansi_color_important star2 faint_on faint_off
                if not defined filemask_audio call validate-environment-variables FILEMASK_AUDIO skip_validation_existence
                set  validated_approve_lyriclessness_4=1
        endiff

rem Usage:
        iff "%1" == "" then
                %color_advice%
                echo.
                echo USAGE: %0 metallica*.txt    —— to approve many audio files for lyriclessness in the folder (using wildcards)
                echo USAGE: %0 a_single_file.mp3 —— to approve one  audio file  for lyriclessness in the folder (using a filename)
                echo USAGE: %0 all               —— to approve ALL  audio files for lyriclessness in the folder (using 'all' mode)
                echo USAGE: %0 *                 —— to approve ALL  audio files for lyriclessness in the folder (using 'all' mode)
                echo USAGE: %0 ask               —— to approve ALL  audio files for lyriclessness with a prompt asking for each one
                echo USAGE: %0 ask force         —— to approve ALL  audio files for lyriclessness with a prompt asking for each one EVEN IF IT WAS ALREADY MARKED AS “DISAPPROVED” FOR LYRICLESSNESS
                echo.
                echo USAGE: add “force” to command line to skip confirmation question.
                %color_normal%
                goto /i END
        endiff


rem Deal with “ask” invocation, and set param_force
        iff "%1" == "ask" then
                set ask=1
                shift
                                    set ask_without_params=0
                if "%1" == ""       set ask_without_params=1
                                    set param_force=0
                if "%1" == "FORCE" (set param_force=1 %+ shift)
        else
                set ask=0
        endiff
        if "%2" == "FORCE" (set param_force=1)
        if "%1" == "FORCE" (set param_force=1 %+ shift)

rem Deal with “all” / “*.*” / “*” / “*.mp3” / “*.flac”  invocations:
        set ask_for_confirmation_for_approving_lyriclessness=0
        if "%1" == "all" .or. "%1" == "*.*" .or. "%1" == "*" .or. "%1" == "*.mp3" .or. "%1" == "*.flac" .or. "1" == "%ask_without_params%" .or. "1" == "%param_force%" (set ask_for_confirmation_for_approving_lyriclessness=1 %+ goto :endpoint_deal_with_params_53)
        set tmp_regex_result=%@Regex[[\*\?],%1$]
        if  "1" == "%tmp_regex_result%"  set ask_for_confirmation_for_approving_lyriclessness=1
        :endpoint_deal_with_params_53
        rem echo ask_for_confirmation_for_approving_lyriclessness=“%ask_for_confirmation_for_approving_lyriclessness%” %+ pause


rem Warn them if their invocation may affect several files:
        if  "1" != "%ask_for_confirmation_for_approving_lyriclessness%" goto :skip_that_block
        if "%2" eq "force"  (echo param2 is force %+ goto :process_by_environment_filemask)
        call warning_soft  "About to approve multiple songs for lyric%italics_on%lessness%italics_off% in folder..."

rem Ask for confirmation if our logic says we should:
        if "1" == "%ask%" goto :skip_main_ask
                unset /q answer
                call AskYN "You sure" %config_are_you_sure_answer% %config_are_you_sure_wait%
                if "%answer%" != "Y" goto :end
        :skip_main_ask


rem Branching:
        if ""  == "%1$"            goto process_by_environment_filemask
        if "1" != "%PARAM_FORCE%"  goto process_by_cli_filemask



rem If we have the “force” process, do it:
        :process_by_environment_filemask
                rem check environment:
                        if not defined filemask_audio call validate-environment-variable filemask_audio skip_validation_existence

                rem Do it for everything:
                        for %%temp_fileeee in (%filemask_audio%) do gosub process2 "%@UNQUOTE["%temp_fileeee%"]"
                goto :END

rem Goto endpoint:
        :skip_that_block

rem Deal with all other invocations:
        :process_by_cli_filemask
        for %%tmpppfile in (%1$) do gosub process "%@UNQUOTE["%tmpppfile%"]" 
        goto :END

rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                goto :skip_process2_definition
                        :process2 [tmpfile]
                                rem Skip if it’s already been marked instrumental or lyricless:
                                        if "1" != "%ask" goto :skip_the_skipping
                                                rem echo tmpfile is %tmpfile% !!!!!!!!!!!!!!!!!!!
                                                rem if "1" eq "%@RegEx[instrumental,%@unquote["%tmpfile%"]]" goto nevermind_this
                                                    set OUR_LL_VAL=%@execstr[type "%@unquote["%tmpfile%"]:lyriclessness">&>nul]
                                                    set OUR_IN_VAL=%@Regex[instrumental,"%@UNQUOTE["%tmpfile%"]"]
                                                    if            "1" == "%OUR_IN_VAL%" (gosub divider %+ echo  %no% Already marked instrumental:    %tmpfile%           %+ echo. %+ goto :nevermind_this)
                                                    if     "APPROVED" == "%OUR_LL_VAL%" (gosub divider %+ echo  %no% Already marked lyricless:       %tmpfile%           %+ echo. %+ goto :nevermind_this)
                                                    if "1" == "%param_force%" goto :nvm_1
                                                            if "NOT_APPROVED" == "%OUR_LL_VAL%" (gosub divider %+ echo  %no% Already marked NOT lyricless:   %tmpfile%   %+ echo. %+ goto :nevermind_this)
                                                    :nvm_1
                                                    if  exist "%@name["%tmpfile%"].lrc" (gosub divider %+ echo  %no% Already have LRC:               %tmpfile%           %+ echo. %+ goto :nevermind_this)
                                                    if  exist "%@name["%tmpfile%"].srt" (gosub divider %+ echo  %no% Already have SRT:               %tmpfile%           %+ echo. %+ goto :nevermind_this)
                                        :skip_the_skipping


                                rem Ask about it if we are supposed to:
                                        :ask_user
                                        gosub divider
                                        unset /q ANSWER
                                        if "1" != "%ask%" set  do_it=1
                                        if "1" != "%ask%" goto do_not_check
                                        set do_it=0
                                        echo %ansi_color_important%%star2% Filename: %faint_on%%@unquote[%tmpfile]%faint_off%
                                        call AskYN "Approve lyriclessness? [%ansi_color_bright_green%I%ansi_color_prompt%=mark as instrumental,%ansi_color_bright_green%P%ansi_color_prompt%=Preview]" no 90 IPL I:mark_as_instrumental,P:play,L:mark_lyricless
                                        if "Y" == "%ANSWER%" .or. "L" == "%ANSWER%" set do_it=1

                                rem Deal with the answer:
                                        :do_not_check
                                        if "1" == "%do_it%"  call      approve-lyriclessness-for-file.bat                                   "%@UNQUOTE["%tmpfile%"]"
                                        if "N" == "%ANSWER%" call   disapprove-lyriclessness-for-file.bat                                   "%@UNQUOTE["%tmpfile%"]"
                                        if "P" == "%ANSWER%" gosub "%BAT%\get-lyrics-for-file.btm"        check_for_answer_of_P             "%@UNQUOTE["%tmpfile%"]" 
                                        if "I" == "%ANSWER%" gosub "%BAT%\get-lyrics-for-file.btm"        rename_audio_file_as_instrumental "%@UNQUOTE["%tmpfile%"]" 
                                        if "P" == "%ANSWER%" goto :ask_user

                                :nevermind_this
                        return
                :skip_process2_definition

rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━



rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                rem Subroutine to speedup calls to divider.bat:
                        :divider
                                iff %_columns eq %LAST_NUM_COLUMNS then
                                       echo %LAST_DIVIDER%
                                else
                                       call divider
                                endiff
                        return

                rem Subroutine to processs each file:
                        :process [tmpfile]
                                rem echo %ansi_color_yellow%:process [%tmpfile%]
                                set file=%@unquote["%tmpfile"]
                                if exist "%file%" goto :file_exists
                                                  call error "File '%italics_on%%file%%italics_off%' does not exist"
                                                  goto :file_did_not_exist

                                        :file_exists
                                                unset /q ANSWER
                                                if "1" == "%ask%" goto :ask_yes
                                                                  goto :ask_no
                                                                  
                                                        :ask_yes
                                                                set do_it=0
                                                                call AskYN "Approve lyriclessness for %italics_on%“%@unquote[%tmpfile]”%italics_off%"
                                                                if "Y" == "%ANSWER%" set do_it=1
                                                        goto :ask_done

                                                        :ask_no
                                                                set do_it=1
                                                        goto :ask_done

                                                :ask_done
                                                if "1" == "%do_it%" call approve-lyriclessness-for-file.bat "%file%"
                                        :file_did_not_exist                       
                        return

rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━



:END


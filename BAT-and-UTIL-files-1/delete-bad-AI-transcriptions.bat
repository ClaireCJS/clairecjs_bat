@loadbtm on
@Echo Off
 on break cancel


rem Halt condition:
        set dir_txt=%italics_on%%faint_on%%[_CWP]%faint_off%%italics_off%%ansi_color_normal% 
        iff not exist *.srt;*.lrc;*.txt then
                title %_CWP
                echo %ansi_color_warning_soft%%star2% %underline_on%No%underline_off%%zzzzzz% %italics_on%bad AI transcriptions%italics_off% %@cursive_plain[to] delete %@cursive_plain[in]: %dir_txt% %+ goto /i END %+ else
                echo %ansi_color_run%%zzzzzzz%%star2% Looking %@cursive_plain[for]%zzzzzzzzz% %italics_on%bad AI transcriptions%italics_off% %zzzzzzzzzzzzzzzzzzzzzzzzz%%@cursive_plain[in]: %dir_txt%
        endiff


rem Grab parameter:
        set PARAM1=%1

rem Validate environment (once):
        iff "1" != "%validated_dbaitrr%" then
                call validate-in-path grep insert-before-each-line.py insert-after-each-line.py run-piped-input-as-bat.bat askyn del-maybe-after-review uniq sed fatal_error
                call validate-environment-variables ansi_color_unimportant ansi_color_important_less ansi_color_normal star2 ansi_color_bright_green ansi_color_bright_blue ansi_color_prompt faint_on faint_off italics_off italics_on ansi_erase_to_eol  faint_on faint_off ansi_color_warning_soft ansi_cursor_invisible ansi_cursor_visible underline_on underline_off star star2 star3 star4 check 
                call validate-is-function ansi_move_to_col randcursor ANSI_MOVE_RIGHT randfg_soft cursive cursive_plain
                set  validated_dbaitrr=1
        endiff

rem Get mode type:
        unset /q BAD_TRANSCRIPTION_DELETE_MODE ANSWER
        :re_ask_delete_bad_ai_transcription_mode
        iff "%PARAM1%" == "1" .or. "%PARAM1%" == "2" .or. "%PARAM1%" == "3"  then
                SET BAD_TRANSCRIPTION_DELETE_MODE=%PARAM1%
        else
                call AskYN "%ansi_color_bright_green%1%ansi_color_prompt%=Delete automatically, %ansi_color_bright_green%2%ansi_color_prompt%=ask for each deletion, or %ansi_color_bright_green%3%ansi_color_prompt%=review before for each deletion" 0 0 123 1:delete_automatically,2:ask_for_each_deletion,3:review_before_deleting
                iff "%answer%" == "1" .or. "%answer%" == "2" .or. "%answer%" == "3" then
                        set BAD_TRANSCRIPTION_DELETE_MODE=%ANSWER%
                else
                        call fatal_error "what kind of answer is “%ANSWER%”"
                endiff
        endiff

rem Create meaningfully-named temporary file:
        set NUM_STEPS=20
        set NUM_STEPS=12
        set NUM_STEPS=13
        set     step_num=1
        gosub   step
        call set-tmp-file "kill bad AI transcriptions filelist A1_original"               %+  set tmpfile1=%tmpfile%.lst
        call set-tmp-file "kill bad AI transcriptions filelist A2_unique"                 %+  set tmpfile2=%tmpfile%.bat
        call set-tmp-file "kill bad AI transcriptions filelist A3_with inserts"           %+  set tmpfile3=%tmpfile%.bat
        call set-tmp-file "kill bad AI transcriptions filelist B1_combined_lyr_and_sub"   %+  set tmpfile8=%tmpfile%.lst
        call set-tmp-file "kill bad AI transcriptions filelist B2_just the filenames"     %+  set tmpfile7=%tmpfile%.lst
        call set-tmp-file "kill bad AI transcriptions script to run"                      %+  set tmpfile9=%tmpfile%.bat

rem Determine the command that handles our situation correctly based on the mode:
        iff     "1" == "%BAD_TRANSCRIPTION_DELETE_MODE%" then set PROCESSING_COMMAND_TO_USE=*del /Ns
        elseiff "2" == "%BAD_TRANSCRIPTION_DELETE_MODE%" then set PROCESSING_COMMAND_TO_USE=*del /Ns /p
        elseiff "3" == "%BAD_TRANSCRIPTION_DELETE_MODE%" then set PROCESSING_COMMAND_TO_USE=call del-maybe-after-review.bat
        endiff

rem ACTUALLY SEARCH FOR BAD AI TRANSCRIPTIONS!!!
                                                rem either LRCget or LyricsGenius.exe seems to have chosen “Lady In Red” by Chris DeBurg for TONS AND TONS of inapplicable songs, as well as “Black City” by Voivod:
                                                goto :skip_old_way
                                                        gosub step %+ if exist *.srt                              (grep -li this.is.the.first.sentence                                 *.srt >>:u8 %tmpfile1%) %+ rem WhisperAI silence hallucination
                                                        gosub step %+ if exist *.lrc                              (grep -li this.is.the.first.sentence                                 *.lrc >>:u8 %tmpfile1%) %+ rem WhisperAI silence hallucination
                                                        gosub step %+ if exist *.txt                              (grep -li this.is.the.first.sentence                                 *.txt >>:u8 %tmpfile1%) %+ rem WhisperAI silence hallucination
                                                        gosub step %+ if exist *.srt                              (grep -li and.we.are.back                                            *.srt >>:u8 %tmpfile1%) %+ rem WhisperAI silence hallucination
                                                        gosub step %+ if exist *.lrc                              (grep -li and.we.are.back                                            *.lrc >>:u8 %tmpfile1%) %+ rem WhisperAI silence hallucination
                                                        gosub step %+ if exist *.txt                              (grep -li and.we.are.back                                            *.txt >>:u8 %tmpfile1%) %+ rem WhisperAI silence hallucination
                                                        gosub step %+ if exist *.srt                              (grep -li a.little.pause\.\.\.                                       *.srt >>:u8 %tmpfile1%) %+ rem WhisperAI silence hallucination
                                                        gosub step %+ if exist *.lrc                              (grep -li a.little.pause\.\.\.                                       *.lrc >>:u8 %tmpfile1%) %+ rem WhisperAI silence hallucination
                                                        gosub step %+ if exist *.txt                              (grep -li a.little.pause\.\.\.                                       *.txt >>:u8 %tmpfile1%) %+ rem WhisperAI silence hallucination
                                                        gosub step %+ if exist *.srt except /Ne ("*lady in red*") (grep -li "I.ve never seen you looking so lovely as you did tonight" *.srt >>:u8 %tmpfile1%) %+ rem Chris DeBurg - Lady In Red
                                                        gosub step %+ if exist *.lrc except /Ne ("*lady in red*") (grep -li "I.ve never seen you looking so lovely as you did tonight" *.lrc >>:u8 %tmpfile1%) %+ rem Chris DeBurg - Lady In Red
                                                        gosub step %+ if exist *.txt except /Ne ("*lady in red*") (grep -li "I.ve never seen you looking so lovely as you did tonight" *.txt >>:u8 %tmpfile1%) %+ rem Chris DeBurg - Lady In Red
                                                        gosub step %+ if exist *.srt except /Ne ( "*black city*") (grep -li "Closed lamps, curfews, dead leaves"                       *.srt >>:u8 %tmpfile1%) %+ rem Voivod - Black City
                                                        gosub step %+ if exist *.lrc except /Ne ( "*black city*") (grep -li "Closed lamps, curfews, dead leaves"                       *.lrc >>:u8 %tmpfile1%) %+ rem Voivod - Black City
                                                        gosub step %+ if exist *.txt except /Ne ( "*black city*") (grep -li "Closed lamps, curfews, dead leaves"                       *.txt >>:u8 %tmpfile1%) %+ rem Voivod - Black City
                                                :skip_old_way

rem ACTUALLY SEARCH FOR BAD AI TRANSCRIPTIONS!!!

        rem either LRCget or LyricsGenius.exe seems to have chosen “Lady In Red” by Chris DeBurg for TONS AND TONS of inapplicable songs, as well as “Black City” by Voivod:
                :new_way
                rem POSSIBLE ONE: “Oh, honey, wait for me.”
                gosub step %+ if exist *.srt;*.lrc;*.txt   (grep -i .                               *.srt *.lrc *.txt   >>:u8 %tmpfile8% >&>nul) %+ rem smush all files we are probing into a single file for speedup
                gosub step %+ (grep    VAD.chunk.*-.[0-9]                                           %tmpfile8%          >>:u8 %tmpfile1%       ) %+ rem WhisperAI temporary file
                gosub step %+ (grep -i this.is.the.first.sentence                                   %tmpfile8%          >>:u8 %tmpfile1%       ) %+ rem WhisperAI silence hallucination
                gosub step %+ (grep -i and.we.are.back                                              %tmpfile8%          >>:u8 %tmpfile1%       ) %+ rem WhisperAI silence hallucination
                gosub step %+ (grep -i a.little.pause\.\.\.                                         %tmpfile8%          >>:u8 %tmpfile1%       ) %+ rem WhisperAI silence hallucination
                gosub step %+ (grep -i "I.ve never seen you looking so lovely as you did tonight"   %tmpfile8%          >>:u8 %tmpfile1%       ) %+ rem incorrectly-placed lyrics: “Chris DeBurg - Lady In Red” 
                gosub step %+ (grep -i "Closed lamps, curfews, dead leaves"                         %tmpfile8%          >>:u8 %tmpfile1%       ) %+ rem incorrectly-placed lyrics:       “Voivod - Black City” 
                if "%@FILESIZE[%tmpfile1%]" == "0" (repeat 5 gosub step %+ goto :nothing_to_do)                         

        rem Set options for del-maybe-after-review:
                set EVEN_MORE_PROMPT_TEXT=,%ansi_color_bright_green%P%ansi_color_prompt%=Play,%ansi_color_bright_green%Q%ansi_color_prompt%=enqueue
                set EVEN_MORE_EXTRA_LETTERS=PQ

        rem create scripts:
                set                                 EXTRACT_FILENAME=sed -s "s/:.*$//ig"
                echo @Echo off                                                                                               >:u8 %tmpfile9%
                echo "%_CWP"                                                                                                >>:u8 %tmpfile9%
                echo on break cancel                                                                                        >>:u8 %tmpfile9%
                echo echo.                                                                                                  >>:u8 %tmpfile9%
                gosub step %+ type %tmpfile1% |:u8 %EXTRACT_FILENAME%                                                       >>:u8 %tmpfile7%
                gosub step %+ type %tmpfile7% |:u8 uniq                                                                     >>:u8 %tmpfile2%
                gosub step %+ type %tmpfile2% |:u8 insert-before-each-line.py "%PROCESSING_COMMAND_TO_USE% {{{{QUOTE}}}}"   >>:u8 %tmpfile3%
                gosub step %+ type %tmpfile3% |:u8  insert-after-each-line.py "{{{{QUOTE}}}}"                               >>:u8 %tmpfile9%
                echos %@ANSI_MOVE_TO_COL[0]%ANSI_ERASE_TO_EOL%

        rem Run script if it exists:
                rem echo %ANSI_COLOR_DEBUG%- DEBUG: executing: %italics_on%%tmpfile9%%italics_off%%newline%%ansi_color_bright_yellow% %+ type %tmpfile9%
                set deletebadaitmpscriptfile=%tmpfile9%
                gosub step
                echos %CHECK%%ansi_erase_to_eol%
                if exist %tmpfile9% call %tmpfile9%
                rem echo %ANSI_COLOR_DEBUG%- DEBUG: done executing: %italics_on%%tmpfile9%%italics_off%

        rem Of course this opens a new issue which is.... If any lyric to any song is LEGITIMATELY “and we are back”, or other catch-phrases ... then we’re in a bit of a pickle
                :nothing_to_do
                echos %@ANSI_MOVE_TO_COL[0]%ANSI_ERASE_TO_EOL%
                goto :END

rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

        :step []                                                                             
                echos %@ansi_move_to_col[0]%star3% %ansi_color_important_less%%faint_off%Looking %@cursive_plain[for]%faint_off% %italics_on%%underline_on%bad%underline_off% AI transcriptions%italics_off%%@randfg_soft[].%@randfg_soft[].%@randfg_soft[].  %ansi_color_bright_blue%Step%ansi_color_important% %step_num% %ansi_color_bright_blue%of%ansi_color_important% %NUM_STEPS%%@randfg_soft[].%@randfg_soft[].%@randfg_soft[].%@randcursor[] ``
                set len_diff=%@EVAL[%@LENGTH[%num_steps%] - %@LENGTH[%step_num%]]
                if %len_diff% gt 0 repeat %len_diff% echos %@ANSI_MOVE_RIGHT[1]

                rem call  inline-progress-bar %step_num% %num_steps%
                    gosub inline_progress_bar %step_num% %num_steps%

                set step_num=%@EVAL[ %step_num% + 1 ]
        return

                :inline_progress_bar [step_num num_steps]                                                                
                        set current_column=%_COLUMN
                        set        columns=%_COLUMNS
                        set       distance=%@EVAL[%columns - %current_column% - 1]
                        set       progress=%@EVAL[%@FLOOR[%@EVAL[((%step_num / %num_steps) * distance) + .5]]  ] 
                        set      remaining=%@EVAL[%distance - %progress]
                        echos %ansi_cursor_invisible%%ansi_color_success%%@repeat[=,%progress%]`>`%@randfg_soft[]%@repeat[%@char[9473],%remaining%]%@ANSI_MOVE_TO_COL[%_COLUMN]%ansi_cursor_visible%
                return

rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

:END
        unset /q step_num
        echos %ansi_color_normal%
        title %_CWP

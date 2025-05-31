@Echo off
@loadbtm on
@on break cancel


rem Validate environment once per session:
        iff "1" != "%validated_claitrfi%" then
                call validate-in-path fast_cat important less_important sort uniq insert-before-each-line.py insert-after-each-line.py run-piped-input-as-bat.bat everything 
                set validated_claitrfi=1
        endiff

rem Take note of how much was free before we started:
        set FREE_C_BEFORE=%@DISKFREE[c]

rem Delete files that could be anywhere:

        rem If we are mis-using this script for things outside it’s original intention❟ branch to that...
        rem .....Otherwise❟ do what this script was made for: Cleaning up AI-transcription trash files!
                if "%1" == "audit-music-files" goto :unrelated_overloaded_functionality
                        call less_important "Erasing trash AI transcription files..."
                        rem If these filename values changes, also update the AI_TRASH_FILES variable in report-lyric-and-subtitle-percentage-completion.bat
                        rem skip for now: gosub DeleteEverywhere .LastInvalidAITranscriptionCheck %+ rem Relates to delete-bad-AI-transcriptions.bat, which is designed to not be re-run every 72 hours. However, upon reboot, we will clean up the trash so that these files don’t stick around forever once we stop using that component
                        gosub DeleteEverywhere               *._vad_collected_chunks*.wav
                        gosub DeleteEverywhere               *._vad_collected_chunks*.srt
                        gosub DeleteEverywhere               *._vad_original*.srt
                        gosub DeleteEverywhere               *._vad_pyannote_*chunks*.wav
                        gosub DeleteEverywhere               *._vad_pyannote_v3.txt

                        iff "%1" == "do_not_delete_BATs" goto :do_not_delete_BATs
                                gosub DeleteEverywhere  create-the-missing-karaokes-here-temp*.bat
                                gosub DeleteEverywhere       get-the-missing-lyrics-here-temp*.bat
                                gosub DeleteEverywhere      get-the-missing-karaoke-here-temp*.bat
                                rem   DeleteEverywhere      __ %+ rem this didn’t work and tried to “get __*.*”
                        :do_not_delete_BATs
                if "%1" == "" goto :DoneDeletingBecauseThisIsANormalInvocation


        rem Here is where we started adding unrelated tasks to this script in an ugly-but-convenient fashion:
                :━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                :unrelated_overloaded_functionality

                
                        rem Detritus from audit-music-files.py:
                                if "%1" == "audit-music-files" (
                                        gosub DeleteEverywhere  RG_fix.bat
                                        gosub DeleteEverywhere  RG_no.dat
                                        gosub DeleteEverywhere  RG_no.dat.bak.*
                                        gosub DeleteEverywhere  RG_yes.dat
                                        gosub DeleteEverywhere  RG_yes.dat.bak.*
                                )

                :━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━



rem Now❟ back to business as usual:
        :DoneDeletingBecauseThisIsANormalInvocation

rem Take note of how much was free after we started finished — though these scripts are small, so "megabytes" is too big of a unit for this situation:
        set FREE_C_AFTER=%@DISKFREE[c]
        
rem Calculate and display how much space we saved:       
        rem In Megs:
                set SPACE_SAVED_MEGS=%@FORMATN[01.0,%@EVAL[(%FREE_C_AFTER - %FREE_C_BEFORE)/1000000]]
                set SPACE_SAVED_MEGS_PRETTY=%@COMMA[%SPACE_SAVED_MEGS]
                iff "%@NAME[%_PBATCHNAME]" != "free-up-harddrive-space" then        
                        echos     `` 
                        call less_important.bat "Saved %bold%%SPACE_SAVED_MEGS_PRETTY%%bold_off% megs"
                endiff
        rem In Gigs:        
                rem SPACE_SAVED_GIGS=%@FORMATN[01.0,%@EVAL[(%FREE_C_AFTER - %FREE_C_BEFORE)/1000000000]]
                rem SPACE_SAVED_GIGS_PRETTY=%@COMMA[%SPACE_SAVED_GIGS]
                rem       `` %+ call less_important.bat "Saved %bold%%SPACE_SAVED_GIGS_PRETTY%%bold_off% gigs"
                
rem Calculate and display how much free space is left overall:
        rem In Gigabytes and Terabites:
                set FREE_GIGABYTES=%@FORMATN[1.1,%@EVAL[%@DISKFREE[c]/1000000000]]
                set FREE_TERABYTES=%@FORMATN[1.2,%@EVAL[%@DISKFREE[c]/1000000000000]]
                iff "%@NAME[%_PBATCHNAME]" != "free-up-harddrive-space" then        
                        echos     `` 
                        call less_important "%ANSI_COLOR_IMPORTANT%Free space now: %FREE_TERABYTES%%blink_on%T%blink_off% (%FREE_GIGABYTES%%blink_on%G%blink_off%)"
                endiff
goto :END

rem ———————————————————————————————————————————————— SUBROUTINES: BEGIN ————————————————————————————————————————————————
        rem Delete a file, but only if it exists:
                :DelIfExists [files_param]
                        set files="%@UNQUOTE[%files_param]"
                        if not exist %files% return
                        if     exist %files% (*del /e /s /a: /f /k /L /X /Y /Z %files%) >nul
                        rem echos %ansi_restore_position%%@repeat[ ,%@len[%@name[%files_param%]]]
                return
        rem Create a folder if it is no longer exists:                
                :CreateIfGone [dir_param]
                        set dir="%@UNQUOTE[%dir_param]"
                        if not isdir %dir% (mkdir /s %dir%)
                        if not isdir %dir% (call error.bat "Problem when creating “%italics_on%%dir%%italics_off%”!")
                return

        rem Delete a file no matter where it exists on all of our harddrives:
                :deleteEverywhere [file]
                        rem Let us know which filename we are on the hunt for:
                                set file="%@UNQUOTE[%file]"                                             %+ rem Strip quotes off filename
                                echos         %ANSI_RESET%``                                            %+ rem Indent this part
                                call less_important "looking for “%italics_on%%file%%italics_off%”"     %+ rem Indented "looking for {filename}" message
                                echos %@randfg_soft[]%@randcursor[]
                        
                        rem Find all instances of the file [found via everything] we are deleting, pipe to sort-and-uniq to dedupe it, then insert "del-if-exists" [and a quote] before it, a quote after it, then pipe *all that* directly to the command line, then pipe it to fast_cat to fix ansi rendering errors:
                        rem Be damn sure you know what you’re doing if you change this. Best put an "echo " before the "*del" and test it out if you do.
                                call set-tmp-file "deleting AI trash"
                                (((*everything "%file%" |:u8 sort |:u8 uniq ) |:u8 insert-before-each-line.py "call del-if-exists {{{{QUOTE}}}}")   |:u8 insert-after-each-line.pl "{{{{QUOTE}}}}") >:u8 %tmpfile%.bat
                                call %tmpfile%.bat |:u8 fast_cat

                                rem echo All done? %+ pause
                                rem echos %@randfg_soft[]%@randcursor[]
                return
        :skip_subroutine_definitions
rem ———————————————————————————————————————————————— SUBROUTINES: END —————————————————————————————————————————————————

:END

rem Cosmetic resets:
        %COLOR_NORMAL%
        call fix-window-title





@on break cancel
@echo off


call validate-environment-variables LOCALAPPDATA TEMP TMPDIR 
call validate-in-path important.bat fast_cat
call validate-in-path important less_important sort uniq insert-before-each-line run-piped-input-as-bat.bat fast_cat everything everything.exe everything.bat clean-up-AI-transcription-trash-files.bat



rem Start, and take note of how much was free before we started:
        call less_important "Freeing up harddrive space..."
        set FREE_C_BEFORE=%@DISKFREE[c]


REM If you use a *.* filemask you need to also call CreateIfGone because IT WILL REMOVE THE FOLDER TOO if you use *.*
REM If you use a *.* filemask you need to also call CreateIfGone because IT WILL REMOVE THE FOLDER TOO if you use *.*
REM If you use a *.* filemask you need to also call CreateIfGone because IT WILL REMOVE THE FOLDER TOO if you use *.*
REM If you use a *.* filemask you need to also call CreateIfGone because IT WILL REMOVE THE FOLDER TOO if you use *.*
REM If you use a *.* filemask you need to also call CreateIfGone because IT WILL REMOVE THE FOLDER TOO if you use *.*

gosub DelIfExists "%LOCALAPPDATA%\Binary Fortress Software\DisplayFusion\CrashDumps\*.dmp"
gosub DelIfExists  %LOCALAPPDATA%\Temp\DiagOutputDir\RdClientAutoTrace\*.etl
gosub DelIfExists  %TEMP%\*.*
gosub DelIfExists  c:\tcmd\runonce-post-split*.bat
gosub CreateIfGone %TEMP%
gosub DelIfExists  %TMPDIR%\*.*
gosub CreateIfGone %TMPDIR%
gosub DelIfExists  c:\recycled\*.*
gosub CreateIfGone c:\recycled

rem Files that could be anywhere:

        rem AI lyric transcription:
                rem moved to separate AI-trash-cleanup bat: echo.
                rem moved to separate AI-trash-cleanup bat: gosub DeleteEverywhere               *._vad_collected_chunks*.wav
                rem moved to separate AI-trash-cleanup bat: gosub DeleteEverywhere               *._vad_original*.srt
                rem moved to separate AI-trash-cleanup bat: gosub DeleteEverywhere  create-the-missing-karaokes-here-temp.bat
                rem moved to separate AI-trash-cleanup bat: gosub DeleteEverywhere       get-the-missing-lyrics-here-temp.bat
                if "%USERNAME%" eq "Claire" call clean-up-AI-transcription-trash-files-everywhere.bat
    

        goto :skip_1
                :deleteEverywhere [file]
                        rem Be goddamned sure you know what you’re doing if you change this.  
                        rem Best put an "echo " before the "*del" and test it out if you do.
                        rem for %%GlobToDestroy in (*._vad_collected_chunks*.wav *._vad_original*.srt) 
                        set file="%@UNQUOTE[%file]"
                        echos         ``
                        call less_important "looking for “%file%”"
                        ((((*everything "%file%" |:u8 sort |:u8 uniq ) |:u8 insert-before-each-line.py "call del-if-exists {{{{QUOTE}}}}")   |:u8 insert-after-each-line.pl "{{{{QUOTE}}}}") |:u8 call run-piped-input-as-bat.bat) |:u8 fast_cat
                return
        :skip_1


set FREE_C_AFTER=%@DISKFREE[c]
set SPACE_SAVED_MEGS=%@FORMATN[01.0,%@EVAL[(%FREE_C_AFTER - %FREE_C_BEFORE)/1000000]]
set SPACE_SAVED_GIGS=%@FORMATN[01.0,%@EVAL[(%FREE_C_AFTER - %FREE_C_BEFORE)/1000000000]]
set SPACE_SAVED_MEGS_PRETTY=%@COMMA[%SPACE_SAVED_MEGS]
set SPACE_SAVED_GIGS_PRETTY=%@COMMA[%SPACE_SAVED_GIGS]
echos     `` %+ call less_important.bat "Saved %bold%%SPACE_SAVED_MEGS_PRETTY%%bold_off% megs"
echos     `` %+ call less_important.bat "Saved %bold%%SPACE_SAVED_GIGS_PRETTY%%bold_off% gigs"
set FREE_GIGABYTES=%@FORMATN[1.1,%@EVAL[%@DISKFREE[c]/1000000000]]
set FREE_TERABYTES=%@FORMATN[1.2,%@EVAL[%@DISKFREE[c]/1000000000000]]
echos     `` %+ call less_important "%ANSI_COLOR_IMPORTANT%Free space now: %FREE_TERABYTES%%blink_on%T%blink_off% (%FREE_GIGABYTES%%blink_on%G%blink_off%)"


goto :END
    :DelIfExists [files_param]
        rem echos %ansi_color_important%%ansi_save_position%%@name[%files_param%]
        %COLOR_REMOVAL%
        set files="%@UNQUOTE[%files_param]"
        if not exist %files% return
        if     exist %files% (*del /e /s /a: /f /k /L /X /Y /Z %files%) >nul
        rem echos %ansi_restore_position%%@repeat[ ,%@len[%@name[%files_param%]]]
    return
    :CreateIfGone [dir_param]
        %COLOR_SUCCESS%
        set dir="%@UNQUOTE[%dir_param]"
        if not isdir %dir% (mkdir /s %dir%)
        if not isdir %dir% (call error.bat "There’s still a problem when Creating %dir%!")
    return
:END
%COLOR_NORMAL%

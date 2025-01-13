@loadbtm on
@Echo Off
 @on break cancel
 set PARAMS=%*

rem CONFIGURE DEFAULTS:
        set are_you_sure_answer=yes
        set are_you_sure_wait=10

rem Usage:
        iff "%1" == "" then
                %color_advice%
                echo.
                echo USAGE: %0 metallica*.txt    —— to    approve many audio files for lyriclessness in the folder (using wildcards)
                echo USAGE: %0 a_single_file.mp3 —— to    approve one  audio file  for lyriclessness in the folder (using a filename)
                echo USAGE: %0 all               —— to    approve ALL  audio files for lyriclessness in the folder (using 'all' mode)
                echo USAGE: %0 all               —— to    approve ALL  audio files for lyriclessness in the folder (using 'all' mode)
                echo.
                echo USAGE: add “force” to command line to skip confirmation question.
                %color_normal%
                goto :END
        endiff
 

rem Deal “all” / “*.*” / “*” / “*.mp3” / “*.flac”  invocations:
        iff "%1" == "all" .or. "%1" == "*.*" .or. "%1" == "*" .or. "%1" == "*.mp3" .or. "%1" == "*.flac" then
                if "%2" eq "force" goto :force_1
                call warning_soft "About to approve multiple songs for lyric%italics_on%lessness%italics_off% in folder..."
                call AskYN        "You sure" %are_you_sure_answer% %are_you_sure_wait%
                if "%answer%" != "y" goto :end
                :force_1
                call validate-environment-variable filemask_audio
                for %%tmpfile in (%filemask_audio%) do (
                       @call    approve-lyriclessness-for-file.bat "%@unquote[%tmpfile]"
                )
                goto :END
        endiff

rem Deal with all other invocations:
        for %%tmpfile in (%PARAMS%) do (
                set file="%@unquote[%tmpfile]"
                if exist %file% (
                        call    approve-lyriclessness-for-file.bat %file%
                ) else (
                        call error "File '%italics_on%%file%%italics_off%' does not exist"
                )
        )        

:END

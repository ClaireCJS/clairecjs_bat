@Echo Off
 @on break cancel
 set PARAMS=%*
 
iff "%1" eq "" then
        %color_advice%
        echo.
        echo USAGE: %0 metallica*.txt    —— to disapprove many audio files for lyriclessness in the folder (using wildcards)
        echo USAGE: %0 a_single_file.mp3 —— to disapprove one  audio file  for lyriclessness in the folder (using a filename)
        echo USAGE: %0 all               —— to disapprove ALL  audio files for lyriclessness in the folder (using 'all' mode)
        %color_normal%
        goto :END
endiff
 

iff "%1" eq "all" .or. "%1" eq "*.*" .or. "%1" eq "*" .or. "%1" eq "*.mp3" .or. "%1" eq "*.flac" then
        call warning_soft "About to disapprove multiple songs for lyric%italics_on%lessness%italics_off% in folder..."
        call AskYN        "You sure" no 10
        if "%answer%" != "y" goto :end
        call validate-environment-variable filemask_audio
        for %%tmpfile in (%filemask_audio%) do (
               @call disapprove-lyriclessness-for-file.bat "%@unquote[%tmpfile]"
        )
        goto :END
endiff


for %%tmpfile in (%PARAMS%) do (
        set file="%@unquote[%tmpfile]"
        if exist %file% (
                call disapprove-lyriclessness-for-file.bat %file%
        ) else (
                call error "File '%italics_on%%file%%italics_off%' does not exist"
        )
)        



:END
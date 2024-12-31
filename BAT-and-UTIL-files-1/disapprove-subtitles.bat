@Echo OFF
 @on break cancel
 set PARAMS=%*

 iff "%1" == "" then
        %color_advice%
        echo.
        echo USAGE: %0 metallica*.txt    —— to disapprove many subtitles in the folder (using  wildcards)
        echo USAGE: %0 a_single_file.txt —— to disapprove one  subtitle  in the folder (using a filename)
        echo USAGE: %0 all               —— to disapprove ALL  subtitles in the folder (using ’all’ mode)
        %color_normal%
        goto :END
endiff


iff "%1" == "all" .or. "%1" == "*.*" .or. "%1" == "*" .or. "%1" == "*.srt" .or. "%1" == "*.lrc" then
        call warning_soft "About to disapprove ALL subtitles %italics_on%(*.srt,*.lrc)%italics_off% in folder..."
        call AskYN        "You sure" no 10
        if "%answer%" != "y" goto :end

        for %%tmpfile in (*.srt;*.lrc) do (
               @call disapprove-subtitle-file.bat "%@unquote[%tmpfile]"
        )
        goto :END
endiff


for %%tmpfile in (%PARAMS%) do (
        set file="%@unquote[%tmpfile]"
        if exist %file% (
                call disapprove-subtitle-file.bat %file%
        ) else (
                call error "File “%italics_on%%file%%italics_off%” does not exist"
        )
)        



:end


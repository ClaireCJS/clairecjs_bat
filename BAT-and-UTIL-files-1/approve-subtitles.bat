@Echo OFF
 @on break cancel
 set PARAMS=%*

iff "%1" eq "" then
        %color_advice%
        echo.
        echo USAGE: %0 metallica*.srt    —— to    approve many subtitles in the folder (using  wildcards)
        echo USAGE: %0 a_single_file.srt —— to    approve one  subtitle  in the folder (using a filename)
        echo USAGE: %0 all               —— to    approve ALL  subtitles in the folder (using 'all' mode)
        %color_normal%
        goto :END
endiff
 

iff "%1" eq "all" .or. "%1" eq "*.*" .or. "%1" eq "*" .or. "%1" eq "*.srt" .or. "%1" eq "*.lrc" then
        call warning_soft "About to approve ALL subtitles %italics_on%(*.srt,*.lrc)%italics_off% in folder..."
        call AskYN        "You sure" no 10
        if "%answer%" != "y" goto :end

        for %%tmpfile in (*.srt;*.lrc) do (
               @call    approve-subtitle-file.bat "%@unquote[%tmpfile]"
        )
        goto :END
endiff


for %%tmpfile in (%PARAMS%) do (
        set file="%@unquote[%tmpfile]"
        if exist %file% (
                call    approve-subtitle-file.bat %file%
        ) else (
                call error "File “%italics_on%%file%%italics_off%” does not exist"
        )
)        



:end


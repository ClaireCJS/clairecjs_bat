@Echo Off
 @on break cancel
 set PARAMS=%*
 
iff "%1" eq "" then
        %color_advice%
        echo.
        echo USAGE: %0 metallica*.txt    —— to approve matching lyrics in the folder (using wildcards)
        echo USAGE: %0 a_single_file.txt —— to approve ALL .txt lyrics in the folder (using a filename)
        echo USAGE: %0 all               —— to approve ALL .txt lyrics in the folder (using 'all' mode)
        %color_normal%
        goto :END
endiff
 

iff "%1" eq "all" .or. "%1" eq "*.*" .or. "%1" eq "*" .or. "%1" eq "*.txt" then
        call warning_soft "About to approve ALL lyrics %italics_on%(*.txt)%italics_off% in folder..."
        call pause-for-x-seconds 5 You sure?
        for %%tmpfile in (*.txt) do (
               @call approve-lyric-file.bat "%@unquote[%tmpfile]"
        )
        goto :END
endiff


for %%tmpfile in (%PARAMS%) do (
        set file="%@unquote[%tmpfile]"
        if exist %file% (
                call approve-lyric-file.bat %file%
        ) else (
                call error "File '%italics_on%%file%%italics_off%' does not exist"
        )
)        



:END
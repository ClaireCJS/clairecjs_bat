@Echo Off
@on break cancel
set PARAMS=%*

rem echo PARAMS=“%PARAMS%”, %%1=“%1”

iff "%1" == "" then
        %color_advice%
        echo.
        echo USAGE: %0 metallica*.txt    —— to    approve many txt lyrics in the folder (using wildcards)
        echo USAGE: %0 a_single_file.txt —— to    approve one .txt lyrics in the folder (using a filename)
        echo USAGE: %0 all               —— to    approve ALL .txt lyrics in the folder (using 'all' mode)
        %color_normal%
        goto :END
endiff
 

iff "%1" == "all" .or. "%1" == "*.*" .or. "%1" == "*" .or. "%1" == "*.txt" then
        call warning_soft "About to approve multiple lyrics %italics_on%(*.txt)%italics_off% in folder..."
        call AskYN        "You sure" no 10
        if "%answer%" != "y" goto :end
        
        for %%tmpfile in (*.txt) do (        
               @call    approve-lyric-file.bat "%@unquote[%tmpfile]"
        )
        goto :END
endiff


for %%tmpfile in (%PARAMS%) do (
        set file="%@unquote[%tmpfile]"
        if exist %file% (
                call    approve-lyric-file.bat %file%
        ) else (
                call error "File “%italics_on%%file%%italics_off%” does not exist"
        )
)        



:END
@loadbtm on
@Echo Off
@on break cancel
set PARAMS=%*


rem Ensure correct usage:
        iff "%1" == "" then
                %color_advice%
                echo.
                echo USAGE: %0 metallica*.txt —— to    approve many txt lyrics in the folder (using wildcards)
                echo USAGE: %0 SingleFile.txt —— to    approve one .txt lyrics in the folder (using a filename)
                echo USAGE: %0 all            —— to    approve ALL .txt lyrics in the folder (using 'all' mode)
                echo USAGE: Add “Force” as 2ⁿᵈ parameter to skip warning prompt, i.e. "approve-lyrics *.txt force"
                %color_normal%
                goto :END
        endiff
 

rem Validate environment (once):
        iff "1" != "%validated_approve_lyrics" then
                call validate-in-path print-message warning_soft askyn error approve-lyric-file
                set validated_approve_lyrics=1
        endiff

rem “ALL” mode:
        iff "%1" == "all" .or. "%1" == "*.*" .or. "%1" == "*" .or. "%1" == "*.txt" then
                call warning_soft "About to approve multiple lyrics %italics_on%(*.txt)%italics_off% in folder..."

                unset /q anwer
                iff "%2" == "force" then
                        set answer=Y
                else
                        call AskYN        "You sure" no 10
                endiff
                if "%answer%" != "y" goto :end
                
                for %%tmpfile in (*.txt) do (        
                        call approve-lyric-file.bat "%@unquote[%tmpfile]"
                )
                goto :END
        endiff


rem Explicitly-named file mode:
        for %%tmpfile in (%PARAMS%) do (
                set file="%@unquote[%tmpfile]"
                if exist %file% (
                        call approve-lyric-file.bat %file%
                ) else (
                        call error "File %lq%%italics_on%%file%%italics_off%%rq% does not exist"
                )
        )        



:END

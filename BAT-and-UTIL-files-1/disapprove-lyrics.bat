@Echo OFF
 @on break cancel
 
iff exist %1 then
        for %%tmpfile in (%*) do (
               @call unapprove-lyric-file.bat "%@unquote[%tmpfile]"
        )        
else
        call warning_soft "About to disapprove ALL lyrics in folder..."
        pause
        for %%tmpfile in (*.txt) do (
               @call unapprove-lyric-file.bat "%@unquote[%tmpfile]"
        )
endiff

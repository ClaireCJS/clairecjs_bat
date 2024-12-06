@Echo OFF
 @on break cancel
 
iff exist %1 then
        for %%tmpfile in (%*) do (
               @call approve-lyric-file.bat "%@unquote[%tmpfile]"
        )        
else
        call warning_soft "About to approve ALL lyrics in folder..."
        pause
        for %%tmpfile in (*.txt) do (
               @call approve-lyric-file.bat "%@unquote[%tmpfile]"
        )
endiff

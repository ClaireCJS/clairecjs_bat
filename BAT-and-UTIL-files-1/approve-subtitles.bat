@Echo OFF
 @on break cancel
 
iff exist %1 then
        for %%tmpfile in (%*) do (
               @call approve-lyric-file.bat "%@unquote[%tmpfile]"
        )        
else
        for %%tmpfile in (*.srt;*.lrc) do (
               @call approve-lyric-file.bat "%@unquote[%tmpfile]"
        )
endiff

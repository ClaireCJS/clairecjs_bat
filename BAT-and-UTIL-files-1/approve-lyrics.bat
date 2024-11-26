@Echo OFF
 @on break cancel
 
for %%tmpfile in (%*) do (
       @call approve-lyric-file.bat "%@unquote[%tmpfile]"
)

@Echo OFF
 @on break cancel
 
for %%tmpfile in (*.txt) do (
       echo @call approve-lyric-file.bat "%@unquote[%tmpfile]"
)

@Echo OFF
 @on break cancel
 
for %%tmpfile in (*.lrc;*.srt) do (
       @call approve-lyric-file.bat "%@unquote[%tmpfile]"
)

@Echo OFF
@on break cancel
for %%tmpFile in (*.txt) do (
        @call unapprove-lyric-file.bat "%@unquote[%tmpFile]"
)        

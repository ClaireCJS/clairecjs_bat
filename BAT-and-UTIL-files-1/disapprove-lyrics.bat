@Echo OFF
@on break cancel
for %%tmpFile in (%*) do (
        @call unapprove-lyric-file.bat "%@unquote[%tmpFile]"
)        

@Echo OFF
@on break cancel
for %%tmpFile in (*.srt;*.lrc) do (
        @call unapprove-subtitle-file.bat "%@unquote[%tmpFile]"
)        

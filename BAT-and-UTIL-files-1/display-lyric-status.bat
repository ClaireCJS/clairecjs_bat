@Echo OFF
@on break cancel


set FILEMASK_TEMP=*.txt

iff "%1" ne "" then
        call validate-is-extension %1 *.txt "1ˢᵗ arg must be text file"
        call display-lyric-status-for-file %*
        goto :END
endiff


iff exist %FILEMASK_TEMP% then
        set USE_SPACER=1
        for %%tmpfile in (%FILEMASK_TEMP%) do (
                call display-lyric-status-for-file "%@UNQUOTE[%tmpFile]"
        )                
        set USE_SPACER=0
else
        call warning "No lyric files here." silent
endiff


:END
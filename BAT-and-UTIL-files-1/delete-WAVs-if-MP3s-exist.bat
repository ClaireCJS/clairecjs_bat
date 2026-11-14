@Echo off
 on break cancel

:DESCRIPTION: Delete a WAV if a companion MP3 exists 
:DESCRIPTION: Most probable use case is: the wav was converted to mp3 and is no longer needed


rem Validate environment (once):
        iff "1" != "%validated_deletewavifmp3sexist%" then
                call validate-in-path askyn randfg
                set  validated_deletewavifmp3sexist=1
        endiff


rem Purely cosmetic:
    if %1 eq "randcolor" (call randfg)


rem Get rid of redundant mp3s:
        for %tmpfile in (*.wav) if exist "%@NAME[%tmpfile].mp3" del "%@NAME[%tmpfile%].wav"


rem While we’re here, ask about redundant FLACs too:
        unset /q ANSWER
        call askyn "do flac too" no 60
        if "Y" == "%ANSWER%" for %tmpfile in (*.wav) if exist "%@NAME[%tmpfile].flac" del "%@NAME[%tmpfile%].wav"


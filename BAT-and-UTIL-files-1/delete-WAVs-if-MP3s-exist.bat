@Echo OFF

:DESCRIPTION: Delete a WAV if a companion MP3 exists 
:DESCRIPTION: Most probable use case is: the wav was converted to mp3 and is no longer needed

for %tmpfile in (*.wav) if exist "%@NAME[%tmpfile].mp3" del "%@NAME[%tmpfile%].wav"


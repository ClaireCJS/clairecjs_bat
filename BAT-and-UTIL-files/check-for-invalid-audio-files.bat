@Echo Off

:this is what's useful - look for files that aren't in our 3 primary accepted formats: MP3, FLAC, and WAV:
 dir /bs %filemask_audio%|gr -v \.mp3|gr -v \.flac|gr -v \.wav



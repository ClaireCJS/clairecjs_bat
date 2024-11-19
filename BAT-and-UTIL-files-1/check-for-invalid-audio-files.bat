@Echo Off
 on break cancel

:this is what's useful - look for files that aren't in our 3 primary accepted formats: MP3, FLAC, and WAV:
 dir /bs %filemask_audio%|:u8gr -v \.mp3|:u8gr -v \.flac|:u8gr -v \.wav



@Echo Off

rem Convert any WAV files to MP3:
        sweep if exist *.wav (call allfiles wav2mp3)

rem Delete Adobe Audition cruft:
        sweep if exist *.xmp (del             *.xmp)

rem If a wav+mp3 pair exists, delete the WAV:
        sweep call del-WAVs-if-mp3s-or-flacs-exist 



@Echo Off
 on break cancel


rem Make sure Adobe Audition is closed:
        :CloseAgain
            call warning "Make sure to close Adobe Audition!"
            pause
            call warning "It better be closed!"
            pause
            call isRunning adobe.*audition
            if  %isRunning eq 1 (call warning "It doesn't look like it's closed, actually." %+ goto :CloseAgain)

rem Convert any WAV files to MP3:
        sweep if exist *.wav (call allfiles wav2mp3)

rem Delete Adobe Audition cruft:
        sweep if exist *.xmp (del       *.pkf;*.xmp)

rem If a wav+mp3 pair exists, delete the WAV:
        sweep call del-WAVs-if-mp3s-or-flacs-exist 



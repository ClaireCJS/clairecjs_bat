@loadbtm on
@on break cancel
@Echo OFF

rem Validate the environment (once):
        iff "1" !=  "%validated_getlyricsforallsongsinthisdir%" then
                call validate-in-path              get-lyrics
                call validate-environment-variable filemask_audio
                set  validated_getlyricsforallsongsinthisdir=1
        else


rem Exclude temporary files from our for loop:
        for /[!*._vad_*_chunks*.wav] %file in (%filemask_audio%) do call get-lyrics "%file"


                       
                       

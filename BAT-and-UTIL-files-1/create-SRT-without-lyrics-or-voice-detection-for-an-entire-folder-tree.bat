@loadbtm on
@Echo OFF
 on break cancel

rem Gotta re-write this to basically just be an option create-lyrics uses.. then just sweep call that



iff 1 ne %validated_createsrtwolovdfaef% then 
        call validate-in-path Faster-Whisper-XXL.exe
        set  validated_createsrtwolovdfaef=1
endiff        


set            FILES=%1
if not defined FILES     (set FILES=%FILEMASK_AUDIO%)
if not defined FILES     (set FILES=*.mp3;*.wav;*.rm;*.voc;*.au;*.mid;*.stm;*.mod;*.vqf;*.ogg;*.mpc;*.wma;*.mp4;*.flac;*.snd;*.aac;*.opus;*.ac3)
if not defined FILES     (call fatal_error "must pass first parameter like *.mp3 or *.flac or have FILEMASK_AUDIO environment variable defined ... suggested value is *.mp3;*.wav;*.rm;*.voc;*.au;*.mid;*.stm;*.mod;*.vqf;*.ogg;*.mpc;*.wma;*.mp4;*.flac;*.snd;*.aac;*.opus;*.ac3" %+ goto :END)


set              COMMAND=Faster-Whisper-XXL.exe --model=large-v2   --language=en --output_dir "%_CWd" --output_format srt --vad_filter False --max_line_count 1 --max_line_width 20 --check_files --sentence    --batch_recursive %FILES% --verbose True
set LAST_WHISPER_COMMAND=%COMMAND%
                    echo %COMMAND%
                         %COMMAND% |:u8 copy-move-post whisper -twhisper.log
                         

:END

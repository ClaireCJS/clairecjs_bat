@loadbtm on
@Echo Off
@on break cancel

rem Redundant environment variable creation in case this is being run without its requirements (good luck with that):
        iff not defined filemask_audio then
                set FILEMASK_AUDIO=*.mp3;*.wav;*.rm;*.voc;*.au;*.mid;*.stm;*.mod;*.vqf;*.ogg;*.mpc;*.wma;*.mp4;*.flac;*.snd;*.aac;*.opus;*.ac3 
        endiff
 
  
rem Validate environment (once):
        iff "1" != "%validated_ctmkh%" then
                call validate-in-path               less_important check-for-missing-karaoke clean-up-AI-transcription-trash-files-here
                call validate-environment-variables ansi_colors_have_been_set emoji_have_been_set star
                rem no need to validate filemask_audio due to above snippet
                set  validated_ctmkh=1
        endiff

rem Filename for our script to create the missing karaokes (if we decide to do that):
        set generated_script=%_CWD\create-the-missing-karaokes-here-temp.bat %+ rem these leftover files are eventually found and erased by free-up-harddrive-space which is called by maintenance which is called on reboot
        

       
rem Make sure we have the files we need:

        iff "%1" == "/s" .or. "%2" == "/s" then
                if not %@FILES[/h/s,%filemask_audio%] gt 0 (echos %ansi_color_warning_soft%%star% No files in %_CWP or its subfolders %conceal_on%121249212993%conceal_off%%+ goto :end)
        else
                if not   exist      %filemask_audio%       (echos %ansi_color_warning_soft%%star% No files in %_CWP %conceal_on%241224669420%conceal_off%%+ goto :end)
        endiff


rem Clean up any trash so we don’t try to make karaokes for the trash files:
        call clean-up-AI-transcription-trash-files-here.bat
        if exist   all.m3u (*del /q   all.m3u >nul >&>nul)
        if exist these.m3u (*del /q these.m3u >nul >&>nul)


rem Generate the script, but check if it’s here already first:
        rem set retry=0
        :Again
        iff exist "%generated_script%" then
                rem call less_important "Looks like a script has already been generated here, so we will run it..."
                rem call "%generated_script%"

                call removal "Looks like a script has already been generated here, so we will delete it first..."
                echo yra|*del /q "%generated_script%">&>nul      
        endiff



rem Call our audit script, which creates %generated_script%:
        call check-for-missing-karaoke %*
        rem if 1 eq %retry (goto :end)
        rem set retry=1
        rem goto :Again


rem Run the generated script (if it exists):
        iff exist "%generated_script%" then
                call important_less "Running generated karaoke-creation script..."
                call "%generated_script%" 
        endiff        



rem Cleanup:
        :END
        unset /q retry




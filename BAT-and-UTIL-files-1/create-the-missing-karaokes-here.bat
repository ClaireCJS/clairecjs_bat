@Echo Off
 on break cancel

rem Redundant environment variable creation in case this is being run without its requirements (good luck with that):
        iff not defined filemask_audio then
                set FILEMASK_AUDIO=*.mp3;*.wav;*.rm;*.voc;*.au;*.mid;*.stm;*.mod;*.vqf;*.ogg;*.mpc;*.wma;*.mp4;*.flac;*.snd;*.aac;*.opus;*.ac3
        endiff

rem Validate environment (once):
        iff 1 ne %validated_ctmkh then
                call validate-in-path               less_important check-for-missing-karaoke
                call validate-environment-variables filemask_audio ansi_color_warning_soft star
                set  validated_ctmkh=1
        endiff

rem Filename for our script to create the missing karaokes (if we decide to do that):
        set generated_script=%_CWD\create-the-missing-karaokes-here-temp.bat %+ rem these leftover files are eventually found and erased by free-up-harddrive-space which is called by maintenance which is called on reboot
        

       
rem Make sure we have the files we need:
        if not exist %filemask_audio% (echos %ansi_color_warning_soft%%star% No files in %_CWP %+ goto :end)


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



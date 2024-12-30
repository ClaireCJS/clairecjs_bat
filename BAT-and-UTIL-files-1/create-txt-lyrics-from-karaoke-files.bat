@Echo Off

:DESCRIPTION: In the current folder, convert all karaoke sidecar files into text sidecar files (unless they already exist).
:DESCRIPTION: That is: If an MP3/FLAC has a corresponding LRC/SRT but not TXT version, convert the LRC/SRT to TXT.

rem Configuration:
        set Approve_Generated_Lyrics_CTLFKF=False         %+ rem Whether to run “approve-lyrics.bat” on the output file or not. Set to “False” to prevent auto-approval

rem Environment preparation:
        if not defined FILEMASK_AUDIO set FILEMASK_AUDIO=*.mp3;*.wav;*.rm;*.voc;*.au;*.mid;*.stm;*.mod;*.vqf;*.ogg;*.mpc;*.wma;*.mp4;*.flac;*.snd;*.aac;*.opus;*.ac3

rem Validate environment (once):
        iff 1 ne %validated_CrTxtFrKarFile% then
                call validate-in-path important_less lrc2txt.bat lrc2txt.py srt2txt.bat srt2txt.py python
                set  validated_CrTxtFrKarFile=1
        endiff

rem Check if there are any audio files:
        if not exist %FILEMASK_AUDIO% (call important_less "No audio files in %_CWP" %+ goto :END)

rem For each audio file, processi t:
        for %%tmpAudioFile in (%FILEMASK_AUDIO%) gosub process_file "%tmpAudioFile%"

rem End:
        goto :END

rem ━━━━ SUBROUTINES: BEGIN: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

        :process_file [infile]
                set                                        file=%@UNQUOTE["%infile%"]         %+ rem filename without quotes
                set                base=%@unquote[%@name["%file%"]]                           %+ rem filename without extension
                set           lrc=%base%.lrc                                                  %+ rem filename of sidecar lrc file
                set           srt=%base%.srt                                                  %+ rem filename of sidecar srt file                                                                  
                set           txt=%base%.txt                                                  %+ rem filename of sidecar txt file
                if     exist %txt%                        return                              %+ rem Nothing to do if the TXT exists already
                if not exist %lrc% .and. not exist %srt%  return                              %+ rem Nothing to do if no LRC/SRT file to convert
                iff    exist %lrc% (set to_convert=%lrc% %+ set converter=lrc2txt)            %+ rem \_____At least one of SRT/LRC exists now, 
                iff    exist %srt% (set to_convert=%srt% %+ set converter=srt2txt)            %+ rem /     ...but we will prefer SRT over LRC. (Although it should be worth mentioning that for organic reasons, srt2txt actually does all the srt in the whole folder and will preclude any other srt conversion from happening within the framework of *this* script, because srt2txt.py itself traverses all files in a folder, quite different from lrc2txt which only works for a single file)
                call %converter% "%to_convert%"                                               %+ rem Perform our conversion
rem             if not exist "%txt%" (call fatal_error "Output file does not exist after trying to convert “%italics_on%%to_convert%%italics_off%” to “%italics_on%%txt%%italics_off%” with “%italics_on%%converter%%italics_off%”")
                rem echo file is %file% %@ansi_move_to_col[40] base=%base% %@ansi_move_to_col[70] srt=%srt%%@ansi_move_to_col[100] cvt=%convert%
        return

rem ━━━━ SUBROUTINES: END ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

:END

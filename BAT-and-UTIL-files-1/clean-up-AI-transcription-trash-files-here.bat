@loadbtm on
@Echo OFF
@on break resume

set  ONLY_CLEAN_UP_LOCALLY=1
call clean-up-AI-transcription-trash-files-everywhere.bat
set  ONLY_CLEAN_UP_LOCALLY=0


                rem OLD:           rem If any are added here, also add them to clean-up-AI-transcription-trash-files-everywhere!
                rem OLD:                   gosub DeleteHere               *._vad_collected_chunks*.*
                rem OLD:                   gosub DeleteHere               *._vad_original*.*
                rem OLD:                   gosub DeleteHere               *._vad_pyannote_*chunks*.wav
                rem OLD:                   gosub DeleteHere               *._vad_pyannote_v*.txt
                rem OLD:                   gosub DeleteHere               *._vad_ten.srt
                rem OLD:                   gosub DeleteHere               *._vad_silero*.srt
                rem OLD:           
                rem OLD:                   iff "%1" == "do_not_delete_BATs" goto :do_not_delete_BATs
                rem OLD:                           gosub DeleteHere  create-the-missing-karaokes-here-temp*.bat
                rem OLD:                           gosub DeleteHere       get-the-missing-lyrics-here-temp*.bat
                rem OLD:                           gosub DeleteHere      get-the-missing-karaoke-here-temp*.bat
                rem OLD:                           rem   DeleteHere      __ %+ rem this didn’t work and tried to “get __*.*”
                rem OLD:                   :do_not_delete_BATs
                rem OLD:           
                rem OLD:           
                rem OLD:           goto :END
                rem OLD:           
                rem OLD:                   :DeleteHere [file]
                rem OLD:                           if exist  %file% (*del /q %file%)
                rem OLD:                   return
                        

:END


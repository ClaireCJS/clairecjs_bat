@loadbtm on
@Echo OFF


rem OLD: if exist              "*._vad_collected_chunks*.wav" (*del /q              "*._vad_collected_chunks*.w*" )
rem OLD: if exist                      "*._vad_original*.srt" (*del /q                      "*._vad_original*.*"  )
rem OLD: if exist "create-the-missing-karaokes-here-temp.bat" (*del /q "create-the-missing-karaokes-here-temp.bat")
rem OLD: if exist      "get-the-missing-lyrics-here-temp.bat" (*del /q      "get-the-missing-lyrics-here-temp.bat")


        rem If any are added here, also add them to clean-up-AI-transcription-trash-files-everywhere!
        gosub DeleteHere               *._vad_collected_chunks*.wav
        gosub DeleteHere               *._vad_collected_chunks*.srt
        gosub DeleteHere               *._vad_original*.*
        gosub DeleteHere               *._vad_pyannote_*chunks*.wav
        gosub DeleteHere               *._vad_pyannote_v3.txt

        iff "%1" == "do_not_delete_BATs" goto :do_not_delete_BATs
                gosub DeleteHere  create-the-missing-karaokes-here-temp*.bat
                gosub DeleteHere       get-the-missing-lyrics-here-temp*.bat
                gosub DeleteHere      get-the-missing-karaoke-here-temp*.bat
                rem   DeleteHere      __ %+ rem this didn’t work and tried to “get __*.*”
        :do_not_delete_BATs


goto :END

        :DeleteHere [file]
                if exist  %file% (*del /q %file%)
        return

        

:END
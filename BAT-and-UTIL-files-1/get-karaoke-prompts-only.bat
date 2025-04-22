@loadbtm on
@Echo OFF



set OLD_DBATF_VALUE=%DELETE_BAD_AI_TRANSCRIPTIONS_FIRST%


        set DELETE_BAD_AI_TRANSCRIPTIONS_FIRST=0

                                                      rem echo %star2% call get-karaoke %1$ PromptAnalysis %+ pause
                                                                       call get-karaoke %1$ PromptAnalysis 
        set DELETE_BAD_AI_TRANSCRIPTIONS_FIRST=1


set DELETE_BAD_AI_TRANSCRIPTIONS_FIRST=%OLD_DBATF_VALUE%



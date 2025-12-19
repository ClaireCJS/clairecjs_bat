@Echo OFF
@on break cancel

REM validate environment once per sessoin:
        iff "1" != "%validated_splitmp3bychapter%" then
                call validate-in-path set-largest-filename less_important  split-mp3-by-inputted-chapter-info-helper.py  askyn add-ReplayGain-tags randcolor metaflac.exe errorlevel metamp3 add-art-to-song randfg add-art-to-all-songs
                call validate-environment-variable ansi_has_been_set 
                if not defined filemask_audio call validate-environment-variable filemask_audio 
                set validated_splitmp3bychapter=1
        endiff


REM If any pre-existing generated splitter .bat exists, get rid of it:
        set       SPLITTING_SCRIPT=generated-splitter.bat
        if exist %SPLITTING_SCRIPT%   (%COLOR_REMOVAL% %+ *del %SPLITTING_SCRIPT%)



REM Actually generate a new splitter .bat and run it on the largest file, which sould be the unsplit album:
        call set-largest-filename

        call less_important "Splitting largest file: “%largest_file%”"
        split-mp3-by-inputted-chapter-info-helper.py 




REM Ensure new splitter .bat exists:
        if not exist %SPLITTING_SCRIPT% call validate-environment-variable SPLITTING_SCRIPT


REM Now that we have our splitter.bat, run it:
    echo. 
    echo. 
    :Redo
    %COLOR_WARNING% %+ echo * About to run %SPLITTING_SCRIPT%... %+ pause
    %COLOR_RUN%     %+                call %SPLITTING_SCRIPT% "%largest_file%"


REM Check if we’ve run it successfully or not:
    REM this thing returns 2 which kinda makes our errorlevelcatcher not so great: call errorlevel "but sometimes we see an errorlevel of 2 which seems to be not so bad in this situation?" 
    if %REDO% eq 1 goto :Redo
    %COLOR_REMOVAL% 
    del %SPLITTING_SCRIPT% "%largest_file%"


REM Hopefully there is just 1 of each of these files, but that’s what should be the case if we’re here!
    ren *.json   info.json
    ren *.txt   README.txt
    ren *.webp  cover.webp



REM Volume issues:
        call AskYN "Add ReplayGain tags to newly-split files" yes 15
        iff "N" != "%ANSWER%" then
                call normalize-all-wavs %+ rem Deprecated so not validating that this is in path
                call add-ReplayGain-tags  
        endiff

REM Cover art:
        call add-art-to-all-songs


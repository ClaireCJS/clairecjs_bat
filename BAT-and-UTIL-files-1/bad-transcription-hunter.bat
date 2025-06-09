@loadBTM ON
@Echo OFF
@on break cancel



rem Validate environment:
        call validate-in-path advice sweep-random delete-bad-ai-transcriptions askyn less_important print-message



rem Sanity check:
        repeat 8 echo.
        call less_important "This Bad-Transcription-Hunter will recurse through all subfolders, randomly, looking for bad AI transcriptoins"
        call advice "Current folder is: %italics_on%%[_CWP]%italics_off%"
        pause "Make sure you are in the root folder of where you want to search for bad AI transcriptions"

rem Ask if we should proceed, and do so if we say “yes”:
        unset /q answer
        call askyn "Proceed with hunting of bad AI transcriptions" no 0
        if "Y" == "%ANSWER%" call sweep-random "call delete-bad-ai-transcriptions 3" force
        unset /q answer


@Echo Off
 on break cancel


rem Usage:
        iff "%1" eq "" then
                %color_advice%
                text
                :USAGE: get-lyriclessness-status {songfile}        —— sets LYRICLESSNESS_STATUS to our return value
                :USAGE: get-lyriclessness-status {songfile} silent —— silent mode: no error output
                endtext
                %color_normal%
                goto :END
        endiff
 

rem Get parameters:
        set SONG_TO_GET_STATUS_OF=%@UNQUOTE[%1]
        iff "%2" eq "silent" then
                set SILENT_GETLYRICLESSNESSSTATUS=1
        else                
                set SILENT_GETLYRICLESSNESSSTATUS=0
        endiff                

rem Validate environment once per session:
        iff 1 ne %validated_getlyriclessnessstatus% then
                call validate-in-path               warning_soft.bat read-ADS-tag-from-file.bat print-message.bat
                call validate-environment-variables emphasis deemphasis color_normal color_advice filemask_audio
                set  validated_getlyriclessnessstatus=1
        endiff
        
rem Validate parameters:
        call validate-environment-variable Song_To_Get_Status_Of "1ˢᵗ argument to “%0” must be the songfile that you want to get the lyric%italics_on%lessness%italics_off% status for"
        call validate-extension            Song_To_Get_Status_Of %FILEMASK_AUDIO%

rem Clear recepticle variables:
        unset /q LYRICLESSNESS_STATUS
        unset /q LYRICSLESSNESS_STATUS

rem Read the lyriclessness status:
        iff exist "%SONG_TO_GET_STATUS_OF%" then
                call read-ADS-tag-from-file "%SONG_TO_GET_STATUS_OF%" lyriclessness
        else
                if 1 ne %SILENT_GETLYRICLESSNESSSTATUS% call warning_soft "File “%italics_on%%emphasis%%SONG_TO_GET_STATUS_OF%%deemphasis%%italics_off%” does not exist"
        endiff
        
rem Set it to a return value environment variable:   
        set LYRICSLESSNESS_STATUS=%RECEIVED_VALUE%
        
rem (Learned very fast that when calling this, a common invocation 
rem  error was to not remember if it was 'lyric' or 'lyrics'):
        set LYRICLESSNESS_STATUS=%RECEIVED_VALUE%


:END

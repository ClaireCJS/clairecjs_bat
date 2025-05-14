@Echo On


rem Install WhisperTimeSync with:      git clone https://github.com/EtienneAb3d/WhisperTimeSync.git
rem Set JAVA_WHISPERTIMESYNC=      to the path of the java.exe you wish to use. Or just set it to "java"

rem Synchonize example from that github:

rem     java -Xmx2G -jar distrib/WhisperTimeSync.jar song.srt lyrics.txt en
                               

rem CONFIG:
        set WhisperTimeSync=%UTIL2%\WhisperTimeSync\distrib\WhisperTimeSync.jar
        set our_language=en

rem VALIDATE ENVIRONMENT:
        iff 1 ne %VALIDATED_WHISPERTIMESYNCHELPER% then
                call validate-in-path               errorlevel
                call validate-environment-variables JAVA_WHISPERTIMESYNC WhisperTimeSync our_language color_advice ansi_color_advice lq rq 
                call validate-is-function           cool_text
                set  VALIDATED_WHISPERTIMESYNCHELPER=1
        endiff



rem USAGE:
        iff "%1" eq "" .or. "%2" eq "" then
                echo.
                call divider
                %color_advice%
                        echo.
                        echo USAGE: %0 [subtitle file with bad words and good timing] [lyric file with good words and no/bad timing]
                        echo USAGE: %0 [subtitles] [lyrics]
                        echo    EX: %0  %@cool_text[subtitl.srt lyrics.txt]%ansi_color_advice%
                        echo    EX: %0  %@cool_text[subtitl.srt crappy.srt]
                call divider
                echo.
                goto :END
        endiff

rem VALIDATE PARAMETERS:
        set SRT=%@UNQUOTE[%1]
        set LYR=%@UNQUOTE[%2]
        iff "1" != "%validated_srt_and_txt_for_whispertimesync_already%" then
                call validate-environment-variables SRT     LYR
                call validate-is-extension        "%SRT%" *.srt
                call validate-is-extension        "%LYR%" *.txt
        endiff

rem Run WhisperTimeSync:
        "%JAVA_WHISPERTIMESYNC%" -Xmx2G -jar %WhisperTimeSync% "%srt%" "%lyr%" %our_language%
        call errorlevel

rem Did it work?
        set BASE=%@NAME[%SRT%]
        set SRT_NEW=%BASE%.txt.srt
        set SRT_NEW=%@NAME["%LYR%"].txt.srt
eset SRT_NEW
        iff exist "%SRT_NEW%" then
                call success "%italics_on%WhisperTimeSync%italics_off% successful"
        else
                call validate-environment-variable SRT_NEW "WhisperTimeSync did not produce expected output file of %lq%%SRT_NEW%%rq%"
        endiff

rem TODO: Possble idea: Preview it if 3ʳᵈ “preview” option (TODO) is passed?



:END

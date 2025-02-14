@Echo Off

rem Install WhisperTimeSync with:  git clone https://github.com/EtienneAb3d/WhisperTimeSync.git
rem Set JAVA_WHISPERTIMESYNC=      to the path of the java.exe you wish to use. Or just set it to "java"

rem Synchonize example from that github: java -Xmx2G -jar distrib/WhisperTimeSync.jar song.srt lyrics.txt en
                               

rem CONFIG:
        set WhisperTimeSync=%UTIL2%\WhisperTimeSync\distrib\WhisperTimeSync.jar
        set our_language=en

rem VALIDATE ENVIRONMENT:
        set  validated_srt_and_txt_for_whispertimesync_already=0
        iff 1 ne %VALIDATED_WHISPERTIMESYNC2% then
                call validate-in-path errorlevel success WhisperTimeSync-helper divider print-with-columms.bat print_with_columns.py review-file review-files AskYN
                call validate-environment-variables JAVA_WHISPERTIMESYNC our_language color_advice ansi_color_advice
                call validate-is-function cool_text
                set  VALIDATED_WHISPERTIMESYNC2=1
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
        set   SRT=%@UNQUOTE[%1]
        set   LYR=%@UNQUOTE[%2]
        set   MP3=%NAME[%LYR%].mp3
        set   WAV=%NAME[%LYR%].wav
        set  FLAC=%NAME[%LYR%].flac
        call validate-environment-variables SRT     LYR
        call validate-is-extension        "%SRT%" *.srt
        call validate-is-extension        "%LYR%" *.txt
        set  validated_srt_and_txt_for_whispertimesync_already=1

rem Run WhisperTimeSync:
        call WhisperTimeSync-helper "%srt%" "%lyr%"                 %+ rem “Did it work?”-style validation is in WhisperTimeSync-helper.bat
        set  validated_srt_and_txt_for_whispertimesync_already=0    %+ rem This flag has now been used and can be disposedo f


rem Preview the lyrics vs OLD srt with stripes next to each other:
        call review-file       -wh -st  "%lyr%"
        call review-file       -wh -stU "%srt%"
        call print-with-columns    -st  "%srt%"

rem Preview the lyrics vs NEW srt with stripes next to each other:
        call divider
        call print-with-columns    -st  "%lyr%"
        call review-file       -wh -stU "%srt_new%"
        call print-with-columns     -st "%srt_new%"

rem Compare stripes of old srt and new srt:
        call print-with-columns    -st  "%lyr%"
        call print-with-columns    -st  "%srt_new%"
        call divider

rem Ask if it’s better or not...
        :AskYnIfBetter
        call AskYN "Is this better than the old" no 666 P P:play_it
        iff "%ANSWER%" == "P" then
                echo 🐐 %0: call vlc %@if[exist "%mp3%","%mp3%",] %@if[exist "%flac%","%flac%",]
                call vlc %@if[exist "%mp3%","%mp3%",] %@if[exist "%flac%","%flac%",]
                goto :AskYnIfBetter
        endiff

rem If it is better, back up the old version and replace it with this one:
        iff "Y" == "%ANSWER%" then
                rem back up the old/existing karaoke:
                        echo     *copy /Nst "%srt%"      "%srt%.pre-wts.%_DATETIME.bak" 
                        echo ray|*copy /Nst "%srt%"      "%srt%.pre-wts.%_DATETIME.bak" 
                rem move the new karaoke to overwrite the now-backed-up old karaoke:
                        echo     *copy /Nst "%SRT_NEW%"  "%srt%" 
                        echo ray|*copy /Nst "%SRT_NEW%"  "%srt%" %+ pause
        else
                        echo ray|*del  /q   "%SRT_NEW%" 
        endiff


:END


:Cleanup
        set validated_srt_and_txt_for_whispertimesync_already=0



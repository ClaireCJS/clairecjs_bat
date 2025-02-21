@Echo Off
@loadbtm on

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
                        echo    EX: %0  %@cool_text[bad.srt good.txt]%ansi_color_advice%
                        rem     EX: %0  %@cool_text[subtitles.srt lyrics.txt]%ansi_color_advice%
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
        if not exist "%SRT%" .or. not exist "%LRC%" call validate-environment-variables SRT     LYR
        call validate-is-extension        "%SRT%" *.srt
        call validate-is-extension        "%LYR%" *.txt
        set  validated_srt_and_txt_for_whispertimesync_already=1

rem Run WhisperTimeSync:
        call WhisperTimeSync-helper "%srt%" "%lyr%"                 %+ rem “Did it work?”-style validation is in WhisperTimeSync-helper.bat
        set  validated_srt_and_txt_for_whispertimesync_already=0    %+ rem This flag has now been used and can be disposedo f


rem Preview changes:
rem            1 lyrics                   \__ review lyrics with stripe
rem            2     lyrics stripe        /  
rem            3     Old Subtitles stripe \__ review subtitles with upper stripe  
rem            4 Old Subtitles            /
rem            5     Old Subtitles stripe
rem            6     New Subtitles stripe\___ review new subtitles with upper stripe
rem            7 New Subtitles           /
rem            8     Old Subtitles stripe
rem            9     lyrics stripe
rem            10    New Subtitles stripe


rem Preview the lyrics vs OLD srt with stripes next to each other:
        call review-file       -wh -st  "%lyr%"                       %+ rem 1 & 2
        call review-file       -wh -stU "%srt%"                       %+ rem 3 & 4
        call divider
        call print-with-columns    -st  "%srt%"                       %+ rem 5

rem Preview the NEW srt with stripes next to each other:
        call review-file       -wh -stU "%srt_new%"                   %+ rem 6 & 7

rem Compare stripes of old srt and new srt:
        call divider
        call print-with-columns    -st  "%lyr%"                       %+ rem 9
        call print-with-columns    -st  "%srt%"                       %+ rem 8
        call print-with-columns    -st  "%srt_new%"                   %+ rem 10
        call print-with-columns    -st  "%lyr%"                       %+ rem 9
        echo %faint_on%(lyrics, original subtitle, new subtitle, lyrics again)%faint_off%
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



@Echo Off
@loadBTM ON
@on break cancel



rem SETUP: 
rem
rem 1) Install WhisperTimeSync with:      git clone https://github.com/EtienneAb3d/WhisperTimeSync.git
rem 2) Set JAVA_WHISPERTIMESYNC=          to the path of the java.exe you wish to use. Or just set it to "java"
rem
rem Synchonize example from that github: java -Xmx2G -jar distrib/WhisperTimeSync.jar song.srt lyrics.txt en



rem TODO: Possble idea: Preview it if 3ʳᵈ “preview” option (TODO) is passed?


                               

rem CONFIG:
        set WhisperTimeSync=%UTIL2%\WhisperTimeSync\distrib\WhisperTimeSync.jar
        set our_language=en

rem VALIDATE ENVIRONMENT:
        iff "1" != "%validated_whispertimesynchelper%" then
                call validate-in-path               errorlevel askyn enqueue.bat warning.bat advice.bat print-message.bat winamp-next subtitle-postprocessor.pl perl
                rem  validate-environment-variables JAVA_WHISPERTIMESYNC WhisperTimeSync our_language color_advice ansi_color_advice lq rq underline_on underline_off italics_on italics_off
                call validate-environment-variables ANSI_COLORS_HAVE_BEEN_SET EMOJIS_HAVE_BEEN_SET JAVA_WHISPERTIMESYNC our_language WhisperTimeSync 
                call validate-is-function           cool_text
                call checkeditor
                set  validated_whispertimesynchelper=1
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
                call validate-environment-variables   SRT     LYR
                call validate-is-extension          "%SRT%" *.srt
                call validate-is-extension          "%LYR%" *.txt
        endiff

rem Extra prep of lyrics:
        call warning "Get the lyrics %italics_on%perfect%italics_off%" big
        %EDITOR% "%LYR%"
        pause "Press any key after fixing up the lyrics"

rem Run WhisperTimeSync:
        %color_run%
        "%JAVA_WHISPERTIMESYNC%" -Xmx2G -jar %WhisperTimeSync% "%srt%" "%lyr%" %our_language%
        call errorlevel

rem Determine output filenames:
        set BASE=%@NAME[%SRT%]
        rem SRT_NEW=%BASE%.txt.srt
        rem SRT_NEW=%@NAME["%LYR%"].txt.srt
        set SRT_NEW=%@PATH[%@UNQUOTE["%LYR%"]]%@NAME[%@UNQUOTE["%LYR%"]].txt.srt                                          %+ rem Never as simple as you think....
        rem eset SRT_NEW

rem Did it work?
        iff exist "%SRT_NEW%" then
                call success "%italics_on%WhisperTimeSync%italics_off% successful"
        else
                call validate-environment-variable SRT_NEW "WhisperTimeSync did not produce expected output file of %lq%%SRT_NEW%%rq%"
        endiff


rem WhisperTimeSync is horribly buggy so we fix some of that——particularly the blocks that are completely missing lyrics——with our subtitle postprocessor:
        subtitle-postprocessor.pl "%SRT_NEW%"

rem WhisperTimeSync is horribly buggy so manual review/fix is needed:
        call warning "%underline_on%WhisperTimeSync%underline_off% is buggy af%italics_off%" big
        call warning "So manually review/fix the subtitles"                                  big
        %EDITOR% "%SRT_NEW%"
        pause "Press any key after fixing up the subtitles"



:END

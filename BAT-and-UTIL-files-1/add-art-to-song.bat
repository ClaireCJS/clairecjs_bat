@LoadBTM ON
@Echo off
@on break cancel


rem Capture parameters:
        SET  ART=%1
        SET SONG=%2

rem Validate parameters:
        if not exist %ART%  call validate-environment-variable ART 
        if not exist %SONG% call validate-environment-variable SONG

rem Validate environment (once):
        iff "1" != "%validated_addarttosong%" then
                call validate-in-path add-art-to-mp3.bat add-art-to-flac.bat success.bat print-message.bat
                set  validated_addarttosong=1
        endiff


rem Call appropriate script depending on extension of parameter:
        iff     "%@ext[%SONG%]" == "mp3" then
                call add-art-to-mp3.bat  %ART% %SONG% %3 %4 %5 %6 %7 %8 %9
        elseiff "%@ext[%SONG%]" == "flac" then
                call add-art-to-flac.bat %ART% %SONG% %3 %4 %5 %6 %7 %8 %9
        else
                %COLOR_ERROR% 
                echo WTF EXTENSION IS %@EXT[%SONG%]!?!?!?!
                pause
                pause
                pause
                pause
                pause
                goto :goto_here_if_not_successful
        endiff


rem Inform success:
        call success "Done!"
        :goto_here_if_not_successful



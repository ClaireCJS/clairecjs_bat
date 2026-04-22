@on break cancel
@Echo off

rem Validate environment (once):
        iff "1" != "%validated_displaymp3length%" then
                call validate-in-path validate-file-extension display-mp3-tags grep sed set-tmp-file
                call validate-function strip_ansi %+ rem we must use stripansi, strip_ansi is just a placeholder/semaphore
                call validate-environment-variables emoji_have_been_set ansi_colors_have_been_set
                set  validated_displaymp3length=1
        endiff


rem Validate parameters
        set OUR_MP3=%@UNQUOTE[%1]
        if not exist %OUR_MP3%  call validate-environment-variable  OUR_MP3
        if "%@EXT["%OUR_MP3%"]" != "mp3" call validate-file-extension  %OUR_MP3% *.mp3
        set PRETTY_OUR_MP3=%@UNQUOTE[%OUR_MP3%] 

rem Cosmetics:
        echos %@CURSOR_COLOR[indigo]%ANSI_COLOR_RUN%%EMOJI_GEAR% Reading length of: %faint_on%%italics_on%%@NAME["%OUR_MP3%"]%italics_off%...%faint_off%%@ANSI_MOVE_TO_COL[0]


rem History:
        rem set DISPLAYMP3LENGTH_OUTPUT=%@EXECSTR[call display-mp3-tags %OUR_MP3% |:u8 grep -i length |:u8 sed -e "s/ 00:/ /" -e "s/ 0/  /" -e "s/ *:/:/" -e "s/^ *//ig" -e "s/:/:%ANSI_COLOR_IMPORTANT%%ITALICS_ON%/" ]
        rem set NEWPUT=%@EXECSTR[grep -i length %tmpfile1% |:u8 sed -e "s/ 00:/ /" -e "s/ 0/  /" -e "s/ *:/:/" -e "s/^ *//ig" -e "s/:/:%ANSI_COLOR_IMPORTANT%%ITALICS_ON%/" ]

rem Create tmp file:
        if not defined tmpfile1 call set-tmp-file "display-mp3-length"

rem Read the thing:
        set READER_OUTPUT=%@EXECSTR[call display-mp3-tags "%OUR_MP3%" |& grep -i Length |& sed -e "s/^ *Length *: [0:]*//i"]

rem Saving the results:
        set DISPLAY_MP3_LENGTH_OUTPUT=%READER_OUTPUT%

rem Aliases for the results:
        set                    OUTPUT=%DISPLAYMP3LENGTH_OUTPUT%
        set                MP3_LENGTH=%DISPLAYMP3LENGTH_OUTPUT%

rem Pretty output unless we give the silent option:
        echos %CURSOR_RESET%
        if "%2" == "silent" goto :silent_dmp3l

        echo %STAR% %ANSI_COLOR_BRIGHT_GREEN%Length of %OUTPUT% %ITALICS_OFF%%ANSI_COLOR_BRIGHT_YELLOW%%DASH% %ANSI_COLOR_YELLOW%for mp3: %ANSI_COLOR_BRIGHT_YELLOW%%@REPLACE[.mp3,%ANSI_COLOR_YELLOW%.mp3,%PRETTY_OUR_MP3%] %STAR%

        :silent_dmp3l
        echos %ANSI_ERASE_TO_EOL%



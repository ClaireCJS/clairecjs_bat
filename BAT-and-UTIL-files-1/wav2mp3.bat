@Echo OFF
 on break cancel

::::: PARAMETERS:
    set SOURCE_WAV=%1
    set TARGET_MP3=%2
    set    QUALITY=%3                        %+ if "%QUALITY%" eq ""   (set QUALITY=0)
    set        MIN=-b 96                     %+ if  %QUALITY%  gt 3    (unset /q MIN)
    set   CHANNELS=-m j                      %+ if "%QUALITY%" eq "-m" (set QUALITY=0 %+ set CHANNELS=%3 %4)  %+ REM This is admittedly ugly, but due to legacy interaction, this bat ends up being overloaded with parameters in a few different combinations. We just have to deal with it.
    set   CHANNELS=-m j                      %+ if "%4%"       eq "-m" (                 set CHANNELS=%4 %5)
    set OTHEROPTIONS=--add-id3v2 --tn 1/1 --replaygain-accurate  %+ REM  Best attempt to force id3v1/v2 stub tags so tagging process goes slightly faster later.
    :OLD: set START=start /low /wait /min    %+ REM stopped doing this with DEMONA in 2022. Things are fast enough to just let them run in the current window.
    unset /q START



::::: VALIDATE ENVIRONMENT, PARAMETERS:
    call validate-environment-variable UTIL
    if ""  eq   "%SOURCE_WAV%" (echo FATAL ERROR: 1st parameter of WAV source file must be given!! %+ beep %+ pause %+ goto :END)
    if ""  eq   "%TARGET_MP3%" (echo FATAL ERROR: 2nd parameter of MP3 target file must be given!! %+ beep %+ pause %+ goto :END)
    if not exist %SOURCE_WAV%  (call alarm-beep FATAL ERROR: parameter 1, source_wav, %SOURCE_WAV%, does not exist!! %+ pause %+ goto :END)

::::: BACKUP DESTINATION IF IT ALREADY EXISTS:
    set MP3_BAK_FILE="%@STRIP[%=",%TARGET_MP3%].bak"
    if exist %TARGET_MP3% .and. exist %MP3_BAK_FILE% (*del %MP3_BAK_FILE%)
    if exist %TARGET_MP3%                            (mv %TARGET_MP3% %MP3_BAK_FILE%)
    if exist %TARGET_MP3%                            (call alarm-beep FATAL ERROR: Check Code: 02934pa0w9jerlijsd!! %+ pause %+ goto :END)

::::: DEAL WITH ARTWORK EMBEDDING:
	unset /q ARTWORK 
	set NAME_TO_CHECK=cover.gif                             %+ if exist %NAME_TO_CHECK% set ARTWORK=%NAME_TO_CHECK%
	set NAME_TO_CHECK=folder.gif                            %+ if exist %NAME_TO_CHECK% set ARTWORK=%NAME_TO_CHECK%
	set NAME_TO_CHECK=cover.jpg                             %+ if exist %NAME_TO_CHECK% set ARTWORK=%NAME_TO_CHECK%
	set NAME_TO_CHECK=folder.jpg                            %+ if exist %NAME_TO_CHECK% set ARTWORK=%NAME_TO_CHECK%
	set NAME_TO_CHECK=cover.png                             %+ if exist %NAME_TO_CHECK% set ARTWORK=%NAME_TO_CHECK%
	set NAME_TO_CHECK=folder.png                            %+ if exist %NAME_TO_CHECK% set ARTWORK=%NAME_TO_CHECK%
    set NAME_TO_CHECK=%@NAME[%@STRIP[%=",%SOURCE_WAV%]].gif %+ if exist %NAME_TO_CHECK% set ARTWORK=%NAME_TO_CHECK%
    set NAME_TO_CHECK=%@NAME[%@STRIP[%=",%SOURCE_WAV%]].jpg %+ if exist %NAME_TO_CHECK% set ARTWORK=%NAME_TO_CHECK%
    set NAME_TO_CHECK=%@NAME[%@STRIP[%=",%SOURCE_WAV%]].png %+ if exist %NAME_TO_CHECK% set ARTWORK=%NAME_TO_CHECK%
	unset /q ARTWORKOPTIONS
	if "%ARTWORK%" ne "" set ARTWORKOPTIONS=--ti "%@UNQUOTE[%ARTWORK%]"

::::: LET USER KNOW:
	echo.
	echo.
	echo.
	echo.
	call randcolor             %+ echos *************************************************************************************************** %+ %COLOR_NORMAL% %+ echo.
    color bright cyan on black %+ echo *** Encoding: %SOURCE_WAV%
    color bright cyan on black %+ echo ***       To: %TARGET_MP3%
    color        cyan on black %+ echo ***   Folder: %_CWP
    color bright blue on black %+ echo ***  Artwork: %ARTWORK%
    color        blue on black %+ echo *** LAME Options:  Quality=%QUALITY% ... MIN=%MIN% ... CHANNELS=%CHANNELS%


::::: DO THE ACTUAL ENCODE:
    rem :20140623 - we dropped the -k option, for some reason
    rem :20150716 - we dropped the -m j (stereo) default option in favor of the perl generator (allfilew2m.pl) adding either "-m j" or "-m m", so that mono stuff is encoded in mono (once again, in a post-Xing environment)
    rem :20241125 - added "" to start command to update to current proper invocation and stop using our bat file that promoted incorrect invocation
    color   red on black %+ echo *** %START% "" %UTIL%\lame.exe -V %QUALITY% %CHANNELS% %ARTWORKOPTIONS% %OTHEROPTIONS% %MIN -h "%@UNQUOTE[%SOURCE_WAV%]" %TARGET_MP3% %5 %6 %7 %8 %9
    color white on black %+          %START% "" %UTIL%\lame.exe -V %QUALITY% %CHANNELS% %ARTWORKOPTIONS% %OTHEROPTIONS% %MIN -h "%@UNQUOTE[%SOURCE_WAV%]" %TARGET_MP3% %5 %6 %7 %8 %9

::::: SOME OLD NOTES:
        ::: quality 9   is about    32kbps        vbr [GUESSING]
        ::: quality 8   is about    56k           vbr [GUESSING]
        ::: quality 7   is about 32-48k (40k avg) vbr
        ::: quality 6   is about    80k           vbr [GUESSING]
        ::: quality 5   is about 48-80k (56k avg) vbr
        ::: quality 4   is about 56-96k (64k avg) vbr
        ::: quality 3   is about   128k           vbr ..
        ::: quality 1-2 is about   160k            vbr ..
        ::: quality 0   is about   192kbps 

        :-k disables all filtering
        :LAME brings us the first (and still only) optimally tweaked (unlike
        :Fraunhofer) VBR mp3 encoder that does not mess up (unlike Xing):
        :c:\util\lame.exe -V 1 -b 128 -h -m j infile.wav outfile.mp3
        :(LAME 3.80 or newer) Remarks:  Perfect sound quality at optimal bitrate.

        :Sounds perfect to me and many others with
        :-V2 -b32, but for the sake of people with very expensive audio equipment and
        :"golden ears" an extra few bytes (about 10% size increase) are allowed with
        :this setting.  Downside to Lame VBR is the slightly longer encoding time when
        :comparing to CBR.  The resulting average bitrate will be around 150 kbit/s to
        :180 kbit/s, depending on the music.  Some complex tracks might encode with an
        :average bitrate of around 200 kbit/s.

::::: UNSET TEMP VARS:
    :END
    unset /q QUALITY
    unset /q SOURCE_WAV
    unset /q TARGET_MP3
    unset /q QUALITY
    unset /q MIN


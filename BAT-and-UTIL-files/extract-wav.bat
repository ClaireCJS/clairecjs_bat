@Echo OFF


%color_advice%
	echo * NOTE: 2022: downsampling to 44kHz may not be what we want, and we may want to change those parameters
%color_normal%

::::: GET SOURCE FILE:
    set  SOURCE=%1



::::: GET TARGET FILENAME:
    SET  TARGET=%2
    if "%TARGET%" ne "" goto :Target_Given
        set TARGET=%@NAME[%SOURCE].wav
        :Edit_Target
            :2022/02/11 - DECIDED TO STOP THIS .... %COLOR_INPUT% %+ eset target
        if exist "%@UNQUOTE[%TARGET%]" goto :Edit_Target
    :Target_Given


::::: EXTRACT THE WAV:
    %COLOR_RUN% 
        :ffmpeg -i "%@UNQUOTE[%SOURCE%]" -vn -ar 44100 -ac 2 -ab 768000 -f wav "%@UNQUOTE[%TARGET%]"
         ffmpeg -i "%@UNQUOTE[%SOURCE%]" -vn           -ac 2            -f wav "%@UNQUOTE[%TARGET%]"
    %COLOR_NORMAL%



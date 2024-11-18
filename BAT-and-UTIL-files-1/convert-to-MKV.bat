@Echo OFF

set OUTPUT_VIDEO_FILENAME="%@UNQUOTE[%@NAME[%1].mkv]"

rem old: ffmpeg -i %1 -acodec copy -vcodec copy %OUTPUT_VIDEO_FILENAME% 
rem      mencoder  %1 -o %OUTPUT_VIDEO_FILENAME% -oac pcm -ovc x264
echo     mencoder  %1 -o %OUTPUT_VIDEO_FILENAME% -oac pcm -ovc x264 -x264encopts crf=18
rem pause
         mencoder  %1 -o %OUTPUT_VIDEO_FILENAME% -oac pcm -ovc x264 -x264encopts crf=5

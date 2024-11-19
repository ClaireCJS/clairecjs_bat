@on break cancel
ffmpeg -i %1 -acodec copy -vcodec copy %@UNQUOTE[%@NAME[%1].avi]
@Echo OFF

if not isdir ".history" md /s ".history"

call sizes.bat            >size-report.txt %+  cp   size-report.txt ".history\sizes-%_DATETIME.txt"
call counts.bat         >counts-report.txt %+  cp counts-report.txt ".history\counts-%_DATETIME.txt"
dir /s %FILEMASK_IMAGE%    >dir-images.txt %+  cp    dir-images.txt ".history\dir-images-%_DATETIME.txt"
dir /s %FILEMASK_VIDEO%    >dir-videos.txt %+  cp    dir-videos.txt ".history\dir-videos-%_DATETIME.txt"


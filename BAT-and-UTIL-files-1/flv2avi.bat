@on break cancel
set BASE=%@NAME[%1]
ffmpeg -i "%BASE.flv" "%BASE.avi"

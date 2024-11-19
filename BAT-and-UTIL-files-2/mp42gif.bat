@echo off
@on break cancel
set  INPUT=%@UNQUOTE[%1]
call important "%emoji_hammer% Converting %1 to GIF..."
ffmpeg -i "%INPUT%" -vf "fps=10" "%@NAME[%INPUT].gif"
call success "Conversion complete!"


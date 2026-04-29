@echo off

call segregate *.mkv;*.avi;*.mp4;*.m4a;*.flv;*.mov;*.wmv;*.mpg;*.mpeg;*.vob;*.bdmv;*.ts;*.m2ts;*.rm;*.qt;*.asf;*.asx;*.fli;*.swf;*.m4v;*.webm;*.f4v;*.rm;*.ram;*.3gp
call dzbf
cd ..
if     isdir video mv/ds hold video
if not isdir video ren   hold video



@echo off

call segregate *.mkv;*.avi;*.mp4;*.m4a;*.flv;*.mov;*.wmv;*.mpg;*.mpeg;*.vob;*.bdmv;*.ts;*.m2ts;*.rm;*.qt;*.asf;*.asx;*.fli;*.swf;*.m4v;*.webm;*.f4v;*.rm;*.ram;*.3gp

cd ..

iff isdir video then
        echo yra|mv/ds HOLD VIDEO
else
        ren HOLD VIDEO
endiff


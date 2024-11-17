for %%f in (*.ts) do call ffmpeg -i "%%~f" -vcodec copy -acodec copy "mp4_%%~nf.mp4"

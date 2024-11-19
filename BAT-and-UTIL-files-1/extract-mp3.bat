@on break cancel
ffmpeg -i %1 -vn -ar 44100 -ac 2 -ab 192000 -f mp3 %2

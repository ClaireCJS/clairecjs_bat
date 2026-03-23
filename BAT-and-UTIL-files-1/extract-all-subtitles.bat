@loadbtm on
@Echo OFF
@on break cancel



do f in *.mkv
    set "MKV=%@UNQUOTE[%f]"
    set "IDX=%@EXECSTR[powershell -NoProfile -Command "$idx = & ffprobe -v error -select_streams s -show_entries stream=index:stream_tags=language -of csv=p=0 -- $env:MKV | Where-Object { $_ -match '^\d+,(eng|en(?:-|$))$' } | Select-Object -First 1 | ForEach-Object { (($_ -split ',')[0]).Trim() }; $idx" ]"

    if not "%IDX" == "" (
        echo Extracting English subs from: %f  [stream %IDX]
        ffmpeg -v error -nostdin -i "%f" -map 0:%IDX% -c:s srt "%@PATH[%f]%@NAME[%f].srt"
    ) else (
        echo No English subtitle track found in: %f
    )
enddo

@Echo OFF
@on break cancel


rem Validate the environment once per session:
        if "%VALIDATED_SIZES_BAT%" ne "1"  (
            call validate-in-path      du  tr  column  sort-by-human-readable-size
            set  VALIDATED_SIZES_BAT=1
        )


rem Display the file sizes, but sort them by human-readable size, and align the columns:
        rem ((du -ha --max-depth=1)|sort-by-human-readable-size) :2020 had to mysteriously drop the -a from -ha for some reason
        rem ((du -h  --max-depth=1)|sort-by-human-readable-size) :2024 re-did with column alignment:
            ((du -h  --max-depth=1)|:u8sort-by-human-readable-size)|:u8tr '\t' '*'|:u8column -t -s '*'



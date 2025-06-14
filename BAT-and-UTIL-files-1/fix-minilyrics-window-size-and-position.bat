@Echo OFF
@on break cancel

goto :20250614

rem activate "minilyrics" pos=-1059,-1085,700,670 %+ rem this works but if it results in a not-high-enough, halfway-off-the-screen-to-the-left, maybe do this one instead:

:20241217
        rem 20241217: before getting new tv: 1080p+1080p main+4K upper-right+1080p monitor
        activate "minilyrics"      pos=-0708,-1085,800,800
        activate "Floating Lyrics" pos=1208,-2157,1275,200
        goto :END

:20250612
        rem 20250612: Same setup, but something has changed....
        activate "minilyrics"      pos=-0820,-1080,1050,1050
        activate "Floating Lyrics" pos=1208,-2157,1275,200
        goto :END

:20250614
        rem 20250614: hate how stupid this is
        activate "minilyrics"      pos=-1280,-1080,820,800
        activate "Floating Lyrics" pos=650,-2200,1500,200
        goto :END



:END



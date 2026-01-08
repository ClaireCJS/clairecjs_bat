@Echo OFF
@on break cancel
@title TCC


if "%1" != "" goto :%1

goto :1


rem post-85", two 4K screens and two 1080 screens
        :1
        :20260103
                activate "minilyrics"      pos=-4250,-1100,1150,1075
                activate "Floating Lyrics" pos=-2325,-2125,1275,190
                activate "Album Art"       pos=-2325,-1850,350,345 
                goto :END


rem 20250614: hate how stupid this is
        :2
        :20250614
                activate "minilyrics"      pos=-1280,-1080,820,800
                activate "Floating Lyrics" pos=650,-2200,1500,200
                goto :END


rem 20250612: Same setup, but something has changed....
        :3
        :20250612
                activate "minilyrics"      pos=-0820,-1080,1050,1050
                activate "Floating Lyrics" pos=1208,-2157,1275,200
                goto :END


rem 20241217: before getting new tv: 1080p+1080p main+4K upper-right+1080p monitor
        :4
        :20241217
                activate "minilyrics"      pos=-0708,-1085,800,800
                activate "Floating Lyrics" pos=1208,-2157,1275,200
                goto :END




:END
rem Try to focus us back to the command-line we were just using:
        activate TCC*



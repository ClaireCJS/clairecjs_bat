@Echo Off

rem Also used to look up images for album art —— part of an integrated "tool" in mp3-tag, which is used as a step in part of our music intake workflow


:DEBUG: echo * image-search-medium %* called (1=%1,2=%2,3=%3,4=%4,5=%5,6=%6,7=%7,8=%8,9=%9) %+ pause 


:first draft:
:https://www.google.com/search?q=%1+%2+%3+%4+%5+%6+%7+%8+%[9]&tbm=isch&source=lnt&tbs=isz:m&&sa=X&ei=xBL9VNaRArXPsQScz4HgBg&ved=0CBUQpwU&dpr=1.1&biw=1745&bih=864&safe=off&

:added resolution overlay to results by making tbs=imgo:1 instead of isz:m
:in 2024 it seems that the way to do get large has changed and is to make tbc=isz:l and that isz:m has gone away


rem Open 2 different attempts at once:
         https://www.google.com/search?q=%1+%2+%3+%4+%5+%6+%7+%8+%[9]&tbm=isch&source=lnt&tbs=imgo:1&sa=X&ei=xBL9VNaRArXPsQScz4HgBg&ved=0CBUQpwU&dpr=1.1&biw=1745&bih=864&safe=off
    rem  https://www.google.com/search?q=%1+%2+%3+%4+%5+%6+%7+%8+%[9]&tbm=isch&source=lnt&tbs=isz:m&&sa=X&ei=xBL9VNaRArXPsQScz4HgBg&ved=0CBUQpwU&dpr=1.1&biw=1745&bih=864&safe=off
         https://www.google.com/search?q=%1+%2+%3+%4+%5+%6+%7+%8+%[9]&tbm=isch&source=lnt&tbs=isz:l&&sa=X&ei=xBL9VNaRArXPsQScz4HgBg&ved=0CBUQpwU&dpr=1.1&biw=1745&bih=864&safe=off&udm=2



rem 202406 norm https://www.google.com/search?q=Persistence+Of+Time&source=lnt&tbs=imgo:1&sa=X&ei=xBL9VNaRArXPsQScz4HgBg&ved=0CBUQpwU&dpr=1.1&biw=1745&bih=864&safe=off&udm=2
rem 202406 big  https://www.google.com/search?q=Persistence+Of+Time&source=lnt&tbs=isz:l&sca_esv=ee550f040f73c7f6&sca_upv=1&udm=2&sxsrf=ADLYWIKZEgW8-c7oeksR6MMv-sY0npXj4A:1718129300496&sa=X&ved=2ahUKEwi47oi1ktSGAxWXElkFHd-xBFkQpwV6BAgDEAc&biw=1162&bih=532&dpr=1.65


:: 2013 notes from: https://stenevang.wordpress.com/2013/02/22/google-search-url-request-parameters/ 
::  Large images: tbs=isz:l
:: Medium images: tbs=isz:m
:: Icon sized images: tba=isz:i
:: Image size larger than 400×300: tbs=isz:lt,islt:qsvga
:: Image size larger than 640×480: tbs=isz:lt,islt:vga
:: Image size larger than 800×600: tbs=isz:lt,islt:svga
:: Image size larger than 1024×768: tbs=isz:lt,islt:xga
:: Image size larger than 1600×1200: tbs=isz:lt,islt:2mp
:: Image size larger than 2272×1704: tbs=isz:lt,islt:4mp
:: Image sized exactly 1000×1000: tbs=isz:ex,iszw:1000,iszh:1000
::  Images in full color: tbs=ic:color
:: Images in black and white: tbs=ic:gray
:: Images that are red: tbs=ic:specific,isc:red
:: show overlay of resultion: tbs=imgo:1
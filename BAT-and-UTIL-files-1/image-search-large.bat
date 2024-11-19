@on break cancel
@Echo OFF

rem Also used to look up images for album art —— part of an integrated "tool" in mp3-tag, which is used as a step in part of our music intake workflow


:DEBUG: echo * image-search-medium %* called (1=%1,2=%2,3=%3,4=%4,5=%5,6=%6,7=%7,8=%8,9=%9) %+ pause 

set SEARCHFOR=%1+%2+%3+%4+%5+%6+%7+%8+%9

rem :from medium:
rem :https://www.google.com/search?q=%SEARCHFOR%+&tbm=isch&source=lnt&tbs=imgo:1&sa=X&ei=xBL9VNaRArXPsQScz4HgBg&ved=0CBUQpwU&dpr=1.1&biw=1745&bih=864&safe=off&
rem :added resolution overlay to results by making tbs=imgo:1 instead of isz:m
rem : added ,isz:l after imgo:1 to make large
rem :NO!!!!!!! https://www.google.com/search?q=%SEARCHFOR%&safe=off&tbm=isch&source=lnt&tbs=imgo:1,isz:l&sa=X&ei=xBL9VNaRArXPsQScz4HgBg&ved=0CBUQpwU&dpr=1.1&biw=1745&bih=864&safe=off&
rem :NO!!!!!!! https://www.google.com/search?q=%SEARCHFOR%&safe=off&tbs=imgo:1,isz:l&tbm=isch&source=lnt&sa=X&ei=4daNVc78EpCfyASZvor4Cw&ved=0CBUQpwU&dpr=1.25&biw=590&bih=496
rem :NO!!!!!!! https://www.google.com/search?q=%SEARCHFOR%&safe=off&tbs=imgo:1,isz:l&tbm=isch&source=lnt&sa=X&ei=cNeNVY64CIyfyASZlpXABA&ved=0CBUQpwU&dpr=1.25&biw=590&bih=496
rem :NO!!!!!!! https://www.google.com/search?q=%SEARCHFOR%&safe=off&tbs=imgo:1,isz:l&tbm=isch&source=lnt&sa=X&dpr=1.25&biw=590&bih=496
rem :YES!! URL=https://www.google.com/search?q=%SEARCHFOR%&safe=off&tbs=isz:lt,islt:xga&tbm=isch&source=lnt&sa=X&ei=xBL9VNaRArXPsQScz4HgBg&ved=0CBUQpwU&dpr=1.1&biw=1745&bih=864&safe=off&
rem :YES!! URL=https://www.google.com/search?q=%SEARCHFOR%&safe=off&tbs=isz:lt,islt:xga,imgo:1&tbm=isch&source=lnt&sa=X&ei=xBL9VNaRArXPsQScz4HgBg&ved=0CBUQpwU&dpr=1.1&biw=1745&bih=864&safe=off&

set    URL="https://www.google.com/search?q=%SEARCHFOR%&safe=off&tbs=isz:lt,islt:xga,imgo:1&tbm=isch&source=lnt&sa=X&ei=xBL9VNaRArXPsQScz4HgBg&ved=0CBUQpwU&dpr=1.1&biw=1745&bih=864&safe=off&"
echo  %URL%
echos %URL%>clip:
      %URL%




:: from: https://stenevang.wordpress.com/2013/02/22/google-search-url-request-parameters/
:: Large images: tbs=isz:l
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
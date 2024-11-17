@Echo OFF


::::: GET SOURCE FILE:
    set  SOURCE=%1


::::: EXTRACT THE JPGs:
    %COLOR_RUN% 
        ffmpeg -i "%@UNQUOTE[%SOURCE%]"  "%@UNQUOTE[%SOURCE%]-%%%%4d.jpg"

    %COLOR_NORMAL%





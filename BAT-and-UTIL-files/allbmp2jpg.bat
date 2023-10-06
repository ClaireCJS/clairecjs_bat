for %%1 in (*.bmp) convert -quality 100 -verbose "%%1" "%@NAME[%%1].jpg"


color bright yellow on black
    echo * Press any key to deprecate the BMP files ...
    pause>nul
color white on black


call dep *.bmp



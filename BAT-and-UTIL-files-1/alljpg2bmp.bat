for %%1 in (*.jpg) (convert -quality 100 -verbose "%%1" "%@NAME[%%1].bmp")
for %%1 in (*.jpg) (if exist "%@NAME[%%1].bmp" call dep "%%1")


:color bright yellow on black
:    echo * Press any key to deprecate the BMP files ...
:    pause>nul
:color white on black


:call dep *.bmp


@Echo OFF

call validate-in-path convert.exe

for %%1 in (*.bmp) convert -quality 100 -verbose "%%1" "%@NAME[%%1].jpg"


pause Press any key to deprecate the BMP files...

%COLOR_REMOVAL%

call dep *.bmp

%COLOR_normal%



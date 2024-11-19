 on break cancel
 for %%1 in (*.tif) convert -quality 100 -verbose "%%1" "%@NAME[%%1].jpg"


@Echo Off

for %1 in (*.zip) (call unzip-gracefully "%@UNQUOTE[%1]")

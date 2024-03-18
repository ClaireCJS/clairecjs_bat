@Echo OFF

if %FILEMASK_ARCHIVE_VALIDATED ne 1 (call validate-environment-variable FILEMASK_ARCHIVE)

for %1 in (%FILEMASK_ARCHIVE%) (call unzip-gracefully "%@UNQUOTE[%1]")



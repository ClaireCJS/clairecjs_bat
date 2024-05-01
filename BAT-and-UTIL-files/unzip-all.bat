@Echo OFF

if %FILEMASK_ARCHIVE_VALIDATED ne 1 (call validate-environment-variable FILEMASK_ARCHIVE)

echo.

for %%our_current_archive in (%FILEMASK_ARCHIVE%) (call randfg %+ call unzip-gracefully "%@UNQUOTE[%our_current_archive]" %+ call randfg %+ call divider - %+ echo.)




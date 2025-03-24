@loadBTM on
@Echo OFF
@on break cancel

repeat 5 echo.
echo ✨ Mark them as what?
 set AS_WHAT=%@IF["" != "%1",%@UNQUOTE["%1"],?]
eset AS_WHAT

gosub "%BAT%\get-lyrics-for-file.btm" actually_rename_every_file_as_an_instrumental_or_whatever  %@IF["%AS_WHAT%" != "","%AS_WHAT%",]


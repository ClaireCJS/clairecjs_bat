@on break cancel
@Echo off

call unimportant "Generating and editing %emphasis%attrib.lst%deemphasis% in %_CWP"

generate-filelists-by-attribute.pl -n %*

call checkeditor.bat


if "%NOEDIT"=="1" goto :noedit
echo Starting editor... %EDITOR %FILE
start %EDITOR attrib.lst
:noedit

set A=%@FILESIZE[attrib.lst]
echo Returning... Checking filesize to make sure it's not a zero-byte file... %A

if "%A"=="0" *del /q /y attrib.lst


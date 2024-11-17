@echo off

rem Used to accelerate personal image tagging workflow 

call setwidth
call imageindex /s 
unset /q WIDTH
call checkeditor

set NOEDIT=1
call makeattrib -i%PICTURES\generate-filelists-by-attribute-images-and-video-WWW.ini
unset /q NOEDIT

%EDITOR %BAT%\start-tagging-images.bat %PICTURES%\standards-and-practices attrib.lst 

if "%USERNAME"=="claire" start 4NT
%PICTURES%\
if not isdir LISTS (call warning "Where is the %italics_on%LISTS%italics_off% folder?")
if     isdir LISTS (cd LISTS)



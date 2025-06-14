@Echo off
@on error resume
if "%1" == "convert" goto :convert
if "%1" == "resize"  goto :resize


set TARGET=for_discord_uploading

call validate-environment-variable FILEMASK_IMAGE
call validate-in-path fatal_error magick.exe errorlevel iehere askyn celebrate deprecate

iff not exist %FILEMASK_IMAGE% then
        call fatal_error no images here!
        goto /i :END
endiff


if not isdir %TARGET% mkdir %TARGET%
if not isdir %TARGET% call validate-environment-variable TARGET
if not isdir %TARGET% goto :END

copy %FILEMASK_IMAGE% %TARGET%
cd %TARGET%

:convert
for %fff in (*.jfif) do (
  magick "%fff" "%@name[%fff].png"
  if exist    "%@name[%fff].png" del /Q "%fff"
)

:resize
for %fff in (%filemask_image%) do (
  echo fff=%fff ... if %@fileSize[%fff] GT 10485760 
  if %@fileSize["%fff%"] GT 10485760 (
        echo magick "%fff" -define jpeg:extent=10MB "%@name[%fff]_resized.%@ext[%fff]"
        magick "%fff" -define jpeg:extent=10MB "%@name[%fff]_resized.jpg"
        call deprecate "%fff%"
        call errorlevel
  )
)


call celebrate "Converted for discord upload!"

call askyn "Open this folder in explorer?" yes 10

if "Y" == "%ANSWER%" call iehere

:END
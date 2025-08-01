@LoadBTM ON
@echo off
@on break cancel

rem Validate environment:
        iff "1" != "%validated_displayImageDim%" then
                call validate-in-path               magick.exe
                call validate-environment-variables star ansi_colors_have_been_set
                call validate-function              rainbow
                set  validated_displayImageDim=1
        endiff


rem Get filename from arg
        set "IMGFILE=%~1"
        if not defined IMGFILE (
            echo Usage: %~nx0 ^<imagefile^>
            goto :eof
)

rem Check if file exists
        if not exist "%IMGFILE%" (
            echo ❌ File not found: %IMGFILE%
            goto :eof
)

rem Use ImageMagick's `identify` to get dimensions
        for /f "usebackq tokens=2 delims== " %%A in (`magick identify -format "Dimensions=%%wx%%h" "%IMGFILE%"`) do (
            set "DIMENSIONS=%%A"
        )

rem Output:
        set "IMGNAME=%~nx1"
        rem echo.
        echo %STAR% %ansi_color_bright_green%Image filename:   %faint_on%%IMGNAME%%faint_off%
        echo %STAR% Image dimensions: %ansi_color_yellow%%@rainbow[%DIMENSIONS%]


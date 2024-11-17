@Echo OFF

REM validate environment
        call validate-in-path magick.exe

REM validate parameters
        set                                FIRST_PARAMETER_IMAGE_FILENAME=%1
        call validate-environment-variable FIRST_PARAMETER_IMAGE_FILENAME
        set               image=%@UNQUOTE[%FIRST_PARAMETER_IMAGE_FILENAME%]
        if not defined image (call error "%0 couldn't figure out a filename to fix" %+ goto :END)

REM get mode?
                             set   CROP=0
                             set EXPAND=0
        if "%2" eq "crop"   (set   CROP=1)
        if "%2" eq "expand" (set EXPAND=1)
        if "%2" eq "extend" (set EXPAND=1) %+ REM protection from calling this incorrectly due to mis-remembering which word was chosen

REM get the dimensions of the image
        set dimensions=%@EXECSTR[magick.exe identify -format "%%%%wx%%%%h" "%IMAGE%"]
        set      width=%@EXECSTR[magick.exe identify -format "%%%%w"       "%IMAGE%"]
        set     height=%@EXECSTR[magick.exe identify -format       "%%%%h" "%IMAGE%"]
        call unimportant "image: '%image%':: width=%width%, height=%height%, dim=%dimensions%"
        set original_dimensions=%width%x%height%

REM is it square?
        set smaller_is=
        set image_is_square=0
        set image_is_changed=0
        if %height gt %width (set image_is_square=0 %+ set  smaller_is=width)
        if %height lt %width (set image_is_square=0 %+ set  smaller_is=height)
        if %height eq %width (set image_is_square=1 %+ goto :no_resize_needed)

REM If we are here, it is not square and needs fixing:
        REM ** crop **
                if %crop eq 1 (
                    if "%smaller_is%" eq "width"  (set SQUARE_DIMEN=%width% %+ call print-if-debug "crop to %width% square")
                    if "%smaller_is%" eq "height" (set SQUARE_DIMEN=%height %+ call print-if-debug "crop to %height square")
                    magick.exe convert "%IMAGE%" -gravity center -crop %SQUARE_DIMEN%x%SQUARE_DIMEN%+0+0 +repage "%IMAGE%"
                    set image_is_changed=1
                    set action_taken=cropped 
                )
        REM ** expand **
                if %expand eq 1 (
                    if "%smaller_is%" eq "width"  (set SQUARE_DIMEN=%height %+ call print-if-debug "expand to %height square")
                    if "%smaller_is%" eq "height" (set SQUARE_DIMEN=%width% %+ call print-if-debug "expand to %width% square")
                    REM        convert "%IMAGE%"                                       -gravity center -background black -extent %SQUARE_DIMEN%x%SQUARE_DIMEN% "%IMAGE%"
                    magick.exe convert "%IMAGE%" -resize %SQUARE_DIMEN%x%SQUARE_DIMEN% -gravity center -background black -extent %SQUARE_DIMEN%x%SQUARE_DIMEN% "%IMAGE%"

                    set image_is_changed=1
                    set action_taken=expanded
                )
        REM ** resize **
                if %crop ne 1 .and. %expand ne 1 (
                    if "%smaller_is%" eq "width"  (set SQUARE_DIMEN=%height %+ call print-if-debug "resize  width of %width% to be %height")
                    if "%smaller_is%" eq "height" (set SQUARE_DIMEN=%width% %+ call print-if-debug "resize height of %height to be %width%")
                    magick.exe convert "%IMAGE%" -resize %SQUARE_DIMEN%x%SQUARE_DIMEN%! -gravity center -crop %SQUARE_DIMEN%x%SQUARE_DIMEN%+0+0 +repage "%IMAGE%"
                    set image_is_changed=1
                    set action_taken=squished/resized
                ) 


REM if it's changed, let user know:
        :no_resize_needed
        if %image_is_changed eq 1 (
            call get-image-dimensions "%IMAGE%"
            echo %ANSI_BRIGHT_CYAN%*** Image %faint_on%%image%%faint_off% has been %italics_on%%action_taken%%italics_off% from %faint_on%%original_dimensions%%faint_off% to %underline_on%%dimensions%%underline_off%
        )




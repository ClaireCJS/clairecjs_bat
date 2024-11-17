@Echo OFF

REM This is actually the same logic as resizing the image to be square, except we expand the image's canvas with black lines at top/bottom rather than stretching it

REM It's invoked by calling make-image-square but with "expand" as the 2nd parameter to activate expand mode instead of resize mode

call make-image-square %1 expand


@Echo OFF
@Echo off

REM This is actually the same logic as resizing the image to be square, except instead we crop it

REM It's invoked by calling make-image-square but with "crop" as the 2nd parameter to activate crop mode instead of resize mode

call make-image-square %1 crop


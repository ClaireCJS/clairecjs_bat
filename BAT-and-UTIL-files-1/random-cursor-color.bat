@Echo OFF
if  %validated_random_cursor_color ne 1 (
    call validate-functions ANSI_CURSOR_COLOR_HEX RANDOM_RGB_HEX 
    call validate-env-vars  ANSI_PREFERRED_CURSOR_SHAPE
    set  validated_random_cursor_color=1
)
@echos %@ANSI_CURSOR_COLOR_HEX[%@RANDOM_RGB_HEX[]]%ANSI_PREFERRED_CURSOR_SHAPE%

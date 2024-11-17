@Echo OFF

if  %validated_random_cursor_shape ne 1 (
    call validate-functions RANDOM_CURSOR_SHAPE
    set  validated_random_cursor_shape=1
)

@echos %@RANDOM_CURSOR_SHAPE[]

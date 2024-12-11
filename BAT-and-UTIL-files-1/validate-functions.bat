@Echo OFF
@on   break cancel
set   old_val=%VALIDATE_MULTIPLE%
set   VALIDATE_MULTIPLE=1
call  validate-function %*
set   VALIDATE_MULTIPLE=%old_val%

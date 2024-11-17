@Echo OFF

:DESCRIPTION: For un-doing something being marked as deprecated via deprecated.bat

call validate-environment-variable LAST_FILE_DEPPED_OLD skip_validation_existence
call validate-environment-variable LAST_FILE_DEPPED_NEW

ren  "%LAST_FILE_DEPPED_NEW%" "%LAST_FILE_DEPPED_OLD%" 


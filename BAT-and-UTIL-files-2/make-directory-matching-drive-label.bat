@on break cancel
@Echo OFF

setlocal

    rem CONFIGURATION:
            SET DIRECTORY_PREFIX_=!!!! ``
            SET DIRECTORY_POSTFIX= !!!!

    rem VALIDATE:
            set DRIVELETTER=%@STRIP[:,%1]
            if         "%DRIVELETTER%"  eq ""  (call FATAL_ERROR "Must pass a drive letter as argument!" %+ goto :END)
            if "%@READY[%DRIVELETTER%]" eq "0" (call FATAL_ERROR "%DRIVELETTER%: is not ready!!!!!!!!!!" %+ goto :END)

    rem GET LABEL, CALCULATE NEW FOLDER NAME:
            set LABEL=%@LABEL[%DRIVELETTER%]
            set   DIR=%DRIVELETTER%:\%DIRECTORY_PREFIX_%%LABEL%%DIRECTORY_POSTFIX%
            call debug "DIR to match label will be: '%italics_on%%DIR%%italics_off%'"

    rem IF FOLDER DOESN'T EXIST, REMOVE OLD SIMILARLY-NAMED FOLDERS AND MAKE THE NEW ONE:
            *rd /Ne "%DRIVELETTER%:\%DIRECTORY_PREFIX_%*"
            *md "%DIR%"

endlocal

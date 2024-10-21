@Echo off

rem Validate environment:
        call validate-in-path usps-tracking ups-tracking fedex-tracking sleep

rem Validate invocation:
        set NUMBER=%*
        iff "%NUMBER%" eq "" then
                call usage "You gotta supply a tracking number!"
                eset NUMBER
        endif

rem Try each package tracking service that we have a script for:
        call  usps-tracking %NUMBER% %+ call sleep 3
        call fedex-tracking %NUMBER% %+ call sleep 4
        call   ups-tracking %NUMBER% 



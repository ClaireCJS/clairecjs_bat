@Echo OFF
 on break cancel

rem Validate invocation:
        set NUMBER=%*
        iff "%NUMBER%" eq "" then
                call usage "You gotta supply a tracking number!"
                eset NUMBER
        endiff

calla advice "Run 'usps-tracking-lastpackage.bat' if you would like to track the very last package tracked."
set tmptmp=c:\bat\usps-tracking-lastpackage.bat

echos http://www.framed.usps.com/cgi-bin/cttgate/ontrack.cgi?tracknbr= >:u8%tmptmp
echos %NUMBER% >>:u8%tmptmp
call %tmptmp
cls

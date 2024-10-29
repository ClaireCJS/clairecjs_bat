@Echo OFF

rem Validate invocation:
        set NUMBER=%*
        iff "%NUMBER%" eq "" then
                call usage "You gotta supply a tracking number!"
                eset NUMBER
        endiff


set tmptmp=c:\bat\ups-tracking-lastpackage.bat
calla advice "Run 'ups-tracking-lastpackage' if you would like to track the very last package tracked."

echos http://wwwapps.ups.com/WebTracking/processInputRequest?AgreeToTermsAndConditions=yes&InquiryNumber1= >%tmptmp
echos %NUMBER% >>%tmptmp
echos &tdts1.x=36&tdts1.y=5 >>%tmptmp

call %tmptmp
cls

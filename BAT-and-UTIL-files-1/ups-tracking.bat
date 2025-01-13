@Echo OFF
 on break cancel

rem Validate invocation:
        set NUMBER=%*
        iff "%NUMBER%" == "" then
                call usage "You gotta supply a tracking number!"
                eset NUMBER
        endiff


set tmptmp=c:\bat\ups-tracking-lastpackage.bat
calla advice "Run 'ups-tracking-lastpackage' if you would like to track the very last package tracked."

echos http://wwwapps.ups.com/WebTracking/processInputRequest?AgreeToTermsAndConditions=yes&InquiryNumber1= >:u8%tmptmp
echos %NUMBER% >>:u8%tmptmp
echos &tdts1.x=36&tdts1.y=5 >>:u8%tmptmp

call %tmptmp
cls

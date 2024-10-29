@Echo OFF

rem Validate invocation:
        set NUMBER=%*
        iff "%NUMBER%" eq "" then
                call usage "You gotta supply a tracking number!"
                eset NUMBER
        endiff

calla advice "Run 'fedex-tracking-lastpackage' if you would like to track the very last package tracked."
echos Otherwise, 
pause
set tmptmp=c:\bat\fedex-tracking-lastpackage.bat
echos http://www.fedex.com/cgi-bin/tracking?action=track&language=english&last_action=alttrack&ascend_header=1&cntry_code=us&initial=x&mps=y&tracknumbers= >%tmptmp
echos %NUMBER% >>%tmptmp
REM echos &TypeOfInquiryNumber=T&HTMLVersion=4.0&tracknums_displayed=5&sort_by=status&line1= >>%tmptmp
REM echos %1 >>%tmptmp
REM echos &tdts1.x=36&tdts1.y=5 >>%tmptmp
call %tmptmp
cls

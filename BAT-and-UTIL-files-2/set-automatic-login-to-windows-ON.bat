@Echo OFF
@on break cancel
 cls

call validate-environment-variables MAPPING_DEMONA_PWD MAPPING_DEMONA_USR invisible_on invisible_off blink_on blink_off
call validate-in-path               repeat warning set eset reg.exe errorlevel.bat success.bat debug.bat

set repeat=4
repeat %repeat% call warning "About to turn automatic login on! [%_repeat/%repeat%]"
rem call warning "About to turn automatic login on! [4]"
rem call warning "About to turn automatic login on! [3]"
rem call warning "About to turn automatic login on! [2]"
rem call warning "About to turn automatic login on! [1]"
rem call warning "About to turn automatic login on! [0]"

pause


rem DEFAULT USERNAME:
         set OUR_USER_NAME_TO_LOG_IN_WITH=%MAPPING_DEMONA_USR%
         set OUR_PASS_WORD_TO_LOG_IN_WITH=%MAPPING_DEMONA_PWD%

call debug "About to set automatic login in with username='%blink_on%%OUR_USER_NAME_TO_LOG_IN_WITH%%blink_off%', password='%invisible_on%%OUR_PASS_WORD_TO_LOG_IN_WITH%%invisible_off%'
pause
call errorlevel 
pause
pause


reg  add "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" /v AutoAdminLogon  /t REG_SZ /d   1                              /f %+ call errorlevel
reg  add "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" /v DefaultUserName /t REG_SZ /d "%OUR_USER_NAME_TO_LOG_IN_WITH%" /f %+ call errorlevel
reg  add "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" /v DefaultPassword /t REG_SZ /d "%OUR_PASS_WORD_TO_LOG_IN_WITH%" /f %+ call errorlevel
reg  add "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" /v DefaultPassWord /t REG_SZ /d "%OUR_PASS_WORD_TO_LOG_IN_WITH%" /f %+ call errorlevel

call success "Automatic login turned %blink_on%ON%blink_off%!"




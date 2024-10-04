@Echo OFF
 cls

call validate-environment-variables MAPPING_DEMONA_PWD MAPPING_DEMONA_USR invisible_on invisible_off blink_on blink_off
call validate-in-path               repeat warning set eset reg.exe errorlevel.bat success.bat debug.bat

repeat 8 call warning "About to turn automatic login on! [%_repeat/8]"
rem call warning "About to turn automatic login on! [4]"
rem call warning "About to turn automatic login on! [3]"
rem call warning "About to turn automatic login on! [2]"
rem call warning "About to turn automatic login on! [1]"
rem call warning "About to turn automatic login on! [0]"

cls


rem DEFAULT USERNAME:
         rem set DEFAULT_USER_NAME_TO_LOG_IN=Claire
         rem eset DEFAULT_USER_NAME_TO_LOG_IN
         set     OUR_USER_NAME_TO_LOG_IN_WITH=%MAPPING_DEMONA_USR%
         set     OUR_PASS_WORD_TO_LOG_IN_WITH=%MAPPING_DEMONA_PWD%

call debug "About to set automatic login in with username='%blink_on%%ROUR_USER_NAME_TO_LOG_IN_WITH%%blink_off%', password=%invisible_on%'%OUR_PASS_WORD_TO_LOG_IN_WITH%'%invisible_off%
pause

reg  add "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" /v AutoAdminLogon  /t REG_SZ /d    1    /f
call errorlevel
reg  add "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" /v DefaultUserName /t REG_SZ /d "%OUR_USER_NAME_TO_LOG_IN_WITH%" /f
call errorlevel
reg  add "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" /v DefaultPassword /t REG_SZ /d "%OUR_USER_NAME_TO_LOG_IN_WITH%" /f
call errorlevel
reg  add "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" /v DefaultPassWord /t REG_SZ /d "%OUR_USER_NAME_TO_LOG_IN_WITH%" /f
call errorlevel

call success "Automatic login turned %blink_on%ON%blink_off%!"




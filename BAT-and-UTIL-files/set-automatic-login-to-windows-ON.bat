@Echo OFF
 cls

call warning "About to turn automatic login on! [5]"
call warning "About to turn automatic login on! [4]"
call warning "About to turn automatic login on! [3]"
call warning "About to turn automatic login on! [2]"
call warning "About to turn automatic login on! [1]"
call warning "About to turn automatic login on! [0]"

cls


rem DEFAULT USERNAME:
         set      DEFAULT_USER_NAME_TO_LOG_IN=Claire
        eset      DEFAULT_USER_NAME_TO_LOG_IN
         set DUN=%DEFAULT_USER_NAME_TO_LOG_IN%
    


reg  add "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" /v AutoAdminLogon  /t REG_SZ /d    1    /f
call errorlevel
reg  add "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" /v DefaultUserName /t REG_SZ /d "%DUN%" /f
call errorlevel

call success "Automatic login turned off!"




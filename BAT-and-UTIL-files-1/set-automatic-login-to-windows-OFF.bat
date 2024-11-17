@Echo OFF

call warning "About to turn automatic login off! [5]"
call warning "About to turn automatic login off! [4]"
call warning "About to turn automatic login off! [3]"
call warning "About to turn automatic login off! [2]"
call warning "About to turn automatic login off! [1]"
call warning "About to turn automatic login off! [0]"

cls

reg  add   "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" /v AutoAdminLogon  /t REG_SZ /d 0 /f
call errorlevel
reg delete "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" /v DefaultUserName /f
call errorlevel

call success "Automatic login turned off!"


netsh advfirewall firewall add rule name="PsExec" dir=in action=allow protocol=TCP localport=445
netsh advfirewall firewall add rule name="PsExec" dir=in action=allow protocol=TCP localport=139

rem ntrights -u carolyn +r SeBatchLogonRight
rem ntrights -u carolyn +r SeInteractiveLogonRight

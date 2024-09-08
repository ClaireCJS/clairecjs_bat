t@Echo OFF

start netplwiz


%COLOR_ADVICE%
echo Requiring the user to enter credentials when his computer starts is an important part of Windows security. If a user account automatically logs on, anyone who has physical access to the computer can restart it and access the user’s files. Nonetheless, there are scenarios where a computer is physically secure and automatic logon might be desired. To configure a workgroup computer (you cannot perform these steps on a domain member) to automatically log on, follow these steps:
echo. 
echo 1. Click Start, type netplwiz, and then press Enter.
echo 2. In the User Accounts dialog box, click the account you want to automatically log on to.If it is available, clear the Users Must Enter A User Name And Password To Use This Computer check box.
echo 3. Click OK. 
echo 4. In the Automatically Log On dialog box, enter the user’s password twice and click OK. 
echo. 
echo The next time you restart the computer, it will automatically log on with the local user account you selected. Configuring automatic logon stores the user’s password in the registry unencrypted, where someone might be able to retrieve it. 
echo. 
%COLOR_NORMAL% 
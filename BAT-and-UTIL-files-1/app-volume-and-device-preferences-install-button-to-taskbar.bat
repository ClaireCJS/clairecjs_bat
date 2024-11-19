@Echo OFF
 on break cancel

cls
echo Trying to install button to go directly to app-volume-preferences ... to the QuickLaunchBar

echo We will also install a copy of the icon to your desktop, so that it can be dragged to the launchbar in case the first step didn't work.

echo Here we go!

pause

@copy c:\bat\app-volume-and-device-preferences.lnk "%appdata%\Microsoft\Internet Explorer\Quick Launch\User Pinned\TaskBar\app vol.lnk"

@copy c:\bat\app-volume-and-device-preferences.lnk %USERPROFILE%\OneDrive\Desktop

echo All done! Good luck!
pause



@on break cancel
@Echo OFF


rem Install Winget with powershell:

        powershell -Command "Add-AppxPackage -RegisterByFamilyName -MainPackage Microsoft.DesktopAppInstaller_8wekyb3d8bbwe"
        cls 
        echo If that didn't work, then try this instead: powershell -Command "Add-AppxPackage -Path \"https://aka.ms/getwinget\""
        




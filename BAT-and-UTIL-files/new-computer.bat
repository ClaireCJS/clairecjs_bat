@Echo OFF




::::: BOOKMARKS:
    set CALIBRATION_URL=http://www.lagom.nl/lcd-test/





::::: PRE-CHECK:
    call checkeditor
    call validate-environment-variables BAT MACHINENAME

::::: SETUP:
    %BAT%\

::::: GET COMPUTER NAME:
    color yellow on black %+ echo What will this computer be named? %+ color white on black 
     set NEW_COMPUTER_NAME=?????
    eset NEW_COMPUTER_NAME


::::: EDIT BAT/ENVIRONMENT FILES:
    %BAT%\
    %EDITOR% environm.btm autoexec-common.btm allcomputers.bat allcomputersexceptself.bat backup-stuff.BAT drives.bat display-drive-mapping.bat fr.bat wake-computers.bat

::::: HOSTS?
    echo. %+ call warning "Hey, we probably need to edit hosts to put this computer in." %+ pause %+ color white on black
    call hosts

::::: VALIDATE PERL SCRIPTS:
    %BAT%
    call validate-all-perl-files
    echo.
    call success "Perl files validated"
    echo. %+ echo. %+ echo. %+ echo. %+ echo. %+ echo. %+ echo. %+ echo. 

:::: SET POWERSHELL STUFF:

    call new-computer.ps1 %+ rem this does: Set-ExecutionPolicy -ExecutionPolicy Bypass


:::: SHARE WHAT WE CAN:
    call create-all-drive-shares-(for-new-installations).bat

::::: OTHER REMINDERS:    
    pause %+ call warning "Run install-common-programs-with-winget.bat in another window now, then come back here"            
    pause
    pause %+ call warning "After installing perl to c:\perl\, run c:\bat\setup-perl-junctions-on-new-computer.bat"            
    pause %+ call warning "Change EditPlus preferences to syntax-highlight TXT files as .CPP files"            
    pause %+ call warning "Let's calibrate our monitor at %ITALICS_ON%%CALIBRATION_URL%%ITALICS_OFF%" %+ pause %+ pause %+ %CALIBRATION_URL%
    pause %+ call advice  "if we still command-line-blog: Test mtsend.bat, install python-2.5.2.msi for mtsend" 

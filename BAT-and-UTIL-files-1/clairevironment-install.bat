@Echo OFF
@rem ****************************** Claire-vironment install script ******************************
 on break cancel



@rem Intro
if "%1" == "force" goto :force_1
cls
echo .
echo .
echo .
echo This will only work if this is an administrator-level CMD line!
echo .
net session >nul 2>&1 || (echo ** THIS APPEARS TO NOT BE AN ADMINISTRATOR-LEVEL CMD.EXE !!! If wrong, run Clairevironment-install 'force' &goto :eof)
echo .
echo .
echo .
echo .
echo .
echo .
echo .
echo .
echo .
:force_1






@rem Install WinGet:
@echo .
@echo *** Attempting to install WinGet using powershell's Add-AppxPackage command: ***
@echo .
powershell -Command "Add-AppxPackage -Path \"https://aka.ms/getwinget\""




@rem Add winget to our path so it works at the command line:
@echo .
@echo *** Attempting to add WinGet to the path: ***
@echo .
path=%path%;"%LOCALAPPDATA%\Microsoft\WindowsApps\";c:\bat\;c:\util;c:\windows\system32;c:\cygwin\bin;c:\cygwin64\bin;c:\MinGW\bin;C:\UTIL\sysinternals;C:\Windows;C:\Windows\system32;C:\Windows\System32\WindowsPowerShell\v1.0\;C:\Windows\System32\OpenSSH;c:\TCMD;C:\Windows\system32\Wbem;c:\TCMD29;c:\TCMD30;c:\TCMD32

@cls
@echo *** Validation #1: Winget needs to be in your Path for this to work ***
@echo .
@echo *** If winget is in your path, hitting a key should produce output: ***
@pause
winget
@echo .
@echo .
@echo *** Is there winget usage instructions above, or an error that winget is not in the path? ***
@echo *** If there was an error, you need to get winget installed such that 'winget' works. ***
@echo *** If there was winget usage output and no error, then: ***
@pause
@pause





@cls
@echo .
@echo *** Attempting to install JPSoft's TCC/TakeCommand command line using winget: ***
@echo .
winget install --location c:\TMCD\ JPSoft.tcmd
@echo .
pause
@echo .
echo  * Attempting to create junction at c:\TCMD\ pointing to TCC install location
echo    (Not applicable if you installed it manually to C:\TCMD)
if exist "c:\Program Files\JPSoft\TCMD33" mklink /d c:\TCMD\ "c:\Program Files\JPSoft\TCMD33" >nul
if exist "c:\Program Files\JPSoft\TCMD34" mklink /d c:\TCMD\ "c:\Program Files\JPSoft\TCMD34" >nul
if exist "c:\Program Files\JPSoft\TCMD35" mklink /d c:\TCMD\ "c:\Program Files\JPSoft\TCMD35" >nul
if exist "c:\Program Files\JPSoft\TCMD36" mklink /d c:\TCMD\ "c:\Program Files\JPSoft\TCMD36" >nul
if exist "c:\Program Files\JPSoft\TCMD37" mklink /d c:\TCMD\ "c:\Program Files\JPSoft\TCMD37" >nul
if exist "c:\Program Files\JPSoft\TCMD38" mklink /d c:\TCMD\ "c:\Program Files\JPSoft\TCMD38" >nul
if exist "c:\Program Files\JPSoft\TCMD39" mklink /d c:\TCMD\ "c:\Program Files\JPSoft\TCMD39" >nul
if exist "c:\Program Files\JPSoft\TCMD40" mklink /d c:\TCMD\ "c:\Program Files\JPSoft\TCMD40" >nul
if exist "c:\Program Files\JPSoft\TCMD41" mklink /d c:\TCMD\ "c:\Program Files\JPSoft\TCMD41" >nul
if exist "c:\Program Files\JPSoft\TCMD42" mklink /d c:\TCMD\ "c:\Program Files\JPSoft\TCMD42" >nul
if exist "c:\Program Files\JPSoft\TCMD43" mklink /d c:\TCMD\ "c:\Program Files\JPSoft\TCMD43" >nul
if exist "c:\Program Files\JPSoft\TCMD44" mklink /d c:\TCMD\ "c:\Program Files\JPSoft\TCMD44" >nul
if exist "c:\Program Files\JPSoft\TCMD45" mklink /d c:\TCMD\ "c:\Program Files\JPSoft\TCMD45" >nul
if exist "c:\Program Files\JPSoft\TCMD46" mklink /d c:\TCMD\ "c:\Program Files\JPSoft\TCMD46" >nul
if exist "c:\Program Files\JPSoft\TCMD47" mklink /d c:\TCMD\ "c:\Program Files\JPSoft\TCMD47" >nul
if exist "c:\Program Files\JPSoft\TCMD48" mklink /d c:\TCMD\ "c:\Program Files\JPSoft\TCMD48" >nul
if exist "c:\Program Files\JPSoft\TCMD49" mklink /d c:\TCMD\ "c:\Program Files\JPSoft\TCMD49" >nul
if exist "c:\Program Files\JPSoft\TCMD50" mklink /d c:\TCMD\ "c:\Program Files\JPSoft\TCMD50" >nul
if exist "c:\Program Files\JPSoft\TCMD51" mklink /d c:\TCMD\ "c:\Program Files\JPSoft\TCMD51" >nul
if exist "c:\Program Files\JPSoft\TCMD52" mklink /d c:\TCMD\ "c:\Program Files\JPSoft\TCMD52" >nul
if exist "c:\Program Files\JPSoft\TCMD53" mklink /d c:\TCMD\ "c:\Program Files\JPSoft\TCMD53" >nul
if exist "c:\Program Files\JPSoft\TCMD54" mklink /d c:\TCMD\ "c:\Program Files\JPSoft\TCMD54" >nul
if exist "c:\Program Files\JPSoft\TCMD55" mklink /d c:\TCMD\ "c:\Program Files\JPSoft\TCMD55" >nul
if exist "c:\Program Files\JPSoft\TCMD56" mklink /d c:\TCMD\ "c:\Program Files\JPSoft\TCMD56" >nul
@echo .
@echo .
@echo .
@echo *** Validation #1: TCC (JPSoft's TakeCommand) needs to be in c:\TCMD\ for this script to work ***
@echo .
@echo *** If TCC is properly installed, hitting a key should produce a list of files in c:\TCMD\: ***
@pause
@cls
dir c:\TCMD
@echo .
@echo .
@echo *** Is there a list of files in c:\TCMD\ above, or does it say 'File Not Found' or such? ***
echo.
@echo *** Or perhaps issue a c:\bat\junction.exe c:\tcmd\ c:\WHEREVER_IT_ENDED_UP_BEING_INSTALLED ***
echo.
echo *** Please break out of this script if that is the case; nothing else will work ***
echo *** Please break out of this script if that is the case; nothing else will work ***
echo *** Please break out of this script if that is the case; nothing else will work ***
echo *** Please break out of this script if that is the case; nothing else will work ***
echo *** Please break out of this script if that is the case; nothing else will work ***
echo *** Please break out of this script if that is the case; nothing else will work ***
echo *** Please break out of this script if that is the case; nothing else will work ***
echo *** Please break out of this script if that is the case; nothing else will work ***
echo *** Please break out of this script if that is the case; nothing else will work ***
echo.
@echo *** If there was a list of files in c:\TCMD\ and no error, then: ***
@pause








@cls
@echo *********************************************************************************
@echo *** At this point, it appears that we have Winget and TCC installed properly! ***
@echo *** Let us proceed with installing the pretentiously-named Clairevironment... ***
@echo *********************************************************************************
@pause




@cls
@echo .........................................................................
@echo ...Installing Git...apologies if you already have it: enjoy the update...
@echo ...Installing Git...apologies if you already have it: enjoy the update...
@echo ...Installing Git...apologies if you already have it: enjoy the update...
@echo .........................................................................
winget install --id Git.Git -e --source winget
@pause


@cls
@echo .................................
@echo ...Installing Windows Terminal...
@echo ...Installing Windows Terminal...
@echo ...Installing Windows Terminal...
@echo .................................
winget install -e --id Microsoft.WindowsTerminal
@pause

@cls
@echo .......................
@echo ...Installing Cygwin...
@echo ...Installing Cygwin...
@echo ...Installing Cygwin...
@echo .......................
winget install --id=Cygwin.Cygwin -e
@pause

@cls
@echo ................................
@echo ...Installing Strawberry Perl...
@echo ...Installing Strawberry Perl...
@echo ...Installing Strawberry Perl...
@echo ................................
winget install -e --id StrawberryPerl.StrawberryPerl
@pause

@cls
@echo ........................................
@echo ...Moving Strawberry Perl to c:\perl\...
@echo ...Moving Strawberry Perl to c:\perl\...
@echo ...Moving Strawberry Perl to c:\perl\...
@echo ........................................
move c:\strawberry c:\perl
@echo .
@echo Does it look like the files properly moved to c:\perl\?  
@echo If so, then:
@pause






@cls
@echo ................................
@echo ...Installing Anaconda Python...
@echo ...Installing Anaconda Python...
@echo ...Installing Anaconda Python...
@echo ................................
winget install --id=Anaconda.Anaconda3 -e
@pause





@cls
@echo .........................
@echo ...Installing EditPlus...
@echo ...Installing EditPlus...
@echo ...Installing EditPlus...
@echo .........................
winget install ES-Computing.EditPlus
@pause







@cls
@echo .................................
@echo ...Installing Claire's scripts...
@echo ...Installing Claire's scripts...
@echo ...Installing Claire's scripts...
@echo .................................
git clone http://www.github.com/clairecjs/clairecjs_bat c:\clairecjs_bat.tmp
@pause




@cls
@echo ........................................
@echo ...About to move Claire's scripts to c:\bat\...
@echo ...About to move Claire's scripts to c:\bat\...
@echo ...About to move Claire's scripts to c:\bat\...
@echo ........................................
pause
move c:\clairecjs_bat.tmp\BAT-and-util-files-1 c:\bat
@echo .............................................
@echo ...Done moving Claire's scripts to c:\bat\...
@echo ...Done moving Claire's scripts to c:\bat\...
@echo ...Done moving Claire's scripts to c:\bat\...
@echo .............................................
@echo .
@echo .
@rem Gotta make these just in case I have them hardcoded:
@if not exist c:\util md c:\util 
@if not exist c:\util md c:\util2
@echo :) >"c:\util\__ put permanent binaries that you can't function without, that you want in your path, in here __"
@echo :) >"c:\util2\__ put permanent portable programs (and large things) that you CAN function without, in here __"
@rem TODO util-dist.bat
@echo (And also making c:\util and c:\util2 folders.)
@echo Use c:\util\  for any binaries you want to keep, and have in your path, for perpetuity. Things you can't function without.
@echo Use c:\util2\ for large things. Portable programs that you want to keep for perpetuity. Things you can function without.
@echo .
@echo .
@pause


@cls
@echo ................................................
@echo ...Copying Claire's tcstart.bat into c:\TCMD\...
@echo ...Copying Claire's tcstart.bat into c:\TCMD\...
@echo ...Copying Claire's tcstart.bat into c:\TCMD\...
@echo .................................
copy c:\bat\tcstart.bat c:\tcmd\tcstart.bat
@pause




@cls
@echo ..................
@echo ...Setting path...
@echo ...Setting path...
@echo ...Setting path...
@echo ..................
@echo * Updating current path:
PATH=c:\bat\;%PATH%
@echo * Updating windows system variable path for current user:
setx    PATH "c:\bat\;%PATH%". N
@echo * Updating windows system variable path for all users:
setx /m PATH "c:\bat\;%PATH%". N
@echo * Running Claire's dynamically-generated path:
call c:\bat\setpath.bat
@pause


@cls
@echo ...................................................................
@echo ...Extracting Claire's Perl libraries to c:\perl\perl\site\lib\Clio\...
@echo ...Extracting Claire's Perl libraries to c:\perl\perl\site\lib\Clio\...
@echo ...Extracting Claire's Perl libraries to c:\perl\perl\site\lib\Clio\...
@echo ...................................................................
cd c:\perl\perl\site\lib\
md Clio
cd Clio
unzip c:\bat\perl-sitelib-Clio.zip
@echo ............................................................................
@echo ...Done extracting Claire's Perl libraries to c:\perl\perl\site\lib\Clio\...
@echo ...Done extracting Claire's Perl libraries to c:\perl\perl\site\lib\Clio\...
@echo ...Done extracting Claire's Perl libraries to c:\perl\perl\site\lib\Clio\...
@echo ............................................................................
@pause


@cls
@echo .........................................................................................................
@echo ...Downloading Claire's Python libraries to c:\ProgramData\anaconda3\lib\site-packages\clairecjs_utils...
@echo ...Downloading Claire's Python libraries to c:\ProgramData\anaconda3\lib\site-packages\clairecjs_utils...
@echo ...Downloading Claire's Python libraries to c:\ProgramData\anaconda3\lib\site-packages\clairecjs_utils...
@echo .........................................................................................................
cd c:\ProgramData\anaconda3\lib\site-packages\
md clairecjs_utils
cd clairecjs_utils
git clone http://www.github.com/clairecjs/clairecjs_utils
@pause
@echo .
@echo .
@echo .
@echo *** NOTE: I haven't verified that winget installs python to c:\ProgramData\anaconda3 ***
@echo ***         We should probably double-check that it's there, so let's do that now... ***
@pause
@echo .
@echo .
@echo .
@echo *** Let's just do a quick directory to take a look at c:\ProgramData\anaconda3\: ***
@echo .
dir c:\ProgramData\anaconda3
@echo .
@echo .
@echo *** Is it there? A bunch of stuff, and not just 1 folder? ***
@echo *** If it's just 1 folder, you're going to need to move clairecjs_utils to the right place ***
@echo *** If it's the full Anaconda Python installation with a bunch of files in it, then: ***
@pause
@echo .
@echo .
@echo .
@echo *** Now let's look inside the clairecjs_utils folder ***
@echo *** We should see some python files, including several that start with "claire" ***
@pause
@echo .
dir c:\ProgramData\anaconda3\lib\site-packages\clairecjs_utils
@echo .
@echo *** If the above command shows an empty folder, or an error, something went wrong ***
@echo *** If you see several python files, including several that start with "claire", then: ***
@pause





@cls
@echo Now it is time for you to set your Clairevironment machine name and OS 
@echo .
@echo Open up c:\TCMD\tcstart.bat in a text editor and change the values for OS and MACHINENAME.
@echo .
@echo For OS, I  currently use Windows 10, so  I  have: set OS=10
@echo For OS, You probably use Windows 11, so you want: set OS=11
@echo .
@echo For MACHINENAME, name your machine whatever you want! Just make sure its unique!
@echo .
@pause
notepad c:\tcmd\tcstart.bat
@pause


`   



@cls
@echo *** Now it is time for you to edit environm.btm to suit your needs. ***
@echo .
@echo *** Open up c:\bat\environ.btm and have at it. ***
@echo *** See https://github.com/ClaireCJS/clairecjs_bat/blob/main/README.md for instructions ***
@echo .
@pause
notepad c:\bat\environm.btm
@pause







@cls
@echo *** Finally, some parting advice for new machines entering the Clairevironent: ***
@echo .
@echo *** 1) Run new-computer.btm to take care of some new-computer loose ends ***
@echo *** 2) Run install-common-programs-with-winget.bat to install a TON of commonly-used programs! ***
@echo .
@echo .
@echo .
@echo .
@echo *** We can do that now if you'd like! ***
@echo *** To run new-computer.bat (which will open several scripts in your text editor): ***
@pause
call c:\bat\new-computer.btm
@echo .
@echo .
@echo .
@echo *** To run install-common-programs-with-winget.bat (will take awhile, and possibly need user input): ***
@pause
@echo *** First, let's open it up in notepad. ***
@echo *** You can remove programs you don't want to install by removing them from the script ***
@echo *** You can also just ignore it and close it! ***
notepad c:\bat\install-common-programs-with-winget-helper.cmd
@pause
@echo .
@echo .
@echo .
@echo .
@echo .
@echo .
@echo .
@echo .
@echo *** Now, let's install the programs in the script we just opened ***
@echo *** If you get bored and just want to continue to the next step, try Ctrl-C'ing out of this part: ***
@pause
call c:\bat\install-common-programs-with-winget-helper.cmdc
@echo .
@echo .
@echo .
@echo .
@echo *** Common programs installed! 
@pause



@cls
@echo *** All done! Enjoy your command-line with bonus goodies! ***
@echo *** All done! Enjoy your command-line with bonus goodies! ***
@echo *** All done! Enjoy your command-line with bonus goodies! ***
@echo .
@echo .
@echo .
@echo "             ================================================.             "
@echo "                  .-.   .-.     .--.                         !             "
@echo "                 | OO| | OO|   / _.-' .-.   .-.  .-.   .''.  !             "
@echo "                 |   | |   |   \  '-. '-'   '-'  '-'   '..'  !             "
@echo "                 '^^^' '^^^'    '--'                         !             "
@echo "             ===============.  .-.  .================.  .-.  !             "
@echo "                            | |   | |                |  '-'  !             "
@echo "                            | ':-:' |                |       !             "
@echo "                            |  '-'  |                |  .-.  !             "
@echo "             ==============='       '================'  '-'  !             "
@echo .
@echo .
@echo .
@echo *** All done! Enjoy your command-line with bonus goodies! ***
@echo *** All done! Enjoy your command-line with bonus goodies! ***
@echo *** All done! Enjoy your command-line with bonus goodies! ***
@echo .

   
:eof

@Echo OFF
:Echo ON

if "%DEBUG_DEPTH%" eq "1" echo * setpath.bat (batch=%_BATCH)

::::: DOCUMENTATION:
	:: WHAT THIS DOES: 	set PATH for all computers!
	:: ASSUMES: 		%MACHINENAME% and %OS% (95,98,ME,2K,XP,7,10) has already been set in the environment
    :: ASSUMES:         %BAT%=C:\BAT\ and %UTIL%=C:\UTIL\ (and optional %UTIL2%=C:\UTIL2) copied from another Clairevironment
    ::                  Normally we would validate these with validate-environment-variables.bat but we want speediness

::::: First, unset the old path:
	unset /q PATH

::::: THEN, we add the very basic path that we want ANYWHERE:
	:Base_Clairevironment_Related_1
		gosub AddFolderToPathEndOnlyIfItExists  c:\util\e
		gosub AddFolderToPathEndOnlyIfItExists  c:\util\aspell\bin
		gosub AddFolderToPathEndOnlyIfItExists  c:\cygwin\bin
		gosub AddFolderToPathEndOnlyIfItExists  c:\cygwin64\bin
		gosub AddFolderToPathEndOnlyIfItExists  c:\MinGW\bin
	:Work_Related_1
		:osub AddFolderToPathEndOnlyIfItExists  %DROPBOX%\work\bat\
		gosub AddFolderToPathEndOnlyIfItExists  C:\bat\work
	:Base_Clairevironment_Related_2
		gosub AddFolderToPathEndOnlyIfItExists  c:\perl\bin
        ::: Changed these 3 from AddToPathBeg to AddToPathEnd on 20230503:
            gosub AddFolderToPathBegOnlyIfItExists  C:\perl\c\bin
            :osub AddFolderToPathEndOnlyIfItExists  C:\perl\c\bin
            gosub AddFolderToPathBegOnlyIfItExists  c:\perl\perl\bin
            :osub AddFolderToPathEndOnlyIfItExists  c:\perl\perl\bin
            gosub AddFolderToPathBegOnlyIfItExists  c:\perl\perl\site\bin
            :osub AddFolderToPathEndOnlyIfItExists  c:\perl\perl\site\bin
		gosub AddFolderToPathEndOnlyIfItExists  c:\python23
		gosub AddFolderToPathEndOnlyIfItExists  c:\python
		gosub AddFolderToPathEndOnlyIfItExists  %UTIL%\sysinternals
		gosub AddFolderToPathEndOnlyIfItExists  %UTIL%\xml
		gosub AddFolderToPathEndOnlyIfItExists  %UTIL2%\git\bin
		gosub AddFolderToPathEndOnlyIfItExists  %UTIL2%
		gosub AddFolderToPathEndOnlyIfItExists  %UTIL2%\nmap
		gosub AddFolderToPathEndOnlyIfItExists  %UTIL2%\emulation\xbox
	:Programs_That_May_Be_Installed_That_I_Script_With_Or_Use
		gosub AddFolderToPathEndOnlyIfItExists "%ProgramFiles%\FastPictureViewer"
		gosub AddFolderToPathBegOnlyIfItExists "%ProgramFiles%\ImageMagick"
		gosub AddFolderToPathBegOnlyIfItExists "%[ProgramFiles(x86)]\ImageMagick-6.3.3-Q16"
		gosub AddFolderToPathBegOnlyIfItExists "%ProgramFiles%\nodejs"
		gosub AddFolderToPathEndOnlyIfItExists "%ProgramFiles%\PHP"
		gosub AddFolderToPathBegOnlyIfItExists "%ProgramFiles\SlikSvn\bin"
		gosub AddFolderToPathEndOnlyIfItExists "%ProgramFiles\TortoiseSVN\bin"
                                                                set C_RSYNCD_BIN=0
                                      if isdir "c:\rsyncd\bin" (set C_RSYNCD_BIN=1)
		gosub AddFolderToPathEndOnlyIfItExists "c:\rsyncd\bin"
	:Java_Versions
		gosub AddFolderToPathEndOnlyIfItExists "%ProgramFiles%\Java\jdk1.6.0_35\bin"
		gosub AddFolderToPathEndOnlyIfItExists "%ProgramFiles%\Java\jdk1.7.0_25\bin"
		gosub AddFolderToPathEndOnlyIfItExists "%ProgramFiles%\Java\jdk1.7.0_76\bin"
		gosub AddFolderToPathEndOnlyIfItExists "%ProgramFiles(x86)%\Java\jre6\bin"
		gosub AddFolderToPathEndOnlyIfItExists "%ProgramFiles(x86)%\Java\jdk1.7.0_25\bin"
		gosub AddFolderToPathEndOnlyIfItExists      "%ProgramFiles%\Common Files\Oracle\Java\javapath"
		gosub AddFolderToPathEndOnlyIfItExists "%ProgramFiles(x86)%\Common Files\Oracle\Java\javapath"
	:Oracle_Versions
		gosub AddFolderToPathEndOnlyIfItExists  C:\oraclexe\app\oracle\product\11.2.0\server\bin
	:Work_Inspired
		gosub AddFolderToPathEndOnlyIfItExists  "%ProgramFiles%\Common Files\Microsoft Shared\Microsoft Online Services"
		gosub AddFolderToPathEndOnlyIfItExists  "%ProgramFiles(x86)%\Common Files\Microsoft Shared\Microsoft Online Services"
		gosub AddFolderToPathEndOnlyIfItExists  "%ProgramFiles%\Intel\WiFi\bin\"
		gosub AddFolderToPathEndOnlyIfItExists  "%ProgramFiles%\Common Files\Intel\WirelessCommon\"
	:Work_Related_2
		gosub AddFolderToPathEndOnlyIfItExists "C:\perl\instantclient"
	:Stuff_We_Want_At_The_Very_End
        gosub AddFolderToPathEndOnlyIfItExists "C:\Program Filnes\Git\bin"
    :2023
        :Anaconda.MiniConda//conda.exe stuff
            gosub AddFolderToPathEndOnlyIfItExists  C:\ProgramData\anaconda3\condabin\
            gosub AddFolderToPathEndOnlyIfItExists  C:\ProgramData\anaconda3\Scripts\
            gosub AddFolderToPathEndOnlyIfItExists  C:\ProgramData\anaconda3\Library\bin\
            gosub AddFolderToPathEndOnlyIfItExists  C:\ProgramData\miniconda3\condabin\
            gosub AddFolderToPathEndOnlyIfItExists  C:\ProgramData\miniconda3\Scripts\
            gosub AddFolderToPathEndOnlyIfItExists  C:\ProgramData\miniconda3\Library\bin\
            gosub AddFolderToPathEndOnlyIfItExists "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.1\bin"
            gosub AddFolderToPathEndOnlyIfItExists "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.1\lib\x64"
            gosub AddFolderToPathEndOnlyIfItExists "T:\ProgramData.Demona.ssd-spillover\anaconda3\Lib\site-packages\torch\lib\x64"
            gosub AddFolderToPathEndOnlyIfItExists                                  "c:\anaconda3\Lib\site-packages\torch\lib\x64"
            gosub AddFolderToPathEndOnlyIfItExists "C:\Program Files\Graphviz\bin"
            :gosub AddFolderToPathEndOnlyIfItExists 
        :SmartGPT, Chocolatey, Docker
            gosub AddFolderToPathEndOnlyIfItExists %USERPROFILE%\.cargo\bin
            gosub AddFolderToPathEndOnlyIfItExists %allusersprofile%\chocolatey\bin\
            gosub AddFolderToPathEndOnlyIfItExists "C:\Program Files\Docker\cli-plugins"
            gosub AddFolderToPathEndOnlyIfItExists "C:\Program Files\Docker\Docker\resources\bin"
            gosub AddFolderToPathEndOnlyIfItExists "C:\ProgramData\anaconda3\Lib\site-packages\torch\lib"
    :2024
            gosub AddFolderToPathEndOnlyIfItExists "C:\Program Files\WindowsApps\Microsoft.DesktopAppInstaller_1.22.10861.0_x64__8wekyb3d8bbwe" %+ rem WinGet
            gosub AddFolderToPathEndOnlyIfItExists "C:\Program Files\WindowsApps\Microsoft.DesktopAppInstaller_1.22.11132.0_x64__8wekyb3d8bbwe" %+ rem WinGet

::::: MOST IMPORTANT STUFF: machinename-specific, then OS-specific BATs, then main/normal/non-specific -- for both BATs and UTILs:
	gosub AddFolderToPathBegOnlyIfItExists C:\UTIL\
	gosub AddFolderToPathBegOnlyIfItExists C:\UTIL\%OS%
	gosub AddFolderToPathBegOnlyIfItExists C:\UTIL\%MACHINENAME%
	gosub AddFolderToPathBegOnlyIfItExists C:\BAT\
	gosub AddFolderToPathBegOnlyIfItExists C:\BAT\%OS%
	gosub AddFolderToPathBegOnlyIfItExists C:\BAT\%MACHINENAME%
	gosub AddFolderToPathBegOnlyIfItExists C:\BAT\beta

::::: WORK-MACHINE STUFF THAT PRECEDES OUR NORMAL PATH:
	rem if %@UPPER["%MACHINENAME"] eq "WORK" gosub AddFolderToPathBegOnlyIfItExists  %DROPBOX%\work\bat
	rem if %@UPPER["%MACHINENAME"] eq "WORK" gosub AddFolderToPathBegOnlyIfItExists  %DROPBOX%\work\bat\eAdjudication

::::: Now include the OS'es binaries at the end of the path:
	:95/98/ME era:
		if "%OS%" == "95" .or. "%OS%" == "98" .or. "%OS%" == "ME" gosub AddFolderToPathEndOnlyIfItExists c:\windows\command
		if "%OS%" == "95" .or. "%OS%" == "98" .or. "%OS%" == "ME" gosub AddFolderToPathEndOnlyIfItExists c:\windows
		if "%OS%" == "95" .or. "%OS%" == "98" .or. "%OS%" == "ME" gosub AddFolderToPathEndOnlyIfItExists c:\windows\system
		if "%OS%" == "95" .or. "%OS%" == "98" .or. "%OS%" == "ME" gosub AddFolderToPathEndOnlyIfItExists c:\4DOS

	:NT/2K era:
		if "%OS%" == "NT" .or. "%OS%" == "2K"                     gosub AddFolderToPathEndOnlyIfItExists c:\winnt\system32
		if "%OS%" == "NT" .or. "%OS%" == "2K"                     gosub AddFolderToPathEndOnlyIfItExists c:\winnt
		if "%OS%" == "NT" .or. "%OS%" == "2K"                     gosub AddFolderToPathEndOnlyIfItExists c:\4NT

	:XP/VISTA/7 era:
		:if "%OS%" == "7"  .or. "%OS%" ==  "XP" .or. "%OS%" == "10"
        gosub AddFolderToPathEndOnlyIfItExists %SystemRoot%
        gosub AddFolderToPathEndOnlyIfItExists %SystemRoot%\system32
        gosub AddFolderToPathEndOnlyIfItExists %SystemRoot%\Wbem
        gosub AddFolderToPathEndOnlyIfItExists %SystemRoot%\WindowsPowerShell\v1.0\
        gosub AddFolderToPathEndOnlyIfItExists %SystemRoot%\System32\WindowsPowerShell\v1.0\
        gosub AddFolderToPathEndOnlyIfItExists %SystemRoot%\System32\OpenSSH
		if "%OS%" ==  "XP" gosub AddFolderToPathEndOnlyIfItExists c:\4NT
        gosub AddFolderToPathEndOnlyIfItExists c:\TCMD
        gosub AddFolderToPathEndOnlyIfItExists c:\TCC

	:10/11 era:
        gosub AddFolderToPathEndOnlyIfItExists %SystemRoot%\system32\Wbem


goto :END

	::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
		:::::::::::::::::::::::::::::::::::::::::::::::::::
		:AddFolderToPathBegOnlyIfItExists [folder]
			if isdir %folder% PATH=%folder%;%PATH
		return
		:::::::::::::::::::::::::::::::::::::::::::::::::::
		:::::::::::::::::::::::::::::::::::::::::::::::::::
		:AddFolderToPathEndOnlyIfItExists [folder]
            :echo if isdir %folder% PATH=%PATH;%folder%
			      if isdir %folder% PATH=%PATH;%folder%
		return
		:::::::::::::::::::::::::::::::::::::::::::::::::::
	::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

:END

REM one last cleanup - no blank path entries - ";;" must become ";"
    PATH=%@REPLACE[;;,;,%PATH]

REM * Save our dynamically-generated path as a .cmd file that can be run in other commandlines such as PowerShell & Anaconda
    path >c:\bat\setpath.cmd



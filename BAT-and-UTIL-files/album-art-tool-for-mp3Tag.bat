@echo off

	gosub process %1
	gosub process %2
	gosub process %3
	gosub process %4
	gosub process %5
	gosub process %6
	gosub process %7
	gosub process %8
	gosub process %9

goto :END


	::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
	:process [artDirty]
		if "%artDirty" eq "" .or. "%artDirty" eq "dashbefore" goto return_now

			:OLD:
			:set         artClean=%@EXECSTR[get-meat-from-mp3-filename.pl         %artDirty%]
			:set  dashBeforeValue=%@EXECSTR[get-before-dash-part-from-filename.pl %artDirty%]
			:NEW:
			 set PROCESSBEFOREDASHONLY=0
			 set         artClean=%@EXECSTR[get-meat-from-mp3-filename.pl %artDirty%]
			 set PROCESSBEFOREDASHONLY=1
			 set  dashBeforeValue=%@EXECSTR[get-meat-from-mp3-filename.pl %artDirty%]
			 set PROCESSBEFOREDASHONLY=0

			 set        artCleanNoSpaces=%@REPLACE[ ,+,%artClean%]
			 set dashBeforeValueNoSpaces=%@REPLACE[ ,+,%dashBeforeValue%]

			                                                  call album-art        %artCleanNoSpaces%
			if "%DASHBEFORE%" eq "1" .or "%3" eq "dashbefore" call album-art %dashBeforeValueNoSpaces%
			delay /m 000
			windowhide /top Mp3tag*
			:meh: keystack alt-tab %+ echo - Alt-Tab! 

			echo * Full parameters:               %*
			echo * Album art current: dirty:      %artDirty%
			echo * Album art clean, yes spaces:   %artClean%
			echo * Album art clean, no  spaces:   %artCleanNoSpaces%
			echo * Dash Before option:            %dashBefore%
			echo * Dash Before value, no  spaces: %dashBeforeValue%
			echo * Dash Before value, yes spaces: %dashBeforeValueNoSpaces%
            call divider


		:return_now		
	 return
	::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

:END

unset /q DASHBEFORE

if "%EXITAFTER%" eq "0" goto :NoExit
        :pause
        call wait 150
        exit
:NoExit


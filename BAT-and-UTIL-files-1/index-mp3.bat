@on break cancel
@Echo OFF

:DESCRIPTION: This a wrapper to launch the REAL indexer (index-mp3-helper.bat) in a separate window/pane

set                                INDEXER=c:\bat\index-mp3-helper.bat
call validate-environment-variable INDEXER
call validate-in-path              perl index-mp3-helper 

goto %OS

    :Default
	:Windows_NT
    :10
    :11
        call validate-in-path      splv
		call splv                 %INDEXER%         %*
		goto :END

    :7
		start    c:\TCMD\TCC.EXE  %INDEXER%         %*
		goto :END


	:NT
	:2K
	:XP
		start    c:\4NT\4NT.EXE   %INDEXER%         %*
		goto :END

	:98
	:ME
		start /m c:\4dos\4dos.com c:\4dos %INDEXER% %*
		goto :END

:END
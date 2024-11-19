@echo off
 on break cancel

	set DASHBEFORE=1
	call album-art-tool-for-mp3Tag %*

unset /q DASHBEFORE

@Echo OFF

:DESCRIPTION: To be run after a fresh Windows install, to automatically install useful programs

:REQUIRES: validate-in-path.bat, winget (may have to install from app store)

REM call list-all-available-winget-programs.bat
REM      ^^ done via:    winget search --query ""


call validate-in-path winget

call install-common-programs-with-winget-helper.cmd

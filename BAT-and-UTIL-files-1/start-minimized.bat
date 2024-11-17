@Echo OFF

call validate-in-path hstart64

rem this was great for restart-winamp use of resarting winamp elevated
     rem %UTIL%\hstart64 /MIN /d="%_CWD" %@SFN["%1"]

rem but we'll just have to take repsonsibility for filename shortening elsewhere	 
	 hstart64 /MIN /d="%_CWD" %*



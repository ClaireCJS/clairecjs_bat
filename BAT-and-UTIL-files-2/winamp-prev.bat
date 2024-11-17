@Echo OFF

 call setTmpMusicServer.bat %*
 call wget32 --tries=3 --wait=1 --http-user=%WAWI_USER% --http-passwd=%WAWI_PASS% --spider http://%TMPMUSICSERVER/prev



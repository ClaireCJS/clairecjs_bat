@Echo OFF
@on break cancel

 call wget32 --tries=3 --wait=1 --http-user=%WAWI_USER% --http-passwd=%WAWI_PASS% --spider http://%TMPMUSICSERVER%/next



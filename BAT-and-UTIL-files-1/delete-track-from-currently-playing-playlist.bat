@Echo OFF


rem CHECK IF A TRACK NUMBER WAS PASSED TO US. IF SO, SAVE IT FOR LATER:
        if "%1"=="" goto :ERROR_NoTrack
        set TRACK=%1


rem FAKE-CLICK THE WINAMP WAWI WEB INTERFACE DELETE BUTTON FOR THE ABOVE-SPECIFIED TRACK:
        :call wget32    --tries=1 --wait=1 --http-user=claire --http-passwd=oh --spider http://%TMPMUSICSERVER%%ZZZZZZZ%/delete?track=%TRACK%
         call wget32                                                                    http://claire:oh@%TMPMUSICSERVER/delete?track=%TRACK%

goto :END


        :ERROR_NoTrack
                call FATALERROR "Track number not given!"
        goto :END


:END
        set LAST_TRACK_DELETED=%TRACK%
        unset /q TRACK
	
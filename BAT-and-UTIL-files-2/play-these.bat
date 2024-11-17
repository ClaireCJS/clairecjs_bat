@Echo OFF


call validate-environment-variables FILEMASK_VIDEO FILEMASK_AUDIO
call validate-in-path play-m3u-with-VLC 
rem not currently used as we changed our mind and started using VLCX for audio to, so as not to distrub winamp's playlist: 
rem             call validate-in-path play-m3u-with-winamp


set  DEFAULT_PLAYLIST=these.m3u
if %@FILES[%FILEMASK_VIDEO%] ge %@FILES[%FILEMASK_AUDIO%] goto :Video
                                                          goto :Audio

        :Video
            call important "Treating as video"
            dir/b/s %FILEMASK_VIDEO% >:u8 %DEFAULT_PLAYLIST%
            if "%1" ne "" ((dir/b/s %FILEMASK_VIDEO% |:u8 grep -i %* )>:u8  %DEFAULT_PLAYLIST%)
        goto :Play

        :Audio
            call important "Treating as audio"
            dir/b/s %FILEMASK_AUDIO% >:u8 %DEFAULT_PLAYLIST%
            if "%1" ne "" ((dir/b/s %FILEMASK_AUDIO% |:u8 grep -i %* )>:u8 %DEFAULT_PLAYLIST%)
        goto :Play

        :Play
            call play-m3u-with-VLC %DEFAULT_PLAYLIST%
        goto :END


:END
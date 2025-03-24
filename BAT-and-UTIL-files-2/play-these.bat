@Echo OFF
@on break cancel


rem Validate environment (once):
        iff "1" != "%validated_play_these_bat%" then
                call validate-environment-variable FILEMASK_VIDEO skip_validation_existence
                call validate-environment-variable FILEMASK_AUDIO skip_validation_existence
                call validate-in-path              play-m3u-with-VLC 
                rem  validate-in-path              play-m3u-with-winamp %+ rem not currently used as we changed our mind and started using VLC for audio too, so as not to distrub winamp's playlist: 
                set  validated_play_these_bat=1
        endiff


rem Determine whether we’re using audio or video logic:
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


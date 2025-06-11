@Echo OFF
@on break cancel

rem Validate environment:
        call validate-environment-variables MP3
        call validate-in-path               mp3 thorough sweep-randomly gkh get-karaoke

rem Go to the folder you want to work:
        call mp3
        call thorough off
        if isdir non-music *cd non-music


rem Confirm
        echo * About to go through %_CWP folder encoding without thorough mode on
        pause "Press any key to do it!"

rem Actually do it:
        call sweep-randomly "call gkh" force

@Echo OFF
@on break cancel


pushd

    call programfilesx86.bat
    cd   last.fm
    call wrapper *start "" "Last.fm Scrobbler.exe"

popd



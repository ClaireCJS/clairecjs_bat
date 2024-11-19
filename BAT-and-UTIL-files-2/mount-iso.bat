@Echo OFF
@on break cancel

rem To mount an ISO in windows 10, you just open it with explorer!
rem So just validate that things are what we seem, then open it!

rem Get parameter, make sure it exists, and is an ISO file:
    set ISO=%@UNQUOTE[%1]
    call validate-environment-variable   ISO
    call validate-file-extension "%ISO%" ISO

rem Mount it using explorer
    explorer "%ISO%"

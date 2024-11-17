@Echo OFF

:DESCRIPTION: Loads files into text editor with a 1 second delay. Useful for automation of loading files into text editors that hang if you throw 50 file-load command lines at them at once.


iff 1 ne %EDITOR_SLOW_VALIDATED% then
        call checkeditor
        set EDITOR_SLOW_VALIDATED=1
endiff

sleep 1
%EDITOR% %*

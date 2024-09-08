@Echo off

REM /SHA1 is slightly faster but potentially insecure
REM /Nj  isn't working right dammit

for /h /a:d /Nj %dir in (*.*) gosub DeDupeDir %dir

goto :END

    :DeDupeDir [%dir]        
        pushd
        *cd %dir
        echos %@RANDFG[]
        rem echo CWD=%_CWD dir=%dir% 
        call delete-duplicate-files-including-subfolder-duplicates.bat
        *cd ..
        popd
    return

:END


@Echo OFF


call AskYN "Run %italics_on%Tag & Rename v3.9.11%italics_off% [on the files in this folder]?" yes 


iff "%answer" eq "Y" then
        pushd .
        call validate-in-path util2 bthis                                                    
        call bthis
        call util2
        if not isdir TagRename-3.9.11 (call error "TagRename-3.9.11 doesn’t exist in %_CWD") 
        cd    TagRename-3.9.11
        
        if not exist TagRename.exe    (call error "TagRename.exe    doesn’t exist in %_CWD") 
        start TagRename.exe
        popd
endiff        



@Echo OFF

call validate-environment-variables NEWCL 
call validate-in-path               newcl thorough sweep-randomly gkh get-karaoke

rem Go to the folder you want to work:
        call newcl
        call thorough
        if isdir music *cd music
        rem cd MISC


call sweep-randomly "call gkh" force

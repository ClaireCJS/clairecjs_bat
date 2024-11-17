@Echo on 
if "%NO7%" ne "1" (call x10 a7 on )
if "%NO6%" ne "1" (call x10 a6 on  %+ set TVLIGHTING=1) 
                   call x10 a1 on 
                   call x10 a2 on 
                   call x10 b1 on 

::::: Also turn ambilight on 
    call aoff

call x10 a15 on 
call x10 a16 on 
call x10 a14 on 
call x10 a12 on 
call x10 a13 on 

call x10 a10 on 
call x10 a11 on 

call x10 a3 on 
call x10 a4 on 
call x10 a5 on 
call x10 a8 on 
call x10 a9 on 

::::: Stubborn light:
call x10 b1 on 

::::: Living room:
call x10 b7 on

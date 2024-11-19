@on break cancel
@Echo OFF
if "%NO7%" ne  "1" (call x10 a7 off)
if "%NO6%" eq  "1" (goto :No6)
if  "NO6"  eq "%1" (goto :No6)
    (call x10 a6 off %+ set TVLIGHTING=0) 
:No6
                   call x10 a1 off
                   call x10 a2 off
                   call x10 b1 off
                   call x10 b7 off

::::: Also turn ambilight off
    call aoff

::::: Turn off all the lights:
::::: (would be more elegant to use our environment variables):
    call x10 a15 off
    call x10 a16 off
    call x10 a14 off
    call x10 a12 off
    call x10 a13 off
    call x10 a10 off
    call x10 a11 off
    call x10 a3  off
    call x10 a4  off
    call x10 a5  off
    call x10 a8  off
    call x10 a9  off

::::: Stubborn lights:
    :call x10 b1 off
    :call x10 b7 off
    :call x10 a3 off
    :call x10 a4 off

@Echo Off
:1988:         Prompt=$P$G
:1990-2000ish::Prompt=$e[0;32;31m$l$e[0;1;31m$t$h$h$h$h$h$h$e[0;32;31m$g $e[0;33;32m$P$G$e[0;0;0m
:2005:         Prompt=$e[0;32;31m$l$e[0;1;31m$t$h$h$h$e[0;32;31m$g $e[0;33;32m$P$G$e[0;0;0m
:200x:         Prompt=$e[1;32;31m$l$e[0;1;31m$M$e[1;32;31m$g $e[1;32;32m$P$G$e[0;0;0m
:2015:

:: QUICK-REF: 1=BOLD;30=Black,31=Red,32=Green,33=Yellow,34=Blue,35=Purp,36=Cyan,37=White

:: I have this weird variation where I do C:> instead of <C:> so I don't have the less-than-symbol before the path:
    set SUPPRESS_LESSTHAN_BEFORE_PATH=1

:: And also, I have my brackets in bold, same color, which is variant from commons:
    set PATH_COLOR_BRACKETS=1;32;32

:: And this!
    set ADD_THE_CPU_USAGE=1

:: Do it
    call prompt-common

:: Also reset the cursor:
    call cursor-Claire


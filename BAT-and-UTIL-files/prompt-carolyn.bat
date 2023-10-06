@Echo OFF
:::1990-2000ish:
:Prompt=$e[0;32;31m$l$e[0;1;31m$t$h$h$h$h$h$h$e[0;32;31m$g $e[0;33;32m$P$G$e[0;0;0m
:::2005: haha:
:Prompt=$e[0;32;31m$l$e[0;1;31m$t$h$h$h$e[0;32;31m$g $e[0;33;32m$P$G$e[0;0;0m
:Prompt=$e[0;32;31m$l$e[0;1;31m$t$h$h$h$e[0;32;31m$g $e[1;32;32m$P$G$e[0;0;0m
:::Carolyn
:Prompt=$e[0;32;34m$l$e[0;1;34m$t$h$h$h$e[0;32;34m$g $e[1;32;35m$P$G$e[0;0;0m
:Prompt=$e[0;32;34m$l$e[0;1;36m$t$h$h$h$e[0;32;34m$g $e[1;32;35m$P$G$e[0;0;0m
:Prompt=$e[1;32;34m$l$e[0;1;36m$t$h$h$h$e[1;32;34m$g $e[1;32;35m$P$G$e[0;0;0m
:Prompt=$e[1;32;34m$l$e[0;1;36m$M$e[1;32;34m$g $e[1;32;35m$l$P$G$e[0;0;0m
:Prompt=$e[1;32;34m$l$e[0;1;36m$M$e[1;32;34m$g $e[0;32;35m$l$e[1;35m$P$e[0;35m$G$e[0;0;0m

:: QUICK-REF: 1=BOLD;30=Black,31=Red,32=Green,33=Yellow,34=Blue,35=Purp,36=Cyan,37=White
set PATH_COLOR_THE_PATH=1;35
set PATH_COLOR_BRACKETS=0;35
set TIME_COLOR_THE_TIME=0;1;36
set TIME_COLOR_BRACKETS=1;32;34
set CPU_USAGE_PERCENTS=1;30
set CPU_USAGE_BRACKETS=0;37
set ADD_THE_CPU_USAGE=1
call prompt-common

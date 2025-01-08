@Echo off
@on break cancel
if  not defined aliases  set aliases=c:\bat\alias.lst
if  not exist  %aliases% set aliases=c:\tcmd\alias.lst
if  not defined aliases  call fatal_error "aliases environment variable not defined to a valid location... “%aliases%”"
iff     defined aliases  then
        unalias *
        alias /r %aliases%
endiff

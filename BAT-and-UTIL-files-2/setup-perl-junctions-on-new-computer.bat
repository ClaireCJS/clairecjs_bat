@Echo OFF
@on break cancel

rem Strawberrry perl likes to install to c:\strawberry\, but I like to install it to c:\perl\, which is misleading compared to most peoples' structures,
rem so I create junctions to make cure \perl\bin, \perl\site, and \perl\lib are valid, even though it's really \perl\perl\bin, \perl\perl\ite, and \perl\perl\lib

rem Not the best decision, but I really want perl to be in C:\PERL, not c:\strawberry, which isn't as easy to know that it's perl from the folder name.

SET OUR_BASE=c:\perl\

call validate-environment-variable OUR_BASE
call validate-in-path              junction

junction c:\perl\site c:\perl\perl\site
junction c:\perl\bin  c:\perl\perl\bin
junction c:\perl\lib  c:\perl\perl\lib




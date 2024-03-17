@echo off
call set-tmpfile
(type clip: | call sort %*) >:u8      %tmpfile%
 type         %tmpfile%     >:u8clip:
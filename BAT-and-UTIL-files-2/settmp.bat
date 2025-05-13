@echo OFF
@on break cancel
call warning "DEPRECATED: Please use set-Tmp-File to create %%TMPFILE%% instead!! [pbatchname=%_PBATCHNAME]"
pause
SET TMP="%@UNIQUE[%TEMP]-%*"

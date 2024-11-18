@echo OFF
call warning "DEPRECATED: Please use set-Tmp-File to create %%TMPFILE%% instead!!"
pause
SET TMP="%@UNIQUE[%TEMP]-%*"

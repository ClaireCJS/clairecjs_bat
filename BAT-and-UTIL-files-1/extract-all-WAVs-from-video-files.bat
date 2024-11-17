@Echo off

call validate-environment-variable FILEMASK_VIDEO

for %%au in (%FILEMASK_VIDEO%) (if not exist "%@NAME[%au].wav" call extract-wav "%au" "%@NAME[%au].wav")



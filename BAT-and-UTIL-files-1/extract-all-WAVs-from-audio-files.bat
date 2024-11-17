@Echo off

call validate-environment-variable FILEMASK_AUDIO

for %%au in (%FILEMASK_AUDIO%) (if not exist "%@NAME[%au].wav" call extract-wav "%au" "%@NAME[%au].wav")



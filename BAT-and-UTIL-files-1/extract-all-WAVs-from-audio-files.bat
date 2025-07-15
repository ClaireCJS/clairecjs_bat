@on break cancel
@Echo off

if not defined FILEMASK_AUDIO  call validate-environment-variable FILEMASK_AUDIO skip_validation_existence

for %%au in (%FILEMASK_AUDIO%) (if not exist "%@NAME[%au].wav" call extract-wav "%au" "%@NAME[%au].wav")



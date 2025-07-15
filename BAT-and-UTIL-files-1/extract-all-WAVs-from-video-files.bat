@on break cancel
@Echo off

if not defined FILEMASK_VIDEO call validate-environment-variable FILEMASK_VIDEO skip_validation_existence

for %%au in (%FILEMASK_VIDEO%) (if not exist "%@NAME[%au].wav" call extract-wav "%au" "%@NAME[%au].wav")



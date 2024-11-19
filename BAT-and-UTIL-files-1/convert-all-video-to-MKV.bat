@Echo off
 on break cancel

call validate-environment-variable FILEMASK_VIDEO

for %%our_temp_file in (%FILEMASK_VIDEO%) (
     call convert-to-MKV "%our_temp_file" "%@NAME[%our_temp_file].mkv"
     call deprecate      "%our_temp_file" 
)



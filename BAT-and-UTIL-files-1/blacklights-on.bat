@Echo OFF
 on break cancel

                          set OPT=on
if "%@UPPER[%1]" eq "OFF" set OPT=off

call validate-environment-variable X10_LIGHTS_BLACKLIGHT

for %%x in (%X10_LIGHTS_BLACKLIGHT%) @call x10 %x %OPT%


@Echo OFF
@on break cancel

if not defined ANSI_UNLOCK_MARGINS call validate-environment-variable ANSI_UNLOCK_MARGINS

echos %ANSI_UNLOCK_MARGINS%

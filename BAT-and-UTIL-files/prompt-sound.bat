@Echo off

if "%1" eq "" (set PROMPT_VOICE_MESSAGE=Input requested)
if "%1" ne "" (set PROMPT_VOICE_MESSAGE=%1)

call beep 450 3 
call beep 550 2 
call beep 675 2 
call beep 550 3
call speak %PROMPT_VOICE_MESSAGE%

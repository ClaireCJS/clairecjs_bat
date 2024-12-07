@Echo off 
on break cancel

iff "%1" eq "" then
        echo Must provide a 1ˢᵗ argument character that you want to dance!
        echo And an optional 2ⁿᵈ argument for how many times to do the dance!
endiff

set our_character=%1
set count_to=
if "%1" ne "" (set count_to=%2)


set clear=echos %@ANSI_MOVE_TO_ROW[1]%@ANSI_MOVE_TO_COL[1]

*cls

set delay=200
echos %ansi_cursor_invisible%

set count=0

:loop
set count=%@EVAL[%count+1]

%CLEAR%
echo %big_top%%our_character%%italics_on% %our_character%%italics_off% %big_top%%our_character%%italics_on% %our_character%%italics_off%
echo %big_bot%%our_character%%italics_on% %our_character%%italics_off% %big_bot%%our_character%%italics_off% %our_character%%italics_off%
echo %big_top%%italics_on%%our_character% %italics_off%%our_character% %big_top%%italics_off%%our_character% %italics_off%%our_character%
echo %big_bot%%italics_on%%our_character% %italics_off%%our_character% %big_bot%%italics_on%%our_character% %italics_off%%our_character%
delay /m %DELAY%
%CLEAR%
echo %big_top%%italics_on%%our_character% %italics_off%%our_character% %big_top%%italics_off%%our_character% %italics_off%%our_character% 
echo %big_bot%%italics_on%%our_character% %italics_off%%our_character% %big_bot%%italics_on%%our_character% %italics_off%%our_character%  
echo %big_top%%our_character%%italics_on% %our_character%%italics_off% %big_top%%our_character%%italics_on% %our_character%%italics_off%                    
echo %big_bot%%our_character%%italics_on% %our_character%%italics_off% %big_bot%%our_character%%italics_off% %our_character%%italics_off%                    
delay /m %DELAY%

if defined count_to .and. %count_to eq %count (goto :end)


goto :loop


:end


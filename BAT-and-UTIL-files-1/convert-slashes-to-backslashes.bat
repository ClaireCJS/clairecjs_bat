@Echo off
if "%1" ne "" (call error "sorry, %0 is only meant for piping to, not for parameters")
call validate-in-path sed
sed 's/\//\\\/ig'

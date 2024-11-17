@Echo off

:DESCRIPTION: To combine md/mkdir and cd/chdir into one command, since we often change into folders we just made.
:DESCRIPTION: BONUS: can say "mcd now" to make (and change into) a folder of the current second (YYYYMMDDHHMMSS)



if "%@UPPER[%1]" eq "NOW" (call mcdnow %& %+ goto :END)  

if     isdir %1 (call warning "folder '%1' %blink_on%already exists%blink_off%!'")
if not isdir %1 (*md %1)
                  cd %1


:END


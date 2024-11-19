@Echo OFF
 on break cancel

cls
call warning "This is untested but might just work"
pause

echo.
echo.
echo.
call less_important "FYI, what it will do, is this:"
for %d in (%[drives_%machinename%]) echo net share %[mapping_%d]=%[%[%[%[%d]REAL]]]:\ /GRANT:Everyone,FULL
pause

echo.
echo.
echo.
call less_important "Doing it now!"
for %d in (%[drives_%machinename%]) net share %[mapping_%d]=%[%[%[%[%d]REAL]]]:\ /GRANT:Everyone,FULL


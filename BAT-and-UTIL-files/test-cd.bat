@Echo on

mcd test-cd

repeat 100 call make-zero-byte-file-named %_repeat

echo This is a test file            >clear
echo This is a test file >testdotjpg_large.jpg_large 
echo This is a test file     >testdotjpg!d.jpg!d     

cd test-cd

*del 2*

cd ..

pause

dir test-cd

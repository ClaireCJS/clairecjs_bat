@Echo OFF


set FILE=%@UNQUOTE["%1"]


echo call get-lyrics "%FILE%" quick_lrc %2$
pause
call get-lyrics "%FILE%" quick_lrc %2$


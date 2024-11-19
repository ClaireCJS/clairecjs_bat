@Echo OFF
 on break cancel
set msg=%@unquote[%*]
echo %BIG_TOP%%@cursive[%msg%]%EOL%
echo %BIG_BOT%%@cursive[%msg%]%EOL%

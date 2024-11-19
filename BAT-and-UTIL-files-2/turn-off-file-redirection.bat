@Echo OFF
@on break cancel

setdos /x-6


rem The features are:
rem 
rem 1 All alias expansion 
rem 2 Nested alias expansion only 
rem 3 All variable expansion (includes environment variables, batch file parameters, variable function evaluation, and alias parameters) 
rem 4 Nested variable expansion only  
rem 5 Multiple commands, conditional commands, and piping (affects the command separator, ||, &&, |, and |&) 
rem 6 Redirection (affects < , >, >&, >&>, etc.) 
rem 7 Quoting (affects back-quotes [`] and double quotes ["]) and square brackets) 
rem 8 Escape character 
rem 9 Include lists 
rem A User-defined functions 

:END
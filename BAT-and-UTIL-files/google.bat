@Echo off
unset /q QUERY
for %tt in (%*) set QUERY=%QUERY+%tt
http://www.google.com/search?q=%QUERY%


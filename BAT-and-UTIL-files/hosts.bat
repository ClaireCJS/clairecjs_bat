@Echo OFF
call checkeditor
"%SystemRoot%\system32\drivers\etc\"
attrib -rs hosts

call important "You want to copy the hosts in hosts-supplimental.txt into the official hosts file"
pause
%EDITOR% "%bat%\hosts-supplimental.txt"
%EDITOR% "%SystemRoot%\system32\drivers\etc\hosts"

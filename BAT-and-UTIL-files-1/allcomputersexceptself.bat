@Echo off
 on break cancel

set  ALL_COMPUTERS_EXCEPT_SELF=1
call allcomputers %*
set  ALL_COMPUTERS_EXCEPT_SELF=0


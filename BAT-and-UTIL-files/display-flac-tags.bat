@Echo OFF

set EXCEPT_BLOCK_TYPE=PICTURE,PADDING,SEEKTABLE

%COLOR_ADVICE% %+ echos * Block types of %EXCEPT_BLOCK_TYPE% will not be displayed.
%COLOR_NORMAL% %+ echo.

metaflac  --list  --except-block-type=%EXCEPT_BLOCK_TYPE%   %*


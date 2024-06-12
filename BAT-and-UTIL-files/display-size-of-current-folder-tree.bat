@Echo OFF

set SIZE=%@FILESIZE[.,bc,/s]
set KILO=%@FLOOR[%@EVAL[%SIZE% / 1024]]
set MEGA=%@FLOOR[%@EVAL[%SIZE% / 1024 / 1024]]
set GIGA=%@FORMATN[0.1,%@EVAL[%SIZE% / 1024 / 1024 / 1024]]
set TERA=%@FORMATN[0.1,%@EVAL[%SIZE% / 1024 / 1024 / 1024 / 1024]]

call less_important "%GIGA%%faint_on%G%faint_off%%ansi_color_less_important%  (%size% bytes)  %faint_on%in%faint_off%  %italics_on%%_CWP%%italics_off%"

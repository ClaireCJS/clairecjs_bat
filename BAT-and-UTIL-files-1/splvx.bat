@Echo OFF
@on break cancel

set EXIT_AFTER_SPLIT_IS_RUN=1
call splv %*
set EXIT_AFTER_SPLIT_IS_RUN=0


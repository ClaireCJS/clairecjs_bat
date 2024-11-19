@Echo off
@on break cancel

set           reset=%bat%\reset.ansi
if not exist %reset% (call fatal_error "file '%reset%' does not exist")
type         %reset%
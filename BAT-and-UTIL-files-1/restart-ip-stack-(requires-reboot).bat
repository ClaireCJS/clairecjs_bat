@echo OFF
@on break cancel
call warning "This will have no effect until rebooting"
call warning "About to restart tcp ip stack"
call pause-for-x-seconds 60
netsh int ip reset
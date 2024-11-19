@echo off
@on break cancel

%color_warning%
    echo wait this doesn't do anything. well it does. but you have to reboot before it happens.
    echo so it's kinda stupid.... you may want to abort...

%color_normal%
    pause
    pause
    pause
    pause
    pause

%color_run%
    call restart-ip-stack %*

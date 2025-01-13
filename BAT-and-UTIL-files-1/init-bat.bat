@rem Set BTM mode for loading whole BAT into memory and allowing us to EDIT our BATs without messing up their execution:
        @loadbtm on

@rem Turn off echo'ing:
        @Echo OFF

rem Make sure Ctrl-Break actually does something:
        on break cancel 
 
 rem Restore defaults (redundant, but feels safer), Remove command separator parsing, 
 rem         Set the command separator,        then Re-enable command separator parsing:
        setdos /x0                                                     
        setdos /x-5                                                    
        setdos /c%DEFAULT_COMMAND_SEPARATOR_CHARACTER%                 
        setdos /x0

rem Unlock any ANSI-locked rows or columns:
        echos %ANSI_UNLOCK_MARGINS%%@ANSI_UNLOCK_ROWS[]
        rem crates nonzero screen output: call unlock
 

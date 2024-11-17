@Echo OFF


echo. %+ echo. %+ echo. %+ echo. %+ echo. %+ echo. %+ echo. %+ echo. %+ echo.  
echo. %+ echo. %+ echo. %+ echo. %+ echo. %+ echo. %+ echo. %+ echo. %+ echo.  

 




echo. %+ echo. %+ color bright green on bright blue %+ echo ****** HARDWARE STATUS ****** %+ color white on black
    echo _acstatus       = AC line status                       = %_acstatus       
    echo _alt            = Alt key depressed                    = %_alt            
    echo _battery        = Battery status                       = %_battery        
    echo _batterylife    = Remaining battery life, seconds      = %_batterylife    
    echo _batterypercent = Remaining battery life, percent      = %_batterypercent 
    echo _capslock       = CapsLock on: 1, else 0               = %_capslock       
    echo _cpu            = CPU type                             = %_cpu            
    echo _cpuusage       = CPU time usage (percent)             = %_cpuusage       
    echo _ctrl           = Ctrl key depressed: 1, else 0        = %_ctrl           
    echo _kbhit          = keyboard input character is waiting  = %_kbhit          
    echo _lalt           = left Alt key depressed: 1, else 0    = %_lalt           
    echo _lctrl          = left Ctrl key depressed: 1, else 0   = %_lctrl          
    echo _lshift         = left Shift key depressed: 1, else 0  = %_lshift         
    echo _numlock        = NumLock on:r 1, else 0               = %_numlock        
    echo _ralt           = right Alt key depressed: 1, else 0   = %_ralt           
    echo _rctrl          = right Ctrl key depressed: 1, else 0  = %_rctrl          
    echo _rshift         = right Shift key depressed: 1, else 0 = %_rshift         
    echo _scrolllock     = ScrollLock on: 1, else 0             = %_scrolllock     
    echo _shift          = Shift key depressed: 1, else 0       = %_shift          
 


echo. %+ echo. %+ color bright green on bright blue %+ echo ****** OPERATING SYSTEM AND SOFTWARE STATUS ****** %+ color white on black
    echo !            = Last argument of previous command              = %!            
    echo _admin       = 1 if administrator; else 0                     = %_admin       
    echo _ansi        = ANSI X3.64 status                              = %_ansi        
    echo _boot        = Boot drive letter, without a colon             = %_boot        
    echo _codepage    = Current code page number                       = %_codepage    
    echo _country     = Current country code                           = %_country     
    echo _dos         = Operating system type                          = %_dos         
    echo _dosver      = Operating system version                       = %_dosver      
    echo _elevated    = 1 if the TCC process is elevated               = %_elevated    
    echo _host        = Host name of local computer.                   = %_host        
    echo _hwprofile   = Windows hardware profile if defined            = %_hwprofile   
    echo _hyperv      = Running inside Hyper-V: 1; else 0              = %_hyperv      
    echo _idleticks   = Milliseconds since last user input             = %_idleticks   
    echo _ip          = IP address(es) of local computer.              = %_ip          
    echo _ipadapter   = Index of the current adapter                   = %_ipadapter   
    echo _ipadapters  = Number of adapters in the system               = %_ipadapters  
    echo _iparpproxy  = 1 if the local computer is acting as ARP proxy = %_iparpproxy  
    echo _ipdns       = 1 if DNS is enabled on the local computer      = %_ipdns       
    echo _ipdnsserver = The default DNS server for the local computer  = %_ipdnsserver 
    echo _iprouting   = Returns 1 if routing is enabled                = %_iprouting   
    echo _osbuild     = Windows build number                           = %_osbuild     
    echo _serialports = Display available serial ports (COM1 - COMn)   = %_serialports 
    echo _tctab       = Running inside Take Command: 1; else 0         = %_tctab       
    echo _virtualbox  = Running inside VirtualBox: 1; else 0           = %_virtualbox  
    echo _virtualpc   = Running inside VirtualPC: 1; else 0            = %_virtualpc   
    echo _vmware      = Running inside VMWare: 1; else 0               = %_vmware      
    echo _windir      = Windows directory pathname                     = %_windir      
    echo _winfgwindow = Title of foreground window.                    = %_winfgwindow 
    echo _winname     = Name of local computer                         = %_winname     
    echo _winsysdir   = Windows system directory pathname              = %_winsysdir   
    echo _winticks    = Milliseconds since Windows was started         = %_winticks    
    echo _wintitle    = Current window title                           = %_wintitle    
    echo _winuser     = Name of current user.                          = %_winuser     
    echo _winver      = Windows version number                         = %_winver      
    echo _wow64       = Running in Windows x64: 1; else 0              = %_wow64       
    echo _wow64dir    = System WOW64 directory                         = %_wow64dir    
    echo _x64         = 1 if TCC is the x64 (64-bit) version           = %_x64         
    echo _xen         = Running inside Xen: 1; else 0                  = %_xen         
 


echo. %+ echo. %+ color bright green on bright blue %+ echo ****** TCC STATUS ****** %+ color white on black
    echo _4ver        = TCC version                                    = %_4ver        
    echo _batch       = Batch nesting level                            = %_batch       
    echo _batchline   = Line number in current batch file.             = %_batchline   
    echo _batchname   = Full path and filename of current batch file   = %_batchname   
    echo _batchtype   = Type of the current batch file                 = %_batchtype   
    echo _bdebugger   = Batch debugger active: 1, else 0               = %_bdebugger   
    echo _build       = Build number                                   = %_build       
    echo _childpid    = Process ID of most recent child process        = %_childpid    
    echo _cmdline     = Current command line                           = %_cmdline     
    echo _cmdproc     = Command processor name                         = %_cmdproc     
    echo _cmdspec     = Full pathname of command processor             = %_cmdspec     
    echo _consoleb    = Handle to the active console screen buffer     = %_consoleb    
    echo _detachpid   = Process ID of most recent detached process     = %_detachpid   
    echo _dname       = Name of the description file.                  = %_dname       
    echo _echo        = Echo status                                    = %_echo        
    echo _editmode    = Default insert mode: 1; else 0                 = %_editmode    
    echo _execarray   = Array elements assigned by the last @EXECARRAY = %_execarray   
    echo _exit        = TCC exit code                                  = %_exit        
    echo _expansion   = Current expansion mode (SETDOS /X)             = %_expansion   
    echo _filearray   = Array elements assigned by the last @FILEARRAY = %_filearray   
    echo _hlogfile    = Current history log file name                  = %_hlogfile    
    echo _ide         = In the IDE / debugger: 1, else 0               = %_ide         
    echo _iftp        = IFTP session active: 1, else 0                 = %_iftp        
    echo _iftps       = IFTPS session active: 1, else 0                = %_iftps       
    echo _isftp       = ISFTP (SSH) session active: 1, else 0          = %_isftp       
    echo _ininame     = Full pathname of the current INI file          = %_ininame     
    echo _insert      = input editor state (0=overstrike, 1=insert)    = %_insert      
    echo _logfile     = Current log file name                          = %_logfile     
    echo _parent      = Name of the parent process                     = %_parent      
    echo _pid         = The TCC process ID (numeric)                   = %_pid         
    echo _pipe        = Current process is running in a pipe: 1/0      = %_pipe        
    echo _ppid        = Process ID of parent process                   = %_ppid        
    echo _registered  = Registered user name                           = %_registered  
    echo _selected    = Selected text in current tab window            = %_selected    
    echo _service     = TCC is a service: 1, else 0                    = %_service     
    echo _shell       = Shell level                                    = %_shell       
    echo _shortcut    = Pathname of shortcut that started this process = %_shortcut    
    echo _shralias    = SHRALIAS is loaded: 1, else 0                  = %_shralias    
    echo _startpath   = Startup directory of current shell.            = %_startpath   
    echo _startpid    = Process ID of most recent STARTed process      = %_startpid    
    echo _stdin       = STDIN redirected: 0, otherwise 1               = %_stdin       
    echo _stdout      = STDOUT redirected: 0, otherwise 1              = %_stdout      
    echo _stderr      = STDERR redirected: 0, otherwise 1              = %_stderr      
    echo _tccrun      = Time current TCC session has been running      = %_tccrun      
    echo _tccstart    = Time current TCC session was started           = %_tccstart    
    echo _tctabactive = TCC is the active Take Command tab: 1, else 0  = %_tctabactive 
    echo _tcexit      = Current value of TCEXIT.*                      = %_tcexit      
    echo _tcfilter    = Current filter in List view window             = %_tcfilter    
    echo _tcfolder    = Selected folder in Folders window              = %_tcfolder    
    echo _tclistview  = Selected entries in the List View window       = %_tclistview  
    echo _tcstart     = Current value of TCSTART.*                     = %_tcstart     
    echo _tctabs      = Current number of Take Command tab windows     = %_tctabs      
    echo _transient   = Current process is a transient shell?          = %_transient   
    echo _unicode     = TCC uses unicode for redirected output?        = %_unicode     
    echo _vermajor    = TCC major version                              = %_vermajor    
    echo _verminor    = TCC minor version                              = %_verminor    
    echo _version     = TCC version (major.minor format) (ie 18.0)     = %_version     
 



echo. %+ echo. %+ color bright green on bright blue %+ echo ****** SCREEN, COLOR, AND CURSOR ****** %+ color white on black
    echo _bg       = Background color at cursor position            = %_bg          
    echo _ci       = Current text cursor shape in insert mode       = %_ci          
    echo _co       = Current text cursor shape in overstrike mode   = %_co          
    echo _column   = Current cursor column                          = %_column      
    echo _columns  = Virtual screen width                           = %_columns     
    echo _fg       = Foreground color at cursor position            = %_fg          
    echo _monitors = Number of monitors                             = %_monitors    
    echo _row      = Current cursor row                             = %_row         
    echo _rows     = Screen height                                  = %_rows        
    echo _selected = Selected text in current tab window            = %_selected    
    echo _vxpixels = Virtual screen horizontal size                 = %_vxpixels    
    echo _vypixels = Virtual screen vertical size                   = %_vypixels    
    echo _xmouse   = Column of last mouse click                     = %_xmouse      
    echo _xpixels  = Physical screen horizontal size in pixels      = %_xpixels     
    echo _xwindow  = Width of Take Command or TCC window in pixels  = %_xwindow     
    echo _ymouse   = Row of last mouse click                        = %_ymouse      
    echo _ypixels  = Physical screen vertical size in pixels        = %_ypixels     
    echo _ywindow  = Height of Take Command or TCC window in pixels = %_ywindow     
 
echo. %+ echo. %+ color bright green on bright blue %+ echo ****** DRIVES AND DIRECTORIES ****** %+ color white on black
    echo _afswcell = OpenAFS workstation cell                    = %_afswcell   
    echo _cdroms   = List of CD-ROM drives                       = %_cdroms     
    echo _cwd      = Current drive and directory                 = %_cwd        
    echo _cwds     = Current drive and directory with trailing \ = %_cwds       
    echo _cwp      = Current directory                           = %_cwp        
    echo _cwps     = Current directory with trailing \           = %_cwps       
    echo _disk     = Current drive                               = %_disk       
    echo _drives   = List of all available drives                = %_drives     
    echo _dvds     = List of DVD drives                          = %_dvds       
    echo _hdrives  = List of hard (fixed) drives                 = %_hdrives    
    echo _lastdir  = Previous directory (from directory history) = %_lastdir    
    echo _lastdisk = Last valid drive                            = %_lastdisk   
    echo _openafs  = OpenAFS service installed: 1, else 0        = %_openafs    
    echo _ready    = List of ready (accessible) drives           = %_ready      
 
echo. %+ echo. %+ color bright green on bright blue %+ echo ****** DATES AND TIMES ****** %+ color white on black
    echo _date        = Current date                                     = %_date        
    echo _datetime    = Current date and time, yyyyMMddhhmmss            = %_datetime    
    echo _day         = Current day of the month                         = %_day         
    echo _dow         = Current day of the week, English, short          = %_dow         
    echo _dowf        = Current day of the week, English, full           = %_dowf        
    echo _dowi        = Current day of the week as an integer            = %_dowi        
    echo _doy         = Current day of the year                          = %_doy         
    echo _dst         = Daylight savings time: 1, else 0                 = %_dst         
    echo _hour        = Current hour                                     = %_hour        
    echo _idow        = Current day of the week, local language, short   = %_idow        
    echo _idowf       = Current day of the week, local language, full    = %_idowf       
    echo _imonth      = Current month name, local language, short        = %_imonth      
    echo _imonthf     = Current month name, local language, full         = %_imonthf     
    echo _isodate     = Current date in ISO 8601 format                  = %_isodate     
    echo _isodowi     = ISO 8601 numeric day of week                     = %_isodowi     
    echo _isowdate    = ISO 8601 current week date (yyyy-Www-d)          = %_isowdate    
    echo _isoweek     = ISO 8601 week of year                            = %_isoweek     
    echo _isowyear    = ISO 8601 week date year                          = %_isowyear    
    echo _minute      = Current minute                                   = %_minute      
    echo _month       = Current month of the year as integer             = %_month       
    echo _monthf      = Current month of the year, English, full         = %_monthf      
    echo _second      = Current second                                   = %_second      
    echo _stzn        = Name of time zone for standard time              = %_stzn        
    echo _stzo        = Offset in minutes from UTC for standard time     = %_stzo        
    echo _time        = Current time                                     = %_time        
    echo _tzn         = Name of current time zone                        = %_tzn         
    echo _tzo         = Offset in minutes from UTC for current time zone = %_tzo         
    echo _utctime     = Current UTC time                                 = %_utctime     
    echo _utcdate     = Current UTC date                                 = %_utcdate     
    echo _utcdatetime = Current UTC date and time                        = %_utcdatetime 
    echo _utchour     = Current UTC hour                                 = %_utchour     
    echo _utcisodate  = Current UTC date in ISO format                   = %_utcisodate  
    echo _utcminute   = Current UTC minute                               = %_utcminute   
    echo _utcsecond   = Current UTC second                               = %_utcsecond   
    echo _year        = Current year                                     = %_year        
 
echo. %+ echo. %+ color bright green on bright blue %+ echo ****** ERROR CODES ****** %+ color white on black
    echo ?          = Exit code, last external program = %?         
    echo _?         = Exit code, last internal command = %_?        
    echo errorlevel = Exit code, last external program = %errorlevel 
    echo _execstr   = Last @EXECSTR return code        = %_execstr  
    echo _ftperror  = Last FTP error code              = %_ftperror 
    echo _syserr    = Latest Windows error code        = %_syserr   
  
echo. %+ echo. %+ color bright green on bright blue %+ echo ****** v16 additions ****** %+ color white on black
    echo _ipadapter     = returns the index of the current adapter.                         = %_ipadapter     
    echo _ipadapters    = returns the number of adapters in the system.                     = %_ipadapters    
    echo _iparpproxy    = returns 1 if the local computer is acting as an ARP proxy.        = %_iparpproxy    
    echo _ipdns         = returns 1 if DNS is enabled for the local computer.               = %_ipdns         
    echo _ipdnsserver   = returns the default DNS server for the local computer.            = %_ipdnsserver   
    echo _iprouting     = returns 1 if routing is enabled on the local computer.            = %_iprouting     
    echo _isftp         = returns 1 if you have an SSH IFTP connection open                 = %_isftp         
    echo _7unzip_files  = returns the number of files extracted in the last 7UNZIP command. = %_7unzip_files  
    echo _7unzip_errors = returns the number of errors in the last 7UNZIP command.          = %_7unzip_errors 
    echo _7zip_files    = returns the number of files compressed in the last 7ZIP command.  = %_7zip_files    
    echo _7zip_errors   = returns the number of errors in the last 7ZIP command.            = %_7zip_errors   


echo. %+ echo. %+ color bright green on bright blue %+ echo ****** v17 additions ****** %+ color white on black
    echo _filearray = The number of array elements assigned by the last @FILEARRAY function.                            = %_FILEARRAY
    echo _tccrun    = The length of time the current TCC session has been running (as a FILETIME, in 100ns increments). = %_TCCRUN   
    echo _tccstart  = The time the current TCC session was started (as a FILETIME, in 100ns increments).                = %_TCCSTART 
 
echo. %+ echo. %+ color bright green on bright blue %+ echo ****** v18 additions ****** %+ color white on black
    echo _hyperv            = returns 1 if TCC is running in a Hyper-V VM.                                      = %_hyperv            
    echo _powerbattery      = returns the battery % (0-100) when the POWERMONITOR condition is triggered.       = %_powerbattery      
    echo _powerdisplay      = returns 0 if the primary monitor is powered off or 1 if it is on.                 = %_powerdisplay      
    echo _powerscheme       = returns the power scheme in use when the POWERMONITOR condition is triggered.     = %_powerscheme       
    echo _powersource       = returns the power source (AC or DC) when the POWERMONITOR condition is triggered. = %_powersource       
    echo _taskdialog_button = the button pressed to exit TASKDIALOG.                                            = %_taskdialog_button 
    echo _taskdialog_radio  = the selected radio button (if any) in TASKDIALOG.                                 = %_taskdialog_radio  
    echo _taskdialog_verify = returns 1 if the verify button was checked in TASKDIALOG.                         = %_taskdialog_verify 
    echo _xen               = returns 1 if TCC is running in a Xen VM.                                          = %_xen               
 
 echo. %+ echo. %+ color bright green on bright blue %+ echo ****** v19 additions ****** %+ color white on black
    call warning skipping bluetooth ones because they bring up a window that requires us to hit a key...
    goto :Skip_BT
        echo _btdevicecount  = The number of Bluetooth devices found.                  = %_btdevicecount  
        echo _btradiocount   = The number of Bluetooth radios installed on the system. = %_btradiocount   
        echo _btservicecount = The number of Bluetooth services present.               = %_btservicecount 
    :Skip_BT


 echo. %+ echo. %+ color bright green on bright blue %+ echo ****** v20 additions ****** %+ color white on black

    echo _dedup_errors   - The number of errors in a DEDUP command (usually access denied). - %_dedup_errors   
    echo _dedup_files    - The number of duplicated files found. - %_dedup_files    
    echo _differ_added   - The number of files in the target directory not found in the source directory in a DIFFER command. - %_differ_added   
    echo _differ_changed - The number of files in the target directory that have been changed (file date/time stamp) compared to the source directory. - %_differ_changed 
    echo _differ_deleted - The number of files in the source directory not found in the target directory in a DIFFER command. - %_differ_deleted 
    echo _differ_errors  - The number of errors in a DIFFER command (usually access denied when comparing hashes). - %_differ_errors  
    echo _foldertime     - The system time of the most recent FOLDERMONITOR update (hh:mm:ss.ms). - %_foldertime     

 

 echo. %+ echo. %+ color bright green on bright blue %+ echo ****** v21 additions ****** %+ color white on black
    echo _MSGBOX_CHECKBOX - if 1, the user has checked the optional MSGBOX checkbox. (See MSGBOX below) - %_MSGBOX_CHECKBOX 
    echo _TCCINSTANCES    - number of instances of TCC  (version 21 or later) currently running. -------- %_TCCINSTANCES 
    echo _TCMDINSTANCES   - number of instances of TCMD (version 21 or later) currently running. -------- %_TCMDINSTANCES 
    echo _USBS            - returns a space-delimited list of all of the USB drives. -------------------- %_USBS 

 
REM NONE echo. %+ echo. %+ color bright green on bright blue %+ echo ****** v22 additions ****** %+ color white on black
REM 404! https://jpsoft.com/help/whats-new-in-version-23.htm is a 404  echo. %+ echo. %+ color bright green on bright blue %+ echo ****** v23 additions ****** %+ color white on black
REM NONE echo. %+ echo. %+ color bright green on bright blue %+ echo ****** v24 additions ****** %+ color white on black
REM 404! https://jpsoft.com/help/whats-new-in-version-25.htm is a 404 echo. %+ echo. %+ color bright green on bright blue %+ echo ****** v25 additions ****** %+ color white on black
REM 404! https://jpsoft.com/help/whats-new-in-version-26.htm is a 404 echo. %+ echo. %+ color bright green on bright blue %+ echo ****** v26 additions ****** %+ color white on black
 echo. %+ echo. %+ color bright green on bright blue %+ echo ****** v27 additions ****** %+ color white on black
    echo _BATCHPATH  - Pathname of the current batch file (including the trailing \). - %_BATCHPATH 
    echo _IPDNSOTHER - A space-delimited list of other DNS servers configured for the host machine. (The primary server is returned by %_IPDNSSERVER.) - %_IPDNSOTHER 
 REM   %+ echo. %+ color bright green on bright blue %+ echo ****** v28 additions ****** %+ color white on black \__ no new vars 
 REM   %+ echo. %+ color bright green on bright blue %+ echo ****** v29 additions ****** %+ color white on black /   fr these ones
 echo. %+ echo. %+ color bright green on bright blue %+ echo ****** v30 additions ****** %+ color white on black
    echo _ipv6 = IPV6 Address = %_IPV6
 echo. %+ echo. %+ color bright green on bright blue %+ echo ****** v30 additions ****** %+ color white on black
    echo _PBATCHNAME = Parent batchfile name = %_PBATCHNAME
    echo _VOLUME     = volume (updated)      = %_volume

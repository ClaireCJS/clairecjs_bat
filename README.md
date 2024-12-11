# 🤓 The Clairevironment — Claire's personal script collection 🤓

## Plunge into the command-line lifestyle! 😂

## BAT files created for [JPsoft's TCC/TCMD command-line](http://www.JPSoft.com)... 🤓

### ...arguably the most sophisticated 64-bit command-line in existence, in constant development for over 35 years... 
### ...And this is the result of me using it for over 35 years...

This is basically a full layer of scripts built on top of TCC's functionality for 35 years, to add all kinds of functionality and improvement. Rich color, ANSI stylization, audio effects where appropriate, validators to prevent script brittleness, workflow management, repository validation, backups, maintenance, unix commands, all kinds of stuff that is hard for me to describe because I've been working on this environment for 35 years. There's at least 800 scripts in this repo, though a lot are oneliners that call others and it's really probably only 400 significant scripts.

After improving my environment for several decades, I decided to generalize it to see if other people could roll it out and use it, as well as to back up all my work and have something to show for it.



---------------------------------



# I would absolutely love feedback! 🤓

I would love to know how this works out for somebody who has never done it. Nobody outside of my own family has ever tried to use my environment. Such feedback is something I could use to further generalize my scripts to be more workable for other people. I can't really test the process on my own machines without wiping them 😅

---------------------------------


# INSTALLATION INSTRUCTIONS

The abridged instructions are: Install TCC, run *[clairevironment-install.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/clairevironment-install.bat)*, add TCC to Windows Terminal, run it and change the command separator character, and you're ready to run my environment!

But here are the proper instructions:



1. Run (Windows-R) ```PowerShell``` and type in the following 2 commands:```
        Set-ExecutionPolicy -ExecutionPolicy Bypass
	Add-AppxPackage -Path "https://aka.ms/getwinget"```
	The first command allows for better TCC<->PowerShell integration (particularly for my [display bluetooth battery levels](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/display-bluetooth-battery-levels.ps1) script)
	The second  command installs winget, which is used to automate most other installation.

1. Install TCC: 
    - The automatic way:  Simply run: ```winget install JPSoft.tcmd```
    - The manual way: Download TCC (Take Command command-line) from [http://www.jpsoft.com](http:///www.jpsoft.com) and install it to the NON-DEFAULT location of ```c:\TCMD\```. DON'T run it just yet.  
    - The worst way: ```url.exe -s -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:92.0) Gecko/20100101 Firefox/92.0" -O https://jpsoft.com/downloads/v33/tcmd.exe```
    
1. Browse to ```c:\TCMD\```, right-click ```tcc.exe```, go to the *Compatibility* tab, and select ```Run as administrator".

1. Open TCC (```c:\TCMD\tcc.exe```). Grab [clairevironment-install.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/clairevironment-install.bat), and run it inside of TCC.  Follow its instructions and pay close close close attention. You may have to abort it and fix things along the way. This part hasn't been tested.

1. Add TCC to Windows Terminal and Run it: 
    Open up *Windows Terminal*, hit Ctrl-, (yes, control-comma) to go into settings. Scroll to the bottom of the left pane and click *Add new profile*. You can duplicate the PowerShell profile or start a new one.  All you need to do is change the name to "TCC", the command line to ```c:\tcmd\tcc.exe```, the starting directory to ```c:\tcmd```, and *Run As Administrator* turned on. Go into ```Appearance``` and change the font to *Cascadia Code*, which has the proper [ligature rendering](https://github.com/microsoft/cascadia-code#font-features) that I sometimes take advantage of cosmetically.
    Now run it.
    A good test for if things worked is typing ```echo %PENTAGRAM%```. Do you see a pentagram character?  If not, you can always try copying my [windows terminal settings file](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/windows-terminal-settings.json-to-be-copied-into-WT-dir-at-own-risk.json) into your *Windows Terminal* folder.

1. At your freshly-run TCC command-line, type ```option```, and switch to the *"Advanced"* tab.  In the upper-left is a section called *"Special Characters"*.  Change the separator to "^" (the [caret character](https://en.wikipedia.org/wiki/Caret)). 
    This is actually a deviation from how most people do things, due to the isolation of learning this command-line in the 1980s and 1990s. It creates complications that I've mostly mitigated—but not completely. Any mitigations I missed will cause failures unless you do this.


# At this point, everything is installed!!! 

### Post-Boot Script configuration: like ‘autoexec.bat’):

1. To have a startup-upon-reboot script akin to the ```autoexec.bat``` of yore, look at [autoexec-common.btm](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/autoexec-comomn.btm), which is called by my [autoexec-common.btm](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/autoexec.btm). Install these as a startup script to your current Windows installation with [install-autoexec-launcher-to-startup.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/install-autoexec-launcher-to-startup.bat)


### Command Line Startup Script: [environm.btm](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/environm.btm) (like ‘.bashrc’):

When TCC opens, it runs [tcstart.btm](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/tcstart.btm) (which should be placed in the ```c:\TCMD``` folder and is only in my BAT-files folder for packaging purposes).  ```tcstart.btm``` then runs [environm.btm](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/environm.btm), which is our main startup script for each command line instance.

1. To deal with mostly-false error messages, and to get our extra functionality working, you will need to edit ```c:\bat\environm.btm```. The goal is for it to produce *no* output when it runs. This is where E-V-E-R-Y-T-H-I-N-G is managed (a bit like unix .init/.rc files on steroids).<BR>
	Examples of some things defined in this central script are harddrive variables to eradicate hard-coded paths, drive-to-machine mappings to make every harddrive in the house/lan accessible to every other computer in the house/lan, repository locations for validating and backing up all your various collections. <BR>
	Secret things, like passwords, API keys, and IP addresses, can be stored in ```private.env```
    * Again, the goal is for ```environm.btm``` to produce *no* output when it runs.
      So let's get on that 😂😂😂

---------------------------------

### Things you almost definitely will want to do:

1. Define all your harddrives:
    * Edit ```environm.btm``` to make the following changes: 
    * Search for ```DEFINE HARDDRIVES``` and look through the next couple of pages. It looks absolutely bonkers, but redefinining the same information in a few different ways has been integral to ease-of-use. Just comment out anything that isn't YOUR harddrive. Unlike me, you might only have 1 computer and 1 drive, instead of 4 computers and 20 or so drives. You might not need the harddrive funtionality at all.
    * This will let you hard-code harddrives in scripts as environment variables instead of letters, so that if it is a different letter on a different computer in your house/LAN, there is a way to reference both locations correctly and simultaneously 
    * This will let you use our drive-related scripts, including: do-command-on-all-all-drives, wake-all-drives, map-drives, unmap-drives, checkmappings, display-drive-mapping, ensure-drive-is-mapped, label-all-drives, make-directory-matching-drive-label, wake-all-drives, myDrives, drives, whichdrive, c-drives


### Things you probably will want to do:

1. Define the computers in your system:
    * Edit ```environm.btm``` to make the following changes: 
    * Search for ```set ALL_COMPUTERS_UP```, and list out the names of all your computers in your house/lan here
    * Search for ```set ALL_COMPUTERS```   , and list out the names of all your computers in your house/lan here, INCLUDING DEAD/BROKEN ONES.
    * Search for ```MACHINE-SPECIFIC EMOJI``` and choose an emoji for your computer (type ```env emoji``` or edit ```emoji.env``` to see a list of them, and use ```emoji-grep``` to search for emoji via regular expression)
    * Search for ```MACHINE-SPECIFIC COLORS``` and choose a color unique for your computer. 
    * This will allow you to use our computer-related scripts, including: all-computers, all-computers-except-self, colorize-by-computer-name, highlight-by-computer-name, display-drives-by-computer.  Various computers are associated with various colors and emoji, which allows a faster visual summary of what's going on.


### Things you should do when you get around to it:

1. Edit [setpath.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/setpath.bat)  to convert your path-setting to dynamically-generated PATHs (also accessible from PowerShell/CMD). Take note of the various functions that can add folders path if the foldres exist, but not if they don't exist. Tthere can be machine-specific paths, paths that depend on, well. Anything really. And paths defined this way survive to all future machines, so adding them here is adding them for life.

1. Validate that your collections (repositories) haven't disappeared, and are fully accessible:
    * Edit ```c:\bat\environm.btm``` and search for "```DEFINE REPOSITORIES```".  For me, it's literally 35 screens of information about various repositories and workflows. Ignore or comment out what doesn't apply to you. Change what does apply to you. If you add anything, make sure to also add a validation for it. Follow the existing patterns in the file.
    * Run  ```c:\bat\environm.btm validate``` to validate all repository locations across all harddrives across all machines sharing this environment in the current house/LAN.  At first, it will be errors galore, because you are not me, and do not have my collections.  But after you edit *environm.btm* to properly reflect the locations of your collections/repositories (just follow the examples therein), you'll be able to use the *backup-repositories.bat* and *backups.bat* scripts, as well as validate that they are all still there. For me, with 20+ harddrives, this is often how I find out about a crashed drive.

1. Create a reliable backup plan for your collections/repositories:
    * Edit [backup-repositories.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/backup-repositories.bat) to match the repositories you want backed up. IT'S REALLY EASY. If ```environm validate``` produces no errors, you likely can edit this without any knowledge and experience, and then run ```backup-repositories.bat``` to start running your backups. They may error out the first time, if the destination folder doesn't exist. But once you fix that, it should be smooth backup sailing for life.

1. Create a reliable backup plan for important individual files:
    * Edit [backup-important-files.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/backup-important-files.bat) to reference important files you want backed up. Search for ```MAIN: BEGIN``` and follow the patterns within. For the dropbox functionality to work, you must have your dropbox-related variables defined properly in ```environm.btm```.

1. Create a reliable backup plan for important individual folders:
    * Edit [backup-important-folders.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/backup-important-folders.bat) ` to reference important folders you want backed up. Search for ```MAIN:``` and follow the patterns within. This one calls an individual BAT file for each important-individual-folder that you want to backup. Three examples already exist in the file for *Rogue Legacy 2*, *Xenia*, and *Rocksmith*. Follow the pattern to add more.

1. TODO

## Visual customizations you may want

1. Change your cursor color and shape by editing [set-cursor.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/set-cursor.bat) to create your own defaults such as [cursor-claire.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/cursor-Claire.bat) or [cursor-claire.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/cursor-Carolyn.bat).

1. Change your prompt (per-person/username, even) and its colors by looking at [prompt-common.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/prompt-common.bat), which is called by [setprompt.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/setprompt.bat). Also look at [prompt-Claire.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/prompt-Claire.bat) for an examle prompt that current CPU usage (which was insanity to implement).  

1. Reduce crash/hang/glitch anxiety by adding ```text color-cycling``` to slow scripts. Increases rainbow beauty and LOOKS REALLY COOL.
    * Integrated into our ```copy``` (cp) and ```move``` (mv) and ```unzip-gracefully``` (uzg) commands. (Notice how all the backslashes color-cycle when copying?)
    * Do this by by piping any slow steps to ```copy-move-post.py```
    * What's going on in the background for that is a lot of tight ANSI-voodoo loops and math calculations, along with using adaptive throttling with precision timers to preserve cpu resource
    * Some examples of how to do this are:
```
     very-slow.exe | copy-move-post
call very-slow-bat | copy-move-post
very-slow-commmand | copy-move-post
```

---------------------------------

# Enhanced Scripting Functionality To Start Using

Now that we have an environment, and our file are backed up, and we can relax.... What else can we do?


### Best practices for scripting, that reduce script brittleness, increase script longevity, and reduce the time that passes before realizing things are set up wrong:


1. Validating environment variables with [validate-environment-variable.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/validate-environment-variable.bat) and [validate-environment-variables.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/validate-environment-variables.bat): ```call validate-environment-variable VARNAME``` validates that an environment variable exists. And if the variable is a file/folder location, it will then validate it actually exists. Always validate environment variables before using them.

1. Validating commands’ validity with [validate-in-path.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/validate-in-path.bat): ```call validate-in-path whatever``` to validate if a command (internal, EXE, BAT, whatever) is valid. Always validate commands before using them. 

1. Validating user functions with [validate-function.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/validate-function.bat) and [validate-functions.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/validate-functions.bat): ```call validate-functions functionname1 functionname2 functionname3``` to validate if a user function  has been defined. For example, to see if  %@cursive[] has been defined, run ```validate-functions cursive```

1. Validating extensions with [validate-is-extension.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/validate-is-extension.bat): ```call validate-is-extension "filename" *.txt;*.lrc;*.src``` to validate if a filename has one of the listed extensions. Note that for this one, we pass a string, not an environment variable. So while we may ```validate-environment-variable INPUT_FILE``` to check an input file’s existence, to check its extensions, the call would look more like: ```validate-is-extension "%INPUT_FILE%" *.wav;*.mp3;*.flac```

1. Validating successful runs with [errorlevel.bat: The Great ErrorLevel Checker](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/errorlevel.bat): ```call errorlevel.bat "{optional custom error message in quotes}"``` will *OPTIONALLY* ½ execution if any form of errorlevel is returned by the previous command (whether internal, executable, or script). Always run this after running any kind of step that can fail.  It uses visual and audio alarms that are defined in [print-messages.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/print-messages.bat), and sets a ```%REDO%``` environment variable to 1, which can be used by the calling script to automatically retry failed commands.

1. Automatically re-running things that fail: ```errorlevel.bat``` sets an environment variable called ```%REDO%``` to 1 when any kind of failure is encountered. This can be used by the calling script to re-try sections of script over and over and over until they succeed. SUPER-USEFUL when a single piece of a long complicated workflow fails, and you don’t want to have to run your way back up to that point again. This allows you to attempt a fix, press a key to test it, and repeat until you succeed.
 
1. Improving presentation with ANSI cursor position manipulation. For example, a prompt can be blinking and red to draw attention to it, but once answered, green without the blinking once you answer it.  [set-ansi.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/set-ansi.bat) defines various ANSI strings  like ```%ANSI_POSITION_SAVE%```, ```%ANSI_POSITION_RESTORE%```; as well as ANSI user functions like ```%@ANSI_MOVE_UP[1]``` and ```%@ANSI_CURSOR_COLOR_CHANGE_BY_HEX[]```.  There are 100+. We also stick ```%ANSI_EOL%``` at the end of lines a lot in order to fix the bug where background colors bleed over to the rightmost column of the screen.

1. Improving presentation with emoji 🎂 and unicode ⨝.  [set-emoji.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/set-emoji.bat) instantiates all the emoji listed in [emoji.env](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/emoji.env).  Emoji are listed as ```EMOJI_{EMOJINAME}``` environment variables, and a few common ones like ```%STAR%``` and ```%ARROW%``` are defined at the bottom.  This is also where our ```%NEWLINE%``` and ```%TAB%``` variables get set.

1. Improve presentation by drawing attention to important messages using blinking (```%BLINK_ON%``` and ```%BLINK_OFF%```, both defined in ```set-ansi.bat```). Draw attention to the most important messages using double-height text ([bigecho.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/bigecho.bat))



## Visual best practices

1. Reduce mental fatigue be adding emoji to your scripts, particularly in the first column. It allows quicker understanding of what's going on, often saving having to read. 
    1400+ emoji are defined as enironment variables in ```set-emojis.bat```, as well as custom pentacle & pentagram & trumpet emoji created by [ANSI escape codes](https://en.wikipedia.org/wiki/ANSI_escape_code) after hand-drawing and converting to [sixels](https://en.wikipedia.org/wiki/Sixel).

1. Accelerate visual understanding of what's going on by adding color to your scripts, including consistent colors for consistent types of things, and random colors where applicable. For example, use ```%ANSI_COLOR_ADVICE%``` for advice, ```%ANSI_COLOR_WARNING%``` for warnings, ```%ANSI_COLOR_ERROR%``` for errors, ```%ANSI_COLOR_DEBUG%``` for debug info, etc. But for a huge list of long filenames, you would want each line to be a unique random color, which really helps when filenames get several lines long and you have trouble knowing where one ends and another begin. A random-colored emphasis can be added with ```%EMPHASIS%``` and ```%DEEMPHASIS%```.   All these environment variables are defined in ```set-colors.bat```, including the functions for custom-RGB foreground/background colors, random colors, and almost every kind of supported ANSI formatting in existence.

1. Improving  legibility by adding as much formatting as possible to scripts: bold & faint text, italicized & underscored text, reverse text, and strikethrough text. Environment variables defined in ```set-colors.bat``` make it very easy. For example:
```
	echo %@RANDCOLOR_FG[]This randomly-colored text has %BOLD_ON%bold%BOLD_OFF% and %ITALICS_ON%italics%ITALICS_OFF% text, and %@ANSI_RGB_FG[0,155,0] I really like this shade of green, %@ANSI_RGB_FG[0,0,50] especially with a slightly blue background to it.
```

1. Always use our internal message-printing system for consistency of presentation compliance. 
    * Messages are displayed with ```print-message.bat {message_type} {"message in quotes"}```
    * To see a test of every message type, run ```print-message.bat test fast```
    * Message decorators and audio effects can be changed in ```print-message.bat```
    * Environment variable ```%MESSAGE_TYPES_WITHOUT_ALIASES%``` contains all the different types of messages
    * Message types have each etheir own dedicated BAT files of the same name. 
    * Here are examples of messages of each types, in approximate order of drama:
```
	call fatal_error    "We're DONE! There is NO HOPE! STOP!!!"
	call error          "Uh-oh! This might be broken!"
	call alarm          "Take notice! We need attention!"
	call warning        "This may do a bad thing!"
	call warning_less   "This may do a thing that maybe might be a little bad..."
	call removal        "temp files have been deleted"

	call important      "narration of main tasks"
	call important_less "narration of subtasks"
	call unimportant    "not sure if we need to bother saying this anymore"
	call subtle         "pretty sure i don't need to say this anymore"

	call advice         "some good advice to take into consideration right now"
	call debug          "the value for %foo[1] is 4329.9342093 right now"

	call completion     "subtask completed"
	call success        "main task successful"
	call celebration    "entire script is done, let's have cake!"

	call normal         "we don't use this one"
```

---------------------------------

# Other cool things we can do

Stuff that isn't about scripting functionality, but which is cool.<BR>
Some of it is useful in scripts, some of it is useful at the command prompt.<BR>


## Visual things you can do:

1. Use ```emoji-grep.bat``` to search for emojis we have defined (about 1,400 are defined, and boy was it a pain!).

1. Use ```env ansi_``` to display all the ANSI variables that we have defined.<BR>Use ```functions|grep -i ansi_``` to display all the ANSI functions that we have defined 

1. Use [ANSI escape codes](https://en.wikipedia.org/wiki/ANSI_escape_code) in conjunction with [sixels](https://en.wikipedia.org/wiki/Sixel) to create brand new characters that don't exist.  To see some of the ones I created:
```echo %EMOJI_TRUMPET_COLORABLE% %PENTAGRAM% %PENTACLE% %EMOJI_TRUMPET_FLIPPED%```
    In this example, the pentagram is red a secondary environment variable was created that includes chaging the color to red *before* the pentagram, and changing the color to default/white *after* the pentagram. 

### Audio things you can do:

* Use ```speak.bat```       to speak with a human voice
* Use ```okgoogle.bat```    to control your smart home with a human voice

* Use ```randmidi.bat```    to create and play 15 seconds of random midi "music"

* Track the progress of minimized scripts by adding audio countdowns! As the beeps get lower and lower, you know your job is closer and closer to being done. For example, you can track a 5-step process this way:
```
  step1.exe   $+   call audio-countdown-noise 1 5
  step2.exe   $+   call audio-countdown-noise 2 5
  step3.exe   $+   call audio-countdown-noise 3 5
  step4.exe   $+   call audio-countdown-noise 4 5
  step5.exe   $+   call audio-countdown-noise 5 5
```

* Use ```white-noise.bat``` to create random white noise.
* Use ```cacophony.bat```   to create audio unpleasantness

* Use ```beep.bat test```   to preview all the Windows system sounds we can access from our command line.<BR>Change them in the Windows control panel.

* Use ```charge.bat```      to rally the troops


### More esoteric things you can do:

1. Tagging music: Embedding album art and *ReplayGain* tags into music files

1. Controlling *Winamp*: Music control, playlist management, and extracting the current song playing:
	* [winamp-setup-notes.txt](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/winamp-setup-notes.txt) — My personal guide on how to build WinAmp my way. 
	* [winamp-start.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/winamp-start.bat) — launches and initializes WinAmp. Moves windows to specific positions via [fix-winamp.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/fix-winamp.bat)
	* [winamp-stop.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/winamp-stop.bat) — kills winamp/etc with [winamp-close-gracefully.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/winamp-close-gracefully.bat), then if that doesn't work, via less gradceful methods.  Then re-launches WinAmp with [winamp-start.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/winamp-start.bat)
	* [get-winamp-state.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/get-winamp-state.bat) — retrives winamp state, prints it out, and assigns it to the ```%WINAMP_STATE%``` varaible
	* [stop.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/stop.bat), [play.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/play.bat), [paus.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/paus.bat) (without an e, as ```pause``` is a reserved command), [unpause.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/unpause.bat), [next.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/next.bat), [prev.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/prev.bat) — basic winamp stop/play/pause/unpase/next-track/previous-track functionality.
	* [winamp-randomize-playlist.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/winamp-randomize-playlist.bat)
	aka [randomize.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/randomize.bat) — randomizes winamp's playlist
	* [switch-winamp-to-playlist.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/switch-winamp-to-playlist.bat) aka [playlist.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/playlist.bat)  Replace existing Winamp plalylist
	* [enqueue-file-into-winamp-playlist.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/enqueue-file-into-winamp-playlist.bat.bat) — Enqueue single song to be the next playling song (had to recompile C code for this one)
	* [add-m3u-to-winamp-playlist.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/add-m3u-to-winamp-playlist.bat) — Append playlist to existing playlist
	* [enqueue-file-into-winamp-playlist.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/enqueue-file-into-winamp-playlist.bat.bat) — Append files from our collection that match a regular expression to the existing playlist. 
	* [remove-currently-playing-song-from-winamp-playlist.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/remove-currently-playing-song-from-winamp-playlist.bat) – Removes current song from WinAmp playlist.
	* [sync-winamp-playlists-to-dropbox.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/sync-winamp-playlists-to-dropbox.bat) — Backup WinAmp playlists to dropbox. Useful if you have music collections in several locations (i.e. home & work) and want playlist changes to propagate
	* [go-to-currently-playing-song-dir.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/go-to-currently-playing-song-dir.bat) – Changes into the folder of the currently-playing song by using the poorly-named 	[edit-currently-playing-attrib.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/edit-currently-playing-attrib.bat)
	and [edit-currently-playing-attrib-helper.pl](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/edit-currently-playing-attrib-helper.pl)
	* [nowplaying.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/nowplaying.bat) – Displays the current song playing, using [get-current-song-playing.pl](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/get-current-song-playing.pl) (which really should be called ```display-current-song-playing.pl```, sorry)
	* [winamp-status-from-file.pl](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/winamp-status-from-file.pl) – Deprecated alternate method to detect currently playing song (and WinAmp state) by scraping the [WAWI webserver’s](https://www.arcadecab.com/Projects/Wireless_jukebox.htm) home page	
	* [set-current_playing_song.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/set-current_playing_song.bat) — Sets environment variable ```%CURRENTLY_PLAYING_SONG%``` to be equal to the song currently playing. Uses [get-current-song-playing.pl](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/get-current-song-playing.pl)
	* [rn-currently-playing-song.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/rn-currently-playing-song.bat) — Renames the file of the currently playing song using our interactive renamer [rn.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/rn.bat).  Don’t hit enter until the next song is playing! 🤓
	* [get-lyrics-for-currently-playing-song.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/get-lyrics-for-currently-playing-song.bat) – Obtains lyrics for current song, to be saved as a sidecar file.
	* [create-srt-file-for-currently-playing-song.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/create-srt-file-for-currently-playing-song.bat) – Uses the WhisperAI to [transcribe a SRT karaoke file for the currently playing song, so that lyrics can be read and highlighted as a song is played](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/docs/song-lyric-transcriptoi-with-ai.md). Read more about it at [song-lyric-transcriptoi-with-ai.md](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/docs/song-lyric-transcriptoi-with-ai.md).
	* [remove-leading-0s-from-music-filenames.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/remove-leading-0s-from-music-filenames.bat) – For an album with fewer than 10 tracks, remove the leading ```0``` from the beginning of each filename. [TODO: this really is more of a music-management command than a winamp command]
	* **NOT REALLY USED:** [winamp_monitor.py](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/winamp_monitor.py) — logs tracks playing to the screen, to test Python-Winamp functionality


### Some scripts that drastically increase scripting power now exist:

1. [all-ready-drives.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/all-ready-drives.bat) can run a command on every single harddrive in your house/LAN

1. [run-piped-input-as-bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/run-piped-input-as-bat.bat)
1. insert-before|after-each-line.py/.pl - Both perl (25% faster) and python (emoji-capable) versions of utilities to insert text before and after each line. Substitutes ```{{{{QUOTE}}}}``` into quote marks. Used to generate-on-the-fly scripts which may also be piped to ```run-piped-input-as-bat```

1. git wrappers todo
1. ```dist.bat``` todo
1. ```.bat``` 
1. ```.bat``` 
1. ```.bat``` 
1. ```.bat``` 
1. ```.bat``` 


## Fun trinkets:

1. Never forget someone's age with ```age.bat```.  "How old is your mom?"  "She's 77.389"
![image](https://github.com/user-attachments/assets/325d90a4-2ddb-444c-a09f-e6c917acf04b)


1. rainbow-echo TODO

---------------------------------

## Enjoy!

1. ENJOY THE CLARIEVIRONMENT!  There's soooooooo much stuff in here. In the future, I will add more reference to this page about them. For the most part, you just have to explore. Most stuff is fairly heavily documented/commented.<BGR>
   Remember: *c:\bat\setpath.bat* can be run to set your path, if you wind up in a situation where commands aren't in your path.<BR>
   Setpath.bat also generates a *setpath.cmd* so that if you go into PowerShell or other shells, you can use the same generated path.





---------------------------------


# I would absolutely love feedback! 🤓

I would love to know how this works out for somebody who has never done it. Nobody outside of my own family has ever tried to use my environment. Such feedback is something I could use to further generalize my scripts to be more workable for other people.
















---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------
---------------------------------



Here are the old, deprecated, manual instructions, in case *clairevironment-install* fails in the future:

---------------------------------
---------------------------------
---------------------------------
---------------------------------


1. Install the Winget tool—which automated program installation—by invoking the following command in PowerShell:
```
  Add-AppxPackage -Path "https://aka.ms/getwinget"
```
  Or the following command in CMD.exe:
```powershell -Command "Add-AppxPackage -Path \"https://aka.ms/getwinget\""```

  If this fails at some point in the future, try [searching for "Winget"](https://apps.microsoft.com/search?query=winget+&hl=en-us&gl=US) in the [Microsoft App Store](https://apps.microsoft.com), but be wary of malware repacked versions——finding the official one this way can be challenging.

1. A lot of my stuff uses unix commands, so you should <em>probably</em> install cygwin from [here](https://www.cygwin.com/install.html), or with *"winget install --id=Cygwin.Cygwin -e"* or learn to recognize which things are breaking because of a lack of cygwin.

1. A lot of my stuff uses advanced ANSI codes that are ONLY supported in Windows Terminal.  The default Windows console can *NOT* handle these.  Install Windows Terminal either from the [official link at aka.ms](https://aka.ms/terminal) or [later/development versions from GitHub](https://github.com/microsoft/terminal)

1. Download my script/util folder into *c:\bat*, and place my *tcstart.bat* script into the correct folder<BR>
```
	git clone http://www.github.com/clairecjs/clairecjs_bat c:\clairecjs_bat.tmp
	move c:\clairecjs_bat.tmp\BAT-and-util-files c:\bat
	move c:\bat\tcstart.bat c:\tcmd
```

1. Add *C:\BAT\* to the BEGINNING your PATH:<BR>
```
   PATH=c:\bat\;%PATH%<BR>
```
   (A better way might be to go into advanced settings under Windows and edit it there.)<BR>
   (Impatient? Just run c:\bat\setpath.bat or c:\bat\setpath.cmd)

1. Configure *[c:\tcmd\tcstart.bat(https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/tcstart.bat)*:    This is the minimal script that is run every time TCC is opened, transient or not.<BR> 
   It belongs in ```C:\TCMD\```! Move it there!
   Open it up in a text editor and change the values for OS and MACHINENAME:<BR>
   <em>set OS=11</em><BR> — Valid values are: 95/98/XP/ME/2K/7/10/11 — for whichever version of windows you use
   <em>SET MACHINENAME=DEMONA</em> — Change this to your machinename! Or just use the same name as me 😅<BR>

1. Run TCC.exe your first time, ignoring any errors.  But not directly!  You want to open it in Windows Terminal!   So open up Windows Terminal, hit Ctrl-, (yes, control-comma) to go into settings. Scroll to the bottom of the left pane and click <em>‘Add new profile’</em>. You can duplicate the PowerShell profile or start a new one.  All you need to do is change the name to ```TCC```, the command line to ```c:\tcmd\tcc.exe```, the starting directory to ```c:\tcmd```, and run as administrator turned on.
   Now run it.
 
1. At your freshly-run TCC command-line, type ```option```, and switch to the "Advanced" tab.  In the upper-left is a section called *Special Characters*.  Change the separator to "^" (the [caret character](https://en.wikipedia.org/wiki/Caret)). This is actually a deviation from how most people do things, and it creates complications that I've mostly mitigated. However, if I missed any of those, this will be required for backward compatibility with bad decisions I made in the 1990s.

1. For EVERYTHING to work, we also need Perl. <BR>
   If you don't have Perl, install [Strawberry Perl](https://strawberryperl.com) to C:\PERL (not C:\STRAWBERRY), or else anything piping to Python or Perl will fail.<BR>
   Strawberry Perl can be installed with winget: *winget install -e --id StrawberryPerl.StrawberryPerl*
   You also may need my [my personal perl libraries](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/perl-sitelib-Clio.zip) ... Sorry, they have no installer. Just download [the zip file](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/perl-sitelib-Clio.zip) and unzip into into <em>c:\perl\perl\site\lib\Clio</em>

1. For EVERYTHING to work, we also need Python.<BR>
   If you don't have Python, install [Anaconda Python](https://www.anaconda.com/download) or else anything using an adjunct Pythons script is likely to fail.<BR>
   Python can be installed with winget: *winget install --id=Anaconda.Anaconda3  -e*
   You might also need my [clairecjs_util Python package](https://github.com/clairecjs/clairecjs_utils) ... Sorry, it has no installer. Just <em>git clone http://www.github.com/clairecjs/clairecjs_utils</em> and copy that folder into <em>anaconda3\lib\site-packages\clairecjs_utils</em>


1. You will also want to pay attention to *c:\bat\environm.btm*.<br>
	This is the script that is run every time TCC is run in a non-transient way.<BR>
	This is the most important script, basically the equivalent of your unix .init/.rc type files.<BR>
	Open it up in a text editor.<br>
	You don't need to do anything at first — It's just important that you know this file defines EVERYTHING.<BR>
	E-V-E-R-Y-T-H-I-N-G. 
	Harddrive letters, machine names, drive-to-machine mappings, repository locations, drive mapping information, IP addresses, the works. (Passwords go in private.env, however.)
	THIS IS THE MAIN FILE TO ORGANIZE MY COMMAND LINE LIFE.

1. Configure <em>c:\bat\environm.btm</em>:<BR>
	Run environm.btm over and over until any errors you don't like seeing are gone.<BR>
	You also could ignore them, but that would be ugly on your screen, and they tend to represent action items.<BR>
	*environm.btm* will now be the central script to handle all definitions of all things, to make sure your command line is in a PERFECT ZEN STATE for you.<BR>
	This file has an incredible set of messy examples that you can customize.<BR>
	Run *environm validate* to run the full set of repository location validation. This absolutely won't work but is a framework for making sure every repository you ever create exists in the correct place and is accessible from every computer in your LAN regardless of mapped drive letter differences.
	Ultimately, this is the file you want to customize for the rest of your life.<BR>
	If you have private environment variables you don't want in your <EM>environm.btm </EM>for privacy reasons, put them in <EM>c:\bat\private.env </EM>.


1. ENJOY THE CLARIEVIRONMENT!  There's soooooooo much stuff in here. In the future, I will add more reference to this page about them. For the most part, you just have to explore. Most stuff is fairly heavily documented/commented.<BGR>
   Remember: *[setpath.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files-1/setpath.bat)* can be run to set your path, if you wind up in a situation where commands aren't in your path.<BR>
   Setpath.bat also generates a *setpath.cmd* so that if you go into PowerShell or other shells, you can use the same generated path.




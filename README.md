# 🤓 The Clairevironment — Claire's personal script collection 🤓

## BAT files created for [JPsoft's TCC/TCMD command-line](http://www.JPSoft.com)...

### ...arguably the most sophisticated 64-bit command-line in existence, in constant development for over 35 years... 
### ...And this is the result of me using it for over 35 years.

This is basically a full layer of scripts built on top of TCC's functionality for 35 years, to add all kinds of functionality and improvement. Rich color, ANSI stylization, audio effects where appropriate, validators to prevent script brittleness, workflow management, repository validation, backups, maintenance, all kinds of stuff that is hard for me to describe because I've been working on this environment for 35 years. There's at least 800 scripts in this repo, though a lot are oneliners that call others and it's really probably only 300 significant scripts.

This is really about integrating existing tools that already exist.



---------------------------------


###  This is a full stack of stuff built around a command line. To use everything I've put here, you have to install everything as I've instructed here. This is what I go through every new computer. 

### ‼ Make sure to use the paths specified. A couple things need to be in alternate areas.


The abridged instructions are: Install TCC, run *clairevironment-install.bat*, add TCC to Windows Terminal, and you're done!

But here are the proper instructions:

1. Download TCC (Take Command command-line) from [http://www.jpsoft.com](http:///www.jpsoft.com) and install it to the NON-DEFAULT location of <em>c:\TCMD\</em>. DON'T run it just yet.

1. Grab [clairevironment-install.bat](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files/clairevironment-install.bat), and run (double-click) it.  Follow its instructions and pay attention.

1. Add TCC to Windows Terminal and Run it: 
    Open up *Windows Terminal*, hit Ctrl-, (yes, control-comma) to go into settings. Scroll to the bottom of the left pane and click *Add new profile*. You can duplicate the PowerShell profile or start a new one.  All you need to do is change the name to "TCC", the command line to ```c:\tcmd\tcc.exe```, the starting directory to ```c:\tcmd```, and *Run As Administrator* turned on.
    Now run it.

1. At your freshly-run TCC command-line, type ```option```, and switch to the *"Advanced"* tab.  In the upper-left is a section called *"Special Characters"*.  Change the separator to "^" (the [caret character](https://en.wikipedia.org/wiki/Caret)). 
    This is actually a deviation from how most people do things, due to the isolation of learning this command-line in the 1980s and 1990s. It creates complications that I've mostly mitigated—but not completely. Any mitigations I missed will cause failures unless you do this.


## At this point, everything is installed! The only problems you have at this point should be mostly-false error messages related to configuration.

1. To deal with mostly-false error messages, you will even5tually need to edit ```c:\bat\environm.btm```.<br>
	This is the most script, which is run every time TCC is run. This is the the equivalent of a unix .init/.rc type files.<BR>
	This script defines E-V-E-R-Y-T-H-I-N-G. Harddrive letters (to eradicate the process of hard-coded paths in scripts), drive-to-machine mappings (for sharing drives across all local computers in this environment), repository locations (for validating and backing up all your various collections), the works. (Passwords, secret things, and secret API keys go in ```private.env```)
    * You ultimately want it to produce *no* output when it runs, or else there will be permanent ugliness.
      So let's get on that 😂😂😂

## Now let's go over some things you definitely will want to do:

1. Define all your harddrives:
    * Edit ```environm.btm```and search for ```DEFINE HARDDRIVES``` and look through the next couple of pages. It looks absolutely bonkers, but redefinining the same information in a few different ways has been integral to ease-of-use. Just comment out anything that isn't YOUR harddrive. Unlike me, you might only have 1 computer and 1 drive, instead of 4 computers and 20 or so drives.
    * This will let you hard-code harddrives in scripts as environment variables instead of letters, so that if it is a different letter on a different computer in your house/LAN, there is a way to reference both locations correctly and simultaneously 
    * This will let you use our drive-related scripts, including: do-command-on-all-all-drives, wake-all-drives, map-drives, unmap-drives, checkmappings, display-drive-mapping, ensure-drive-is-mapped, label-all-drives, make-directory-matching-drive-label, wake-all-drives, myDrives, drives, whichdrive, c-drives


## Now let's go over some things you probably will want to do:

1. Define the computers in your system:
    * Edit ```environm.btm``` 
    * Search for ```set ALL_COMPUTERS_UP```, and list out the names of all your computers in your house/lan here
    * Search for ```set ALL_COMPUTERS```   , and list out the names of all your computers in your house/lan here, INCLUDING DEAD/BROKEN ONES.
    * Search for ```MACHINE-SPECIFIC EMOJI``` and choose an emoji for your computer (type ```env emoji``` or edit ```emoji.env``` to see a list of them, and use ```emoji-grep``` to search for emoji via regular expression)
    * Search for ```MACHINE-SPECIFIC COLORS``` and choose a color unique for your computer. 
    * This will allow you to use our computer-related scripts, including: all-computers, all-computers-except-self, colorize-by-computer-name, highlight-by-computer-name, display-drives-by-computer.  Various computers are associated with various colors and emoji, which allows a faster visual summary of what's going on.

1. Validate that your collections (repositories) haven't disappeared, and are fully accessible:
    * Edit ```c:\bat\environm.btm``` and search for "```DEFINE REPOSITORIES```".  For me, it's literally 35 screens of information about various repositories and workflows. Ignore or comment out what doesn't apply to you. Change what does apply to you. If you add anything, make sure to also add a validation for it. Follow the existing patterns in the file.
    * Run  ```c:\bat\environm.btm validate``` to validate all repository locations across all harddrives across all machines sharing this environment in the current house/LAN.  At first, it will be errors galore, because you are not me, and do not have my collections.  But after you edit *environm.btm* to properly reflect the locations of your collections/repositories (just follow the examples therein), you'll be able to use the *backup-repositories.bat* and *backups.bat* scripts, as well as validate that they are all still there. For me, with 20+ harddrives, this is often how I find out about a crashed drive.

1. Create a reliable backup plan for your collections/repositories:
    * Edit ```backup-repositories.bat``` to match the repositories you want backed up. IT'S REALLY EASY. If ```environm validate``` produces no errors, you likely can edit this without any knowledge and experience, and then run ```backup-repositories.bat``` to start running your backups. They may error out the first time, if the destination folder doesn't exist. But once you fix that, it should be smooth backup sailing for life.

1. Create a reliable backup plan for important individual files:
    * Edit ```backup-important-files.bat``` to reference important files you want backed up. Search for ```MAIN: BEGIN``` and follow the patterns within. For the dropbox functionality to work, you must have your dropbox-related variables defined properly in ```environm.btm```.

1. Create a reliable backup plan for important individual folders:
    * Edit ```backup-important-folders.bat``` to reference important folders you want backed up. Search for ```MAIN:``` and follow the patterns within. This one calls an individual BAT file for each important-individual-folder that you want to backup. Three examples already exist in the file for *Rogue Legacy 2*, *Xenia*, and *Rocksmith*. Follow the pattern to add more.

1. TODO

1. TODO

1. TODO

1. TODO


## And let's go over some things you MAY want to do:

1. Dynamically-generated PATHs accessible from PowerShell/CMD. Look at ```setpath.bat```. TODO.


## Visual things you can do:

1. Use ```print-message.bat``` to consistently display messages in the best way possible

1. Use ```emoji-grep.bat`` to search for emojis we have defined (about 1,400 are defined, and boy was it a pain!).

1. Change the colors of your prompt (per-person/username, even) by looking at ```setprompt.bat```

1. Add ```color-cycling``` of default-color'ed text to slow scripts, so that you know things aren't hung, by piping any slow steps to ```copy-move-post.py```. What's going on in the background for that is a lot of tight ANSI-voodoo loops and math calculations, along with using adaptive throttling using precision timers to avoid eating up all the cpu cycles:  Some examples of how to do this are:
```     very-slow.exe | copy-move-post```
```call very-slow-bat | copy-move-post```
``` very-slow-command | copy-move-post```
    * This is integrated into our ```copy``` (cp) and ```move``` (mv) and ```unzip-gracefully``` (uzg) commands, all of which can look stalled when running on big files. Notice how all the backslashes color-cycle? Seeing the colors cycle lets you know that things are *not* in fact stalled or hung. AND IT LOOKS REALLY REALLY COOL.

1. Use (ANSI escape codes)[https://en.wikipedia.org/wiki/ANSI_escape_code] in conjunction with [sixels](https://en.wikipedia.org/wiki/Sixel) to create brand new characters that don't exist.  To see some of the ones I created:
```echo %EMOJI_TRUMPET_COLORABLE% %PENTAGRAM% %PENTACLE% %EMOJI_TRUMPET_FLIPPED%``````
    In this example, the pentagram is red a secondary environment variable was created that includes chaging the color to red *before* the pentagram, and changing the color to default/white *after* the pentagram. 

## Audio things you can do:

* Track the progress of minimized scripts by adding audio countdowns! As the beeps get lower and lower, you know your job is closer and closer to being done. For example, you can track a 5-step process this way:
```
	step1.exe $+ call audio-countdown-noise 1 5
	step2.exe $+ call audio-countdown-noise 2 5
	step3.exe $+ call audio-countdown-noise 3 5
	step4.exe $+ call audio-countdown-noise 4 5
	step5.exe $+ call audio-countdown-noise 5 5
```

* Use ```beep.bat test```   to preview all the Windows system sounds we can access from our command line. 
  (Change them in the Windows control panel.)

* Use ```speak.bat```       to speak with a human voice

* Use ```okgoogle.bat```    to control your smart home with a human voice

* Use ```charge.bat```      to rally the troops

* Use ```white-noise.bat``` to create random white noise.

* Use ```white-noise.bat``` to create random midi "music".  

* Use ```cacophony.bat```   to create audio unpleasantness


## More esoteric things you can do:

1. Tagging music: Embedding album art and *ReplayGain* tags into music files

1. Controlling *Winamp*: Play/Pause/Stop/etc as well as randomizing/adding/removing songs to the playlist. Determining the current song playing (if winamp is integrated into last.fm).

1. TODO


## Best practices for scripting, that reduce script brittleness, increase script longevity, and reduce the time that passes before realizing things are set up wrong:

1. Always use our internal message-printing system for consistency of presentation compliance. Messages are displayed with ```print-message.bat {message_type} {"message in quotes"}```. Environment variables ```%MESSAGE_TYPES_WITHOUT_ALIASES%``` contains all the different types of messages. Message types have their own dedicated BAT files of the same name. Here are examples of the current types, in approximate order of drama:
```
	call fatal_error    "We're DONE! There is NO HOPE! STOP!!!"
	call error          "Uh-oh! This might be broken!"
	call alarm          "Take notice! We need attention!"
	call warning        "This may do a bad thing!"
	call warning_less   "This may do a thing that maybe might be a little bad..."

	call important      "narration of main tasks"
	call important_less "narration of subtasks"
	call unimportant    "not sure if we need to bother saying this anymore"
	call subtle         "pretty sure i don't need to say this anymore"

	call advice         "this is something nice to know right now"
	call debug          "the value for X is 69 right now"
	call removal        "File deleted!"

	call completion     "task competed"
	call success        "task successful"
	call celebration    "everything is done, let's have cake"

	call normal         "we don't use this one"
```
    The message decorators and audio effects can be changed in ```print-message.bat```.
    To see a test of every message type, run ```print-message.bat test fast```.

1. Eradicating hard-coded paths: By having environment variables for each harddrive (and for common locations) all centrally defined in ```environm.btm```, we can reference locations in a dynamic way that changes over time [less brittle, more reliable].

1. Validating environment variables: ```call validate-environment-variable VARNAME``` validates that an environment variable exists. And if the variable is a file/folder location, it will then validate it actually exists. Always validate environment variables before using them.

1. Validating commands: ```call validate-in-path whatever``` to validate if a command (internal, EXE, BAT, whatever) is valid. Always validate commands before using them. 

1. Validating successful runs: ```call errorlevel.bat "{optional custom error message in quotes}"``` will halt execution if any form of errorlevel is returned by the previous command (whether internal, executable, or script).   
  Always validate after running any kind of step that can fail.  
  (It uses visual and audio alarms that are defined in ```print-messages.bat```, and sets a ```%REDO%``` environment variable that can be used for automatic retries.) 

1. Automatically re-running things that fail: ```errorlevel.bat``` sets an environment variable called ```%REDO%``` to 1, which can be used to re-try sections of script over and over and over until they succeed. SUPER-USEFUL when a single peice of a long complicated workflow fails, and you find yourself having to manually run a step in the middle of a long script. This allows you to fix the situation, then press any key to retry without losing your place in your script. 
    In the event of error, it gives a timed prompt allowing a gracefully return to the command line in a more reliable way than ``Ctrl-C``` or ```Ctrl-Break``` (or rapidly alternating between those 2 keys, which unfortunately works worse in Windows Terminal).
    
1. Improving presentation with ANSI cursor position manipulation. For example, a prompt can be blinking and red to draw attention to it, but once answered, green without the blinking once you answer it.  ```set-colors.bat``` defines various cursor functions like ```%ANSI_POSITION_SAVE%```, ```%ANSI_POSITION_RESTOR%```, ```%@ANSI_MOVE_UP[1]```, and such.  We also stick ```%ANSI_EOL%``` at the end of lines a lot in order to fix the bug where background colors bleed over to the rightmost column of the screen.

## Accessibility / mental fatigue improvements:

1. Reduce mental fatigue be adding emoji to your scripts, particularly in the first column. It allows quicker understanding of what's going on, often saving having to read. 
    1400+ emoji are defined as enironment variables in ```set-emojis.bat```, as well as custom pentacle & pentagram & trumpet emoji created by (ANSI escape codes)[https://en.wikipedia.org/wiki/ANSI_escape_code] after hand-drawing and converting to [sixels](https://en.wikipedia.org/wiki/Sixel).

1. Accelerate visual understanding of what's going on by adding color to your scripts, including consistent colors for consistent types of things, and random colors where applicable. For example, use ```%ANSI_COLOR_ADVICE%``` for advice, ```%ANSI_COLOR_WARNING%``` for warnings, ```%ANSI_COLOR_ERROR%``` for errors, ```%ANSI_COLOR_DEBUG%``` for debug info, etc. But for a huge list of long filenames, you would want each line to be a unique random color, which really helps when filenames get several lines long and you have trouble knowing where one ends and another begin. A random-colored emphasis can be added with ```%EMPHASIS%``` and ```%DEEMPHASIS%```.   All these environment variables are defined in ```set-colors.bat```, including the functions for custom-RGB foreground/background colors, random colors, and almost every kind of supported ANSI formatting in existence.

1. Improve misdirected attention by adding blinking and double-height text (```set-colors.bat```)

1. Improving  legibility by adding as much formatting as possible to scripts: bold & faint text, italicized & underscored text, reverse text, and strikethrough text. Environment variables defined in ```set-colors.bat``` make it very easy. For example:
```
	echo %@RANDCOLOR_FG[]This randomly-colored text has %BOLD_ON%bold%BOLD_OFF% and %ITALICS_ON%italics%ITALICS_OFF% text, and %@ANSI_RGB_FG[0,155,0] I really like this shade of green, %@ANSI_RGB_FG[0,0,50] especially with a slightly blue background to it.
```


## Some scripts that drastically increase scripting power now exist:

1. ```all-ready-drives.bat```can run a command on every single harddrive in your house/LAN

1. ```.bat``` 
1. ```.bat``` 
1. ```.bat``` 
1. ```.bat``` 
1. ```.bat``` 
1. ```.bat``` 
1. ```.bat``` 
1. ```.bat``` 
1. ```.bat``` 
1. ```.bat``` 
1. ```.bat``` 
1. ```.bat``` 
1. ```.bat``` 
1. ```.bat``` 
1. ```.bat``` 
1. ```.bat``` 


## Fun trinkets:

1. Never forget someone's age with ```age.bat```.  "How old is your mom?" ```age mom```.  "She's 77.389"



1. ENJOY THE CLARIEVIRONMENT!  There's soooooooo much stuff in here. In the future, I will add more reference to this page about them. For the most part, you just have to explore. Most stuff is fairly heavily documented/commented.<BGR>
   Remember: *c:\bat\setpath.bat* can be run to set your path, if you wind up in a situation where commands aren't in your path.<BR>
   Setpath.bat also generates a *setpath.cmd* so that if you go into PowerShell or other shells, you can use the same generated path.






















Here are the old, deprecated, manual instructions, in case *clairevironment-install* fails in the future:

1. Install the Winget tool—which automated program installation—by invoking the following command in PowerShell:
```
  Add-AppxPackage -Path "https://aka.ms/getwinget"
```
  Or the following command in CMD.exe:
```powershell -Command "Add-AppxPackage -Path \"https://aka.ms/getwinget\""```

  If this fails at some point in the future, try [searching for "Winget"](https://apps.microsoft.com/search?query=winget+&hl=en-us&gl=US) in the [Microsoft App Store](https://apps.microsoft.com), but be wary of malware repacked versions——finding the official one this way can be challenging.

1. A lot of my stuff uses unix commands, so you should <em>probably</em> install cygwin from [here](https://www.cygwin.com/install.html), or with *"winget install --id=Cygwin.Cygwin -e"* or learn to recognize which things are breaking because of a lack of cygwin.

1. A lot of my stuff uses advanced ANSI codes that are ONLY supported in Windows Terminal.  The default Windows console can *NOT* handle these.  Install Windows Terminal either from the [official link at aka.ms](https://aka.ms/terminal) or [later/development versions from GitHub](https://github.com/microsoft/terminal)

1. Download my script/util folder into <em>c:\bat</em>, and place my *tcstart.bat* script into the correct folder<BR>
```
	git clone http://www.github.com/clairecjs/clairecjs_bat c:\clairecjs_bat.tmp
	move c:\clairecjs_bat.tmp\BAT-and-util-files c:\bat
	move c:\bat\tcstart.bat c:\tcmd
```

1. Add <em>C:\BAT\</em>to the BEGINNING your PATH:<BR>
```
   PATH=c:\bat\;%PATH% </em><BR>
```
   (A better way might be to go into advanced settings under Windows and edit it there.)<BR>
   (Impatient? Just run c:\bat\setpath.bat or c:\bat\setpath.cmd)

1. Configure *c:\tcmd\tcstart.bat*:    This is the minimal script that is run every time TCC is opened, transient or not.<BR>
   Open it up in a text editor and change the values for OS and MACHINENAME:<BR>
   <em>set OS=11</em><BR> — Valid values are: 95/98/XP/ME/2K/7/10/11 — for whichever version of windows you use
   <em>SET MACHINENAME=DEMONA</em> — Change this to your machinename! Or just use the same name as me 😅<BR>

1. Run TCC.exe your first time, ignoring any errors.  But not directly!  You want to open it in Windows Terminal!   So open up Windows Terminal, hit Ctrl-, (yes, control-comma) to go into settings. Scroll to the bottom of the left pane and click <em>'Add new profile'</em>. You can duplicate the PowerShell profile or start a new one.  All you need to do is change the name to "TCC", the command line to "c:\tcmd\tcc.exe", the starting directory to "c:\tcmd", and run as administrator turned on.
   Now run it.
 
1. At your freshly-run TCC command-line, type ```option```, and switch to the "Advanced" tab.  In the upper-left is a section called *Special Characters*.  Change the separator to "^" (the caret character). This is actually a deviation from how most people do things, and it creates complications that I've mostly mitigated. However, if I missed any of those, this will be required for backward compatibility with bad decisions I made in the 1990s.

1. For EVERYTHING to work, we also need Perl. <BR>
   If you don't have Perl, install [Strawberry Perl](https://strawberryperl.com) to C:\PERL (not C:\STRAWBERRY), or else anything piping to Python or Perl will fail.<BR>
   Strawberry Perl can be installed with winget: *winget install -e --id StrawberryPerl.StrawberryPerl*
   You also may need my [my personal perl libraries](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files/perl-sitelib-Clio.zip) ... Sorry, they have no installer. Just download [the zip file](https://github.com/ClaireCJS/clairecjs_bat/blob/main/BAT-and-UTIL-files/perl-sitelib-Clio.zip) and unzip into into <em>c:\perl\perl\site\lib\Clio</em>

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
   Remember: *c:\bat\setpath.bat* can be run to set your path, if you wind up in a situation where commands aren't in your path.<BR>
   Setpath.bat also generates a *setpath.cmd* so that if you go into PowerShell or other shells, you can use the same generated path.



---------------------------------


# I would absolutely love feedback! 🤓

I would love to know how this works out for somebody who has never done it. Nobody outside of my own family has ever tried to use my environment. Such feedback is something I could use to further generalize my scripts to be more workable for other people.



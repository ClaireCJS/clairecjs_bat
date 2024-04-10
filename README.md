# 🤓 The Clairevironment — Claire's personal script collection 🤓

## BAT files created for [JPsoft's TCC/TCMD command-line](http://www.JPSoft.com)...

### ...arguably the most sophisticated 64-bit command-line in existence, in constant development for over 35 years...

#### These BAT files have been in constant development for over 35 year, too.

This is basically a full layer of scripts built on top of TCC's functionality for 35 years, to add all kinds of functionality and improvement. Rich color, ANSI stylization, audio effects where appropriate, validators to prevent script brittlness, workflow management, all kinds of stuff that is hard for me to describe because I've been working on this environment for 35 years. There's at least 600 scripts in this repo, though a lot are oneliners that call others.

Installation is not easy, bedcause this is really about integrating existing tools.



---------------------------------


### ‼ To install and use this, make sure to use the paths specified, because there is some ugly hard-coding at points. Do not deviate from these steps or things will eventually fail:

1. A lot of my stuff uses unix commands, so you should <em>probably</em> install [cygwin](https://www.cygwin.com/install.html), or learn to recognize which things are breaking because of a lack of cygwin.

1. A lot of my stuff uses advanced ANSI codes that are ONLY supported in Windows Terminal.  The default Windows console can *NOT* handle these.  Install Windows Terminal either from the [official link at aka.ms](https://aka.ms/terminal) or [later/development versions from GitHub](https://github.com/microsoft/terminal)

1. Download the TCC command line installer from JPsoft at [www.jpsoft.com](http:///www.jpsoft.com)

1. Install TCC to <em>c:\TCMD\ </em>instead of to the default location in program files

1. Now you're ready to download my script files:<BR>
   <em>git clone http://www.github.com/clairecjs/clairecjs_bat</em>

1. Put these script files into the correct hardcoded location of *c:\bat*:<br>
   <em>copy clairecjs_bat\BAT-and-UTIL-files\ c:\bat</em>

1. Add <em>C:\BAT\ </em>to your PATH:<BR>
   <em>PATH=%PATH%;c:\bat\ </em><BR>
   (A better way might be to go into advanced settings under Window and edit it there.)<BR>
   (An alternate method to do this quickly is to just run c:\bat\setpath.bat)

1. Copy our TCC-start-script into the TCC folder:<BR>
   <em>copy c:\bat\tcstart.bat c:\tcmd</em>

1. Configure *tcstart.bat*:    This is the minimal script that is run every time TCC is opened, transient or not.<BR>
   Open it up in a text editor and change the values for OS and MACHINENAME:<BR>
   <em>set OS=10</em><BR>
   <em>SET MACHINENAME=DEMONA</em> — Change this to your machinename! Or just use the same name as me 😅<BR>
   Valid OS values are 95/98/XP/ME/2K/7/10/11 — I've used all of these over the years!<BR>
   Most people just want "11" these days!<BR>

1. Run TCC.exe your first time, ignoring any errors.  But not directly!  You want to open it in Windows Terminal!   So open up Windows Terminal, hit Ctrl-, (yes, control-comma) to go into settings. Scroll to the bottom of the left pane and click <em>'Add new profile'</em>. You can duplicate the PowerShell profile or start a new one.  All you need to do is change the name to "TCC", the command line to "c:\tcmd\tcc.exe", the starting directory to "c:\tcmd", and run as administrator turned on.

1. Type <em>option</em> at the TCC command line, switch to the "Advanced" tab.  In the upper-left is a section called *Special Characters*.  Change the separator to "^" (the caret character). This is actually a deviation from how most people do things, and it creates complications that I've mitigated. However, it's required for backward compatibility with decisions I made in the 1990s (which I have not yet mitigated, and probably never will).

1. You really need to install [Anaconda Python](https://www.anaconda.com/download) and [Strawberry Perl](https://strawberryperl.com), too ..... Or else anything piping to Python or Perl will fail.

1. You will also want to pay attention to *c:\bat\environm.btm*.<br>
	This is the script that is run every time TCC is run in a non-transient way.<BR>
	This is the most imporant script, basically the equivalent of your unix .init/.rc type files.<BR>
	Open it up in a text editor.<br>
	You don't need to do anything at first — It's just important tyat you now this file defines EVERYTHING. E-V-E-R-Y-T-H-I-N-G. 

1. Configure <em>c:\bat\environm.btm:</em>.<BR>
	Run environm.btm over and over until any errors you don't like seeing are gone.<BR>
	You also could ignore them, but that would be ugly on your screen.<BR>
	*environm.btm* will now be the central script to handle all definitions of all things, to make sure your command line is in a PERFECT ZEN STATE for you.<BR>
	This file has an incredible set of messy examples that you can customize.<BR>
	Ultimately, this is the file you want to customize for the rest of your life.<BR>
	If you have private environment variables you don't want in your <EM>environm.btm </EM>for privacy reasons, put them in <EM>c:\bat\private.env </EM>s.


1. ENJOY THE CLARIEVIRONMENT!  There's soooooooo much stuff in here. In the future, I will add more reference to this page about them. For the most part, you just have to explore. Most stuff is fairly heavily documented/commented.
   Remember: *c:\bat\setpath.bat* can be run to set your path, if you wind up in a situation where commands aren't in your path. 
   Setpath.bat also generates a *setpath.cmd* so that if you go into PowerShell or other shells, you can use the same generated path.



---------------------------------


# I would absolutely love feedback! 🤓

I would love to know how this works out for somebody who has never done it. Such feedback is something I could use to further generalize my scripts to be more workable for other people.


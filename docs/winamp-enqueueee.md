# Updated EnqueueEE.exe for WinAmp

[EnqueueEE.exe](../BAT-and-UTIL-files-1/enqueueee2024.zip) is a WinAmp utility first posted on the [Winamp forums in 2004](https://forums.winamp.com/forum/developer-center/winamp-development/176397-enqueue-and-play?p=2244202#post2244202) by a user named [jyeee](https://forums.winamp.com/member/160968-jyeee).

It is a command-line song enqueue'er for WinAmp.  It adds an mp3/songfile to your current winamp playlist, as the next song after the one currently playing.

Because it came with its [CPP source](../enqueueee.cpp), I was able to modify it to behave the way I wanted, which isn't the way the author wanted.  

The original author wanted "enqueue and play immediately".  Enque'ing a song would end the current song and move to the enque'd song.

I wanted "just enqueue".  So that I can enqueue several songs at once without disturbing the playlist over and over.  Enque'ing a song in my version adds it to the next slot in the playlist, and does NOT play it.  The song you are currently listening to continues playing. 

The original fix was done in 2020, with a Windows 10-specific fix in 2024.

[jyeee](https://forums.winamp.com/member/160968-jyeee), wherever you are, thank you for providing the source. That was nice.




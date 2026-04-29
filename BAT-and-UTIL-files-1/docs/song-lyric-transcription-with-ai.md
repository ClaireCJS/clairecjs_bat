
# 🎆 AI Lyric Transcription System For Windows 🎆

## ✨ Goals: ✨

  1. 🥅 *General*: 🥅 To see the lyrics 📄 to music 🎵 highlighted ↔ as they are sung 🎤
  1. 🥅 *Technical*: 🥅 To automate AI transcription of music into karaoke files
  1. 🥅 *Specific*: 🥅 To have the [MiniLyrics](https://minilyrics.en.softonic.com/) program correctly display lyrics as they are sung.
  1. 🥅 *Detailed*: 🥅 To obtain and approve accurate lyrics for songs, which are then used as a prompt to improve the accuracy of WhisperAI’s transcription of audio files into karaoke/subtitle files, as well as to ensure each file has TXT and either LRC or SRT subtitles—usually both.

-----------------------------------------------------------------------------------------------------------------------------------------------

## 📓 Terminology: 📓

<details><summary>Click here to view full definitions of “karaoke files” and “sidecar files”</summary>  
  
  &nbsp;
  
  📑 *Karaoke Files*: 📑 We generally call both ```SRT files``` and ```LRC files``` “karaoke files”, which is a colloquial shorthand for “files capable of displaying the lyrics *as* they are sung”. This system generates ```SRT``` files, but includes a batch converter that converts ```SRT``` to ```LRC```.
  
  &nbsp;
  
  🏎 *Sidecar Files*: 🏎 A file of the *same* name, but *different* extension.
  
  For example, ```filename.mp3``` might have a sidecar file named ```filename.txt```, which would typically be lyrics for a song, and a sidecar file named ```filename.jpg```, which would typically be the cover art to the song.  
  
  Another example is when a program like ```whatever.exe``` has a ```whatever.ini`` *INI file* for its settings; That *INI* file is a sidecar file the *EXE* file. 
  
  
  😢 *Lyriclessness*: This meaning is specific to this project: Lyriclessness is a state in which a song’s lyrics cannot be found on the internet. At this point of giving up on our lyrics search, we can “approve” the lyriclessness state to mark our task as complete.
  
  
  🎸 *Instrumental*: A song that has no vocals or lyrics. The system WILL skip processing these. Marked with “ [instrumental]” in the filename.
  
  🎹 *Semi-Instrumental*: The system will NOT skip processing these. Marked with “ [semi-instrumental]” in the filename. A semi-instrumental is a song that has either:
    - vocals that aren’t lyrics, i.e. lyricless opera, skat, choruses going “ahhh”, etc
    - words that aren’t vocals, i.e. an electronica song but it starts off with a spoken-word sample
    - Some of these may need to be marked “[no lyrics]” to prevent processing

</details>


-----------------------------------------------------------------------------------------------------------------------------------------------

# ✔️ Setup/Requirements: ✔️

<details><summary>Click here to view the full requirements, which are primarily: Whisper, TCC, my scripts, and an optional WinAmp plugin</summary>  
  
  &nbsp; 
  
1. 👂 AI: The [latest Faster-Whisper-XXL binaries](https://github.com/Purfview/whisper-standalone-win/releases/tag/Faster-Whisper-XXL)

    - The command ``faster-whisper-xxl.exe`` — our AI transriber — must be in your ```path```.

&nbsp;    

2. 💻 Command line requirements ([JPSoft’s TakeCommand (TCC) command-line v31+](https://jpsoft.com/all-downloads/all-downloads.html))
    - Install JPSoft’s TakeCommand (aka “TCC”):
        - either from [JPSoft.com](https://jpsoft.com/all-downloads/all-downloads.html)
        - or via *WinGet* with the command: ```winget install JPSoft.tcmd```
          - No *WinGet*? Install it in *PowerShell* with the command ```Add-AppxPackage -Path "https://aka.ms/getwinget"``` 
          - or with command ```Add-AppxPackage -RegisterByFamilyName -MainPackage Microsoft.DesktopAppInstaller_8wekyb3d8bbwe```
    - Make ```c:\TCMD``` point to our [TCC](https://jpsoft.com/all-downloads/all-downloads.html) installation:
      - via the command: ```mklink c:\TCMD "c:\Program Files\TCMD31"``` 
      - The folder ```TCMD31``` may vary depending on what version of [TCC](https://jpsoft.com/all-downloads/all-downloads.html) is current.
    - Update TCC to be compatible with my scripts:
       - Open **TCC/TCMD** 
       - type ```option``` at the command line
       - In the upper-left is a section called *“Special Characters”*
       - Change the separator to “^” (the [caret character](https://en.wikipedia.org/wiki/Caret))
       
&nbsp;

3. 🐍 Python requirements 
    - Install Python Anaconda ... That one specifically. [TODO link this]
    - install the *LyricsGenius* package: 
      - install: ```pip install lyricsgenius```
      - upgrade: ```pip install -U lyricsgenius```
      - ensure that ```lyricsgenius.exe``` is in your path and works as a command
    - install the *SyncedLyrics* package:
      - install: ```pip install syncedlyrics```
      - ensure that ```syncedLyrics.exe``` is in your path and works as a command
    - install the *WhisperTimeSync* package:
      - install: ```pip install WhisperTimeSync```
      - if that doesn’t work, check out instructions at: ttps://github.com/EtienneAb3d/WhisperTimeSync
      - Set ```JAVA_WHISPERTIMESYNC``` enivronment variable  to the path of the java.exe you wish to use. Or just set it to "java" if the java command is in your path and happens to be the version you’re comfortable with using.
        As of 2026, what works for me is: ```set JAVA_WHISPERTIMESYNC=C:\Program Files\Java\jre-1.8\bin\java.exe```

&nbsp;

4. 🦪 Perl
    - Install Strawberry Perl [TODO link this]
    - install [my Perl libraries](../perl-sitelib-Clio.zip)
      - ```Unzip perl-sitelib-Clio.zip``` into ```c:\Strawberry\perl\site\lib\Clio```
    - Alternately, Install [my whole site\lib folder](../perl-site-lib.zip)
      - ```Unzip perl-site-lib.zip``` into ```c:\Strawberry\perl\site\lib\```

&nbsp;

5. 🖥 [Windows Terminal](https://jpsoft.com/all-downloads/all-downloads.html).  
    - Needed to support our colorful presentation
    - Will look nonsensical otherwise
    - Install *Windows Terminal*:
      - either from [GitHub](https://github.com/microsoft/terminal/releases/)
      - or via *WinGet* with the command: ```winget install -e --id Microsoft.WindowsTerminal```
      - or from the Microsoft Store
    - Add *TCC* to your *Windows Terminal*:
      - Open up *Windows Terminal*
      - Hit Ctrl-, (yes, control-comma) to go into settings
      - Scroll to the bottom of the left pane and click *Add new profile*
      - Duplicate the PowerShell profile
      - Change the name to “TCC”
      - Change the command line to ```c:\tcmd\tcc.exe```
      - Change the starting directory to ```c:\tcmd```
      - Ensure *Run As Administrator* is turned on. 
      - Go into ```Appearance``` and change the font to *Cascadia Code*, which has the proper [ligature rendering](https://github.com/microsoft/cascadia-code#font-features) that I take advantage of cosmetically.
      

&nbsp;    


6. ⌨️ My full [Clairevironment](https://github.com/ClaireCJS/clairecjs_bat/) (a big ball of stuff which includes this project).
    - Technically you probably only need about 100 of these files.  
    - This folder has it’s own ```sort``` and ```uniq``` executables (from [Cygwin](https://www.cygwin.com)) to ensure consistency
    - To install: 
```
git.exe clone https://github.com/ClaireCJS/clairecjs_bat/
mv BAT-and-UTIL-files-1 c:\bat\
set path=%path%;c:\bat\
copy c:\bat\tcmd.ini.bat c:\tcmd\tcmd.ini
copy c:\bat\tcstart.bat  c:\tcmd\tcstart.bat
copy c:\bat\alias.lst    c:\tcmd\alias.lst
```

&nbsp;

7. 💻 Certain environment variables should be defined
    - ```%MP3%```    should be set to your music repository      (i.e. ```set mp3=c:\mp3\```)
    - ```%EDITOR%``` should be set to your text editor command   (i.e. ```set editor=editplus.exe```)
    - ```%LYRICS%``` should be set to your [MiniLyrics](https://minilyrics.en.softonic.com/) repository (i.e. ```set lyrics=c:\lyrics\```)

&nbsp;

8. 📂 Filename requirements: Don’t have any audio files with these characters in them: “%^;”. 
    - Unicode characters should be fine
    - Emoji   characters should be fine, but may be risky
    - DON’T USE “```%```” (the percent character)! It’s technically not even valid, but Windows allows it. Use the unicode ```％``` if you must, but even that can be a problem! Better to just say "{percent}".
    - DON’T USE “```^```” (the [caret character](https://en.wikipedia.org/wiki/Caret))!  Sorry!  Caret is my personal command separator. Spent a lot of time making this system work with caret-filenames, and it mostly does, but with some errant error messages. In the end, I recommend not using carets in music collection filenames. I was using them to represent exponents in quirky song titles that have mathematical equations in their title, such as those by *Type O Negative* and *Man Or Astro Man?*.  It turns out that the superscript characters ¹²³⁴⁵⁶⁷⁸⁹⁰ are easier to live with... Use ```²``` instead of ```^2``` to represent the mathematical concept of “squared”. Or better yet just say “{squared}”.
    

&nbsp;

9. 📜 Recommended: As mentioned earlier, to use the “local lyric repository search” functionality, you must set an environment variable named ```LYRICS``` to point to your lyric repository.  For example, ```set LYRICS=c:\lyrics```.
This is a repository of saved lyrics, possibly from years of past [MiniLyrics](https://minilyrics.en.softonic.com/)/[EvilLyrics](https://www.evillabs.sk/evillyrics/) use.   
The structure of the repository is assumed to be subfolders for the 1ˢᵗ letter of the artist, with filenames that are “*Artist* - *Title*.txt”, for example ```c:\Lyrics\M\Metallica - Enter Sandman.txt```, with the possibility of apostrophes being substituted into underscores. 

&nbsp;

10. ☯️ Optional: For [automatic cleanup](../clean-up-AI-transcription-trash-files) of leftover AI files across an entire computer:
    - Always be running  the ```Everything``` service, which comes with TakeCommand ([TCC](https://jpsoft.com/all-downloads/all-downloads.html))
    - Use ```start-everything.bat``` or ```start EVERYTHING.EXE -startup``` to start it, if it doesn’t start automatically. 
    - ```clean-up-AI-transcription-trash-files``` is the command to clean up our trash.  Insert it into your startup/autoexec.bat equivalent and this system won’t leave any trash anywhere.

&nbsp;

11. ⚡️ Optional: For 🦙 *[WinAmp](https://forums.winamp.com/forum/winamp/winamp-discussion/306661-winamp-5-666-released-build-3516)* 🦙 integration:
    - Install the [WinampNowPlayingToFile plugin](https://github.com/Aldaviva/WinampNowPlayingToFile)
    - Configure the [WinampNowPlayingToFile plugin](https://github.com/Aldaviva/WinampNowPlayingToFile) so that the 2ⁿᵈ line of its output file is the full filename of the currently playing song. 
    - TODO add picture
    - Configure the 3ʳᵈ line to be the time elapsed. Not currently used, but may be used in the future for timed lyric display within MilkDrop3’s messaging system.
    - Here is what I use as of 2025/07/15: ```{{#if Artist}}{{Artist}} – {{/if}}{{Title}}{{#if Album}} – {{Album}}{{/if}}{{#newline}}{{Filename}}{{#newline}}elapsed={{Elapsed:m\:ss}}{{#newline}}album={{Album}}{{#newline}}year={{Year}}{{#newline}}genre={{Genre}}{{#newline}}length={{Length:m\:ss}}{{#newline}}artist={{Artist}}{{#newline}}title={{Title}}{{#newline}}filename={{Filename}}{{#newline}}comment={{Comment}}{{#newline}}end_comment=1{{#newline}}subtitle={{Subtitle}}{{#newline}}end_subtitle=1{{#newline}}composer={{Composer}}{{#newline}}```
    - This allows instant no-resource any-computer access to the location of which song file is currently playing in [WinAmp](https://forums.winamp.com/forum/winamp/winamp-discussion/306661-winamp-5-666-released-build-3516), allowing us to have commands that operate on “whatever song we are currently listening to” from any computer in the household. 🦙
      - Currently doesn’t work if the music is paused, but a future update to the WinAmpNowPlayingToFile plugin is headed down the pipeline

&nbsp;

12. Optional: To speed up the workflow, pre-download lyrics for your entire music collection before even starting to look at individual albums/songs.  
    - Start with: [predownload-all-lyrics-in-all-subfolders.bat](../predownload-all-lyrics-in-all-subfolders.bat), which runs [predownload-lyrics-here.bat](../predownload-lyrics-here.bat) on random subfolders in a random order.  
    - The predownloader marks files so that they are never retried in pre-download mode ever again. 
    - If you would like to erase those markings, run [reset-genius-search-status-for-all-audio-files.bat](../reset-genius-search-status-for-all-audio-files.bat) in a folder. 
    - If you would like to check your overall lyric/karaoke progress for your entire collection, run [report-lyric-and-subtitle-percentage-completion.bat](../report-lyric-and-subtitle-percentage-completion.bat)
    - If you would like to check how many lyric approvals you did on a certain day, run [report-lyric-approval-progress.bat](../report-lyric-approval-progress.bat)
    - If you would like to check how many transcriptions were initiated on a certain day, run [how-many-AI-transcriptions-have-run-today.bat](../how-many-AI-transcriptions-have-run-today.bat) 


</details>

-----------------------------------------------------------------------------------------------------------------------------------------------

# ⚙️ To transcribe albums/songs/playlists ⚙️

<details><summary>Click here to view the basics</summary>  
						    
From a running TCC command line, use whatever system commands you’d like from the list below.

  - For single songs/files: ```get-lyrics {filename}``` to align lyrics, ```get-karaoke {filename}``` to transcribe aligned lyrics to subtitle/karaoke file. 
    - ⚡ For Winamp Integration only: ⚡ To operate on the song currently playing in WinAmp: ```glt``` (```get-lyrics this```) to align lyrics, ```gkt``` (```get-karaoke this```) to transcribe
    - Add the ```fast``` parameter to skip the search & deletion of bad AI files.


  - For albums/folders: ```glh``` (```get-lyrics-here```) until lyrics are aligned, then ```gkh``` (```get-karaokes-here```) to transcribe.  Beforehand, optionally use ```predownload-lyrics```, ```ask-if-instrumentals``` and ```ask-if-lyricless```.

  - For playlists/filelists: ```get-lyrics playlist.m3u``` or ```get-karaoke playlist.m3u```, where *playlist.m3u* is the filename of the playlist you want to traverse


## 🌟 Main workhorse script, once things are moving along more:

### 🌟 [work.bat](../work.bat)

This script requires some personalization to use, but once set up:

Type “work karaoke” to search a playlist of your choice for 25 karaoke files to work on.
Type “work lyrics”  to search a playlist of your choice for 25 lyric   files to work on.
Type “work”         to be interactively asked as to the nature of your work.

(This framework can also be extended for other kinds of work. It helps limit the “chunk size” of how much work we bite off at a time, which can make karaoke/lyric work a bit more pleasant with shorter wait times. A value of 25 is recommended.)

</details>


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ⚙️  To transcribe entire music collections: # ⚙️ 


<details><summary>Click here to view Step ① File preparation:.</summary>  

- ① Prep files:
  - Optionally use ```LRCget``` (TODO link) to pre-download lyrics and transcriptions for your collection (if you don’t, this whole project make take 20–60% longer). BEWARE!!!!!  Every single live or remix song will match to the official version, so you want to take note of the date you run this, and delete every file that has “(live” or “Mix)” in it [or however it is you name things in your own collection]. (Possible todo: Create tool to do this named “LRCget-post-cleanup.bat”. But probably not worth the effort.)
  - Optionally use ```ydl.bat``` (TODO link) to download YouTube videos in a way that saves SRT subtitles. This is better for accuracy than using AI... But make sure those YouTube subtitles are official, and not AI-generated, because this project will produce much better results than YouTube’s crappy AI subtitles.
  - Optionally use ```global /i create-txt-lyrics-from-karaoke-files.bat``` to convert any LRC/SRTs we already have to TXT
  - Optionally use ```global /i predownload-lyrics``` to pre-download lyrics available from genius.com (if you don’t, the approving lyrics process will take 20–40% longer) 
  - Optionally use ```global /i ask-if-instrumentals``` to mark instrumentals (if you don’t, you’ll waste electricity+GPU time to get hallucinatory instrumental transcriptions)
    - for folders with too many to answer individually, you can pre-answer for all files in the folder with: ```mark-all-filenames-ADS-tag-for-as_instrumental``` and ```mark-all-filenames-ADS-tag-for-NOT-as_instrumental``` 
  - Optionally use ```global /i ask-if-lyricless``` to mark files that are in a state of “lyriclessness”, our term for unfindable lyrics/giving up on finding lyrics (if you don’t, the lyric approval process will take much longer)
    - for folders with too many to answer individually, you can pre-answer for all files in the folder with:```approve-lyriclessness.bat *``` and ```approve-lyriclessness.bat *``` 
    - When done, cleanse invalid lyrics/subtitles with ```global /i post-lyricless-clean.bat```
      - This is necessary in the event of LRCget downloading transcriptions that we later decide are invalid via bulk command, TODO: as well as to purge erroneous subtitle/lyric files associated with instrumentals
</details>

<details><summary>Click here to view Step ②: Lyric alignment.</summary>  

- ② Then, align lyrics with ```get-lyrics-here```:
  - Alignment is done by previewing the lyrics of each & every audio file, then either:
    - *approving lyrics* (they look good) 
	- ━or━
	- *approving lyriclessness* (can’t/won’t find lyrics) 
  - Alignment can be done in either ABC or random order:
    - (1) for ABC order: ```global /i glh``` 
    - (2)  random order: ```align-music-collection-lyrics.bat``` or ```sweep-random "glh" force``` which
  - Repeat alignment command until everything passes
  - Track how many were aligned on a particular day with ```report-lyric-approval-progress.bat```
   - Track progress with ```report-lyric-and-subtitle-percentage-completion```
     - it takes a snapshot of progress that lets you see your progress over time
</details>

<details><summary>Click here to view Step ③: Karaoke alignment.</summary>  

- ③ Then, transcribe audiofiles with ```get-karaoke-here``` (“gkh”).  
  - A GeForce RTX 3060 with 12G VRAM can do about 300 per day.
  - (1) transcribe in alphabetical order: ```global /i gkh```
  - (2) transcribe in    random    order: ```sweep-random "gkh" force``` 
  - Repeat transcription command until everything is transcribed
  - Ren ```gkh report``` if you want to see what percentage remains in a specific folder (like if you’ve been working a folder with hundreds of songs and are curious).
  - Track total project progress with ```report-lyric-and-subtitle-percentage-completion```, which takes a snapshot of progress that lets you see your progress over time
  - Add the ```fast``` parameter to skip the search & deletion of bad AI files.

</details>

<details><summary>Click here to view Step ④: Cleanup & reporting.</summary>  

- ④ When completely done with the entire project
  - Double-check for bad AI transcriptions by running ```delete-bad-ai-transcription``` in every folder of your collection. Do this by going ot the base folder and running the command: ```global /i call delete-bad-ai-transcription``` which runs our deleter inside each and every subfolder
  - If you have not made it part of your computer’s reboot automation scripts, manually run ```clean-up-AI-transcription-trash-files-everywhere.bat include-dot-files``` to clean up any remaining trash files and lockfiles
</details>





━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━




-----------------------------------------------------------------------------------------------------------------------------------------------


# ⚙️ SYSTEM COMMANDS ⚙️

### NOTE: Many commands have several different aliases, for convenience-of-remembering.

#### 🍀 Five main types of commands exist for this system: TODOLINKTOBELOW

  1. 💾 Filename alignment  (mark-all-filenames-as-instrumental.bat, ask-if-these-are-instrumentals.bat, etc)
  1. 🎤️ Lyric alignment  ([get-lyrics](../get-lyrics.bat),  [get-missing-lyrics](../check-for-missing-lyrics.bat), etc)
  1. 🧏 Karaoke alignment ([get-karaoke](../get-karaoke.bat), [get-karaoke-for-playlist](../get-karaoke-for-playlist.bat), etc)
  1. 🕵 Lyric   Auditing ([review-lyrics](../review-files.bat), [display-lyric-status.bat](../display-lyric-status.bat), etc)
  1. 🕵 Karaoke Auditing ([review-subtitles](../review-subtitles.bat), [check-for-missing-karaoke](../check-for-missing-karaoke.bat), etc)
  
🍀 Two lesser types of commands exist for this system:

  1. ⚡ [WinAmp](https://forums.winamp.com/forum/winamp/winamp-discussion/306661-winamp-5-666-released-build-3516) 🦙 integration commands (to work with the song that is currently playing in ⚡️Winamp⚡️) [WinAmp](https://forums.winamp.com/forum/winamp/winamp-discussion/306661-winamp-5-666-released-build-3516) 🦙)
  1. ⚙️ Subordinate commands (*under-the-hood* stuff not generally invoked directly)


🍀 Uncategorized commands:

  1. [thorough.bat](../thorough.bat) - sets/unsets the ```%LYRIC_KARAOKE_ALIGNMENT_THOROUGH_MODE%``` environment variables for thorough mode, so that no prompts auto-timeout. This is for those who want to trade thoroughness for speed.  You can’t run things overnight in thorough mode.

  1. [display-audio-file-length.bat](../display-audio-file-length.bat) - Displays the length of an audio file or of an SRT/LRC file (bonus overloaded functionality). To use the value elsewhere, add ```silent``` to run it with no output, with the return value in seconds stored in the environment variable ```%DISPLAY_AUDIO_FILE_LENGTH_OUTPUT%```. Use ```env.bat length_readable``` to inspect the environment variables containing the return value in various readable formats.

-----------------------------------------------------------------------------------------------------------------------------------------------

# 👉👉👉 *Filename Alignment* commands:

#### These commands manage the filenames to better direct our resources.


<details><summary>Click here to view command list & descriptions.</summary>  
									
### 🌟🌟🌟 SPECIAL FILENAMES THAT AFFECT BEHAVIOR 🌟🌟🌟

The following file naming conventions affect system behavior:

| File Name Contains                                   | Meaning                                            | System Behavior                        |
| --------------------------------------------         | ----------------------------                       | -------------------------------------- |
| - ```(instrumental)```, ```[instrumental]```         | file is an instrumental                            | lyrics & transcription will be skipped |
| - ```(sound effect)```, ```[sound effect]```         | file is a sound clip/effect                        | lyrics & transcription will be skipped |
| - ```(sound clip)```, ```[sound clip]```             | file is a sound clip/effect                        | lyrics & transcription will be skipped |
| - ```(chiptune)```, ```[chiptune]```                 | file is a chiptune/tracker file                    | lyrics & transcription will be skipped |
| - ```(untranscribeable)```, ```[untranscribeable]``` | transcription for this file has failed in the past |          transcription will be skipped |
| - ```(untranscribable)```, ```[untranscribable]```   | transcription for this file has failed in the past |          transcription will be skipped |
| - ```(no vocals)```, ```[no vocals]```               | transcription for this file is not necessary       |          transcription will be skipped |
| - ```(no vocal)```, ```[no vocal]```                 | transcription for this file is not necessary       |          transcription will be skipped |
| - ```(no lyrics)```, ```[no lyrics]```               | transcription for this file is not necessary       |          transcription will be skipped |

| Folder Name Contains                                 | Meaning                                                                   | System Behavior                        |
| ----------------------------------------------       | ----------------------------------------                                  | -------------------------------------- |
| - ```(instrumentals)```, ```[instrumentals]```       | folder contains only instrumentals                                        | lyrics & transcription will be skipped |
| - ```sound effects```                                | folder contains only sound clips/effects                                  | lyrics & transcription will be skipped |
| - ```(sound clips)```, ```[sound clips]```           | folder contains only sound clips/effects                                  | lyrics & transcription will be skipped |
| - ```(chiptunes)```, ```[chiptunes]```               | folder contains only chiptune/tracker files                               | lyrics & transcription will be skipped |
| - ```(untranscribeable)```, ```[untranscribeable]``` | folder contains only files for which transcription has failed in the past |          transcription will be skipped |
| - ```(untranscribable)```, ```[untranscribable]```   | folder contains only files for which transcription has failed in the past |          transcription will be skipped |
| - ```(no vocals)```, ```[no vocals]```               | transcription for this folder is not necessary                            |          transcription will be skipped |
| - ```(no vocal)```, ```[no vocal]```                 | transcription for this folder is not necessary                            |          transcription will be skipped |
| - ```(no lyrics)```, ```[no lyrics]```               | transcription for this folder is not necessary                            |          transcription will be skipped |
| - ```audiobook```                                    | folder contians only audiobook files                                      |  (only used for reporting statistics)  |


### 🌟 [preview-audio-file](../preview-audio-file.bat)

Previews an audio-file in VLC player.  
Used to preview audio files so we can mark them as instumentals or not.
If ⚡ WinAmp 🦙 Integration is enabled, pauses and unpauses ⚡ WinAmp 🦙 before/after the preview.

### 🌟 aii / [ask-if-instrumental](../ask-if-instrumental.bat)

Asks if an *INDIVIDUAL* song is an instrumental, and takes appropriate actions if it is. 
Those actions include: Previewing any TXT/LRC/SRT lyric/subtitle files and prompting the user for deletion of each one, prompting the user for deletion of any associated JSON/LOG files, and allowing the user to preview the song (with ```preview-audio-file.bat```) or enqueue the song in ⚡ WinAmp 🦙 (with my recompiled ```enqueueee.exe```) for double-checking its instrumental nature.

### 🌟 [ask-if-instrumentals](../ask-if-instrumentals) / [mark-all-filenames-as-instrumental](../mark-all-filenames-as-instrumental.bat)

```ask-if-instrumentals``` extends ```ask-if-instrumental``` to multiple songs. It cleans out bad AI transcriptions from the current folder and then *ASKS* us—one audio file at a time—if we want to mark each audio file in a folder as an instrumental (or as a sound effect).  

This process can be very annoying on a folder of 100+ songs, sooooo ```ask-if-instrumentals``` is extended to (see next entry):

### 🌟 [mark-all-filenames-ADS-tag-for-NOT-as_instrumental](../mark-all-filenames-ADS-tag-for-NOT-as_instrumental.bat) TODO

Marks *ALL* filenames in a folder with an ADS tag flagging them as NOT AN INSTRUMENTAL. 

Why would we ever do this?  To speed up the ```ask-if-instrumentals``` process on a folder that has hundreds of non-instrumental files. 

Rather than answering “N” to each file, this can pre-mark the answer so we aren’t asked in the first place. Very useful, for example, on folder trees full of vocal-less music.  You can do this on an entire folder tree via the command: ```global /i mark-all-filenames-ADS-tag-for-NOT-as_instrumental```


### 🌟 [mark-all-filenames-ADS-tag-for-as_instrumental](../mark-all-filenames-ADS-tag-for-as_instrumental.bat) 

The opposite of the last script. This marks all filenames in a folder with an ADS tag flagging them as an instrumental. 

However, this is NOT our preferred solution! 
Our preferred solution is for EACH FILENAME to have “ [instrumental]” in it!

In many situations, only the filename is examined, so if you want full precision in progress reports, and faster playlist processing (i.e. ```get-lyrics``` and ```get-karaoke``` when used on playlists), you will eventually need to rename the filename as well.

		  

### 🌟 [unmark-all-filenames-ADS-tag-for-as_instrumental](../unmark-all-filenames-ADS-tag-for-as_instrumental.bat) 

If we screwed up with either of the last 2 scripts, this removes the answers for every file in the folder.

It does this by completely removing the ```is_instrumental``` ADS tag from every audio file in the folder. This resets our “Y”/“N” answers for ```ask-if-these-are-instrumentals``` and allows us to start the process over for any filenames which have been flagged solely with ADS tags.

</details>

-----------------------------------------------------------------------------------------------------------------------------------------------

# 👉👉👉 *Lyric Alignment* commands:

#### These commands manage the lyric files which we download to improve transcription accuracy.


<details><summary>Click here to view command list & descriptions.</summary>  

### 🌠 BASIC LYRIC ALIGNMENT PROCESS (all optional): mark instrumentals ➜ mark lyriclessness ➜ predownload lyrics ➜ review/re-download/google lyrics ➜ approve lyrics

### 🌟 ❶ OPTIONAL STEP 1: [predownload-all-lyrics-in-all-subfolders.bat](../predownload-all-lyrics-in-all-subfolders.bat)

You can ```set OVERRIDE_FILE_ARTIST_TO_USE=Artist Name``` to override the artist name.

Runs an initial pass of pre-downloading lyrics from Genius **in a completely unattended fashion**, for an entire folder tree, for later review. 

  - BENEFIT 1: THIS SAVES TIME!!!!!!!!  By doing initial fetches in advance, you aren’t wasting *your* time, but *attended* time.
  - BENEFIT 2: This allows for lyric approval/disapproval to be performed when internet connectivity is down.

### 🌟 ❷ OPTIONAL STEP 2: Mark any instrumentals with [ask-if-instrumentals.bat](../ask-if-these-are-instrumentals.bat)

Particularly useful for soundtrack scores... and easy way to add “[instrumental]” to filenames so that we don’t spend AI-energy trying to transcribe files that have no lyrics.  

*Side-note:* We recommend using “[semi-instrumental]” to denote songs that have vocals but no lyrics (i.e. chorus voices being used as instruments), or songs that have a few words but no real vocals (i.e. a 3 minute electronic tracks with a spoken sample at the beginning). Semi-instrumentals will still be transcribed if caught by our scripts, but only 1 attempt will be made before they are flagged with an ADS tag to prevent infinite re-attempts.

### 🌟 ❸ OPTIONAL STEP 3: Mark any songs with unfindable lyrics as “lyricless” with ```ask-if-lyricless.bat``` [ask-if-lyricless.bat](../ask-if-these-are-lyricless.bat)

I usually skip this one except in rare instances, buuuut:

Sometimes, you just KNOW that a song’s lyrics will not be found. Ever. 

Maybe it’s:
  - a podcast, news segment, or other non-music that wouldn’t have “lyrics” posted because it’s not a song
  - songs you yourself recorded
  - a band so obscure no one listens to it
  - Something you look for lyrics for already

This will go through the songs one at a time and ask if you want to mark any as lyricless / in a state of lyriclessness, which is our internal nomenclature for “we don’t want to bother looking for lyrics anymore”. Ultimately, this is a bit faster than running into these songs one at a time later.

### 🌟 ❹ STEP 4: Get and approve lyrics with [get-lyrics {*songfile* | *playlist* / “this”} / get-lyrics-for-file {*songfile*} / get-lyrics-for-song {*songfile*} / get-lyrics-via-multiple-sources {*songfile*}](../get-lyrics-via-multiple-sources.bat):

Obtains the lyrics for a song file, a playlist, or the currently playing song. 
- transcriptions work **much** better with lyrics
- checks local sidecar files for pre-existing lyric files
- checks local lyrics/[MiniLyrics](https://minilyrics.en.softonic.com/)/EvilLyrics repository for pre-existing lyric files
- searches Genius for lyrics
- gives option to hand-edit artist/track name if lyrics are not find
- gives option to Google lyrics if all else fails
- gives an option to hand-edit lyrics after download
- can approve lyrics for later use (to concentrate your focus ONLY on lyrics, since karaoke can be generated automatically when the approved lyric file is found)
- can approve lyric*less*ness “give up” on a lyric search (to allow aforementioned automatic AI-generation to happen even though no lyrics were found, and to prevent us from searching for lyrics a 2ⁿᵈ time at a later date)
- lyrics are processed (for example, the apostrophe conversion of changing ```'``` into ```’```)
- lyrics are filtered (spam and unrelated text that follows common patterns are removed)


## OTHER LYRIC ALIGNMENT COMMANDS:

Note that you can ```set OVERRIDE_FILE_ARTIST_TO_USE=Artist Name``` to override the artist name when getting lyrics. Can be useful if it’s a cover album. For example, a Nirvana tribute album where every artist is not Nirvana definitely uses Nirvana’s lyrics, so setting the value to ```Nirvana``` would be an appropriate way to speed up the process.


### 🌟 [get-lyrics-for-currently-playing-song](../get-lyrics-for-currently-playing-song.bat):

If 🦙 *[WinAmp](https://forums.winamp.com/forum/winamp/winamp-discussion/306661-winamp-5-666-released-build-3516)* 🦙 integration is enabled, get lyrics for *the song currently being played*.


### 🌟 glh / [get-missing-lyrics-here.bat](../check-for-missing-lyrics-here.bat) / [get-missing-lyrics](../check-for-missing-lyrics-here.bat) / [gmlh](../check-for-missing-lyrics-here.bat) / [gml](../check-for-missing-lyrics-here.bat):

Gets lyrics for all the files *in the current folder* that do not have *approved* lyric files.
(Uses [check-for-missing-lyrics.bat](../check-for-missing-lyrics.bat).)

Use [get-lyrics-here-in-alphabetical-order.bat](../get-lyrics-here-in-alphabetical-order.bat) to do it in alphabetical order instead of random order.



### 🌟 [get-lyrics-for-playlist.bat](../get-lyrics-for-playlist.bat) {limit}:

Gets lyrics for all the files *in a playlist* that do not have *approved* lyric files, in random order to avoid alphabetical bias. Can specify an optional *limit*  so that it stops after finding a few.   (Uses [check-for-missing-lyrics.bat](../check-for-missing-lyrics.bat))


### 🌟 cmt / gmt / [create-txt-lyrics-from-karaoke-files.bat](../BAT-and-UTIL-files-1create-txt-lyrics-from-karaoke-files.bat.bat):


In the current folder, convert all karaoke sidecar files into text sidecar files (unless they already exist).
That is: If an MP3/FLAC has a corresponding LRC/SRT but not TXT version, convert the LRC/SRT to TXT.

It is good to prep your entire collection with this, by running it in every folder of your music collection. Do this by going to the base folder of your music collection and running: ```global /i create-txt-lyrics-from-karaoke-files.bat```


### [review-all-lyrics-in-all-subfolders.bat](../review-all-lyrics-in-all-subfolders.bat)

Randomly walks a folder tree, obtaining/reviewing lyrics, with the intent of approving lyrics for later automatic AI transcription.  
(It is reviewing lyrics in the case of predownload-all-lyrics-in-all-subfolders.bat having already downloaded some lyrics. And it is obtaining lyrics in the case of those lyrics not existing or not being sufficient.)

### [post-lyricless-clean.bat] (../delete-sidecar-lyric-and-subtitle-files-for-audiofiles-in-lyricless-approved-state.bat)

Utility to delete lyric/subtitle sidecar files that should no longer exist at this point.

These include lyric/subtitle files of audio files whose lyric*less*ness status is approved, but whose lyrics are not (removed with [delete-sidecar-lyric-and-subtitle-files-for-audiofiles-in-lyricless-approved-state](../delete-sidecar-lyric-and-subtitle-files-for-audiofiles-in-lyricless-approved-state.bat)), 
and lyric/subtitle files of audio files that are instrumentals (removed with [delete-sidecar-lyric-and-subtitle-files-for-audiofiles-that-are-instrumentals](../delete-sidecar-lyric-and-subtitle-files-for-audiofiles-that-are-instrumentals.bat))

Longer explanation: When this system marks a song as lyriclessness (aka “lyrics unfindeable, proceed with AI-only transcription”) it deletes any existing sidecar & lyric files. However, it is still possible for invalid sidecar lyric/subtitle files to exist for songs marked lyricless, if an external utility like LRCget was used to downloaded incorrect LRC/TXT files (for example, attaching a LRC file for the wrong song, or a studio version’s LRC to a live version of the song). Thus, this tool grew out of necessity. Instrumental files need the same treatment too.


### 🌟 Lyric-related Reports:

If you would like to check your overall lyric/karaoke progress as a percentage of your whole music collection, run [report-lyric-and-subtitle-percentage-completion.bat](../report-lyric-and-subtitle-percentage-completion.bat) from the root folder of your music collection. It generates a log file (```lyric-subtitle-compliance.log```) that allows you to track your progress over time.

If you would like to check how many lyric approvals you did on a certain day, just for that sense of accomplishment, run [report-lyric-approval-progress.bat](../report-lyric-approval-progress.bat), which will tell you how many lyric[less] approvals you did on a specific calendar day.

</details>

-----------------------------------------------------------------------------------------------------------------------------------------------


# 👉👉👉 *Karaoke Alignment* commands:

#### These commands create & repair the karaoke files that are the primary goal of this project! 🎈 

<details><summary>Click here to view the karaoke generation command lists & descriptions.</summary>  

### 🌟 THE 1ˢᵗ BIG ONE: create-srt {*songfile*} / [create-srt-from-file {*songfile*}](../create-srt-from-file.bat):

**Create karaoke for one audio file.**
Performs the AI transcription process for a single song file.
Run without parameters to see various options, as the list here is not guaranteed to be synchronized with the most up-to-date options. Options include:

    - ```         force``` — generate it even if it already exists, or is an instrumental (some instrumentals have samples or backing choruses you might want displayed)
    - ```            ai``` — skips  the   lyrics   component, and transcribes file only with AI
    - ```LyricsApproved``` — don’t skip the lyrics component, and transcribes file with existing lyrics *even if not pre-approved* [i.e. consider them approved regardless]
    - ```          fast``` — shortens prompt timer lengths [to get more done overnight]
    - ```          last``` — retry the last transcription again [in case of error]
    - ```       cleanup``` — just clean up the temp files [in case of error]
    - ```PromptAnalysis``` — instead of encoding, simply log the prompt to the log file for later analysis. Great way to test our lyric postprocessor system-wide proper to doing system-wide transcription.

One may also set the environment variables %OVERRIDE_VAD_THRESHOLD% and %OVERRIDE_LANGUAGE% to override the %DEFAULT_VAD_THRESHOLD% and %DEFAULT_LANGUAGE% values in the config section of create-srt.

### 🌟 srtthis / [create-srt-file-for-currently-playing-song.bat](../create-srt-file-for-currently-playing-song.bat):

If 🦙 *[WinAmp](https://forums.winamp.com/forum/winamp/winamp-discussion/306661-winamp-5-666-released-build-3516)* 🦙 integration is enabled, creates karaoke file for *the song currently being played*.
If lyrics (or lyriclessness) are pre-approved, creation is automatic.


### 🌟 THE 2ⁿᵈ BIG ONE: cmk / gmk / cmkf / [create-missing-karaoke-files / create-the-missing-karaokes-here](../create-the-missing-karaokes-here.bat):

Create karaoke files for **all songs** *in the current folder* that do not have them
Songs that have pre-approved lyrics go through the process automatically.
To do for an entire folder tree, preceed with ```global /i ```



### 🌟 [get-lrc](../get-lrc) {audio_file} / ```get-lyrics quick_lrc``` mode:

Uses *SyncedLyrics* to quickly gather *just* the LRC file that belongs with an audio file.  
*SyncedLyrics* uses MULTIPLE sources, which can then save us the trouble of having to make our own SRT/LRC files, which might be less accurate anyway.

Downloads are compared to existing files *and* to each other to prevent duplicates.
Downloads are checked to ensure they are actually LRC, and if they are not, treated as TXT.
Downloads and audio file are checked for duration, and user is warned if subtitles are longer in duration than the audio file.
Downloads are compared to existing files (including visual representation stripe)



### 🌟 [get-all-LRCs](../get-all-LRCs.bat) / [get-LRCs](../get-LRCs.bat):

Same as above, but for all audio files in the folder.
Leaves breadcrumb files (```.GetAllLRCsRunHereAlready```) in folders to mark them as done, to prevent wasting time re-running in the same folder more than once.
Use the ```force``` / ```--force``` parameter to run it on a folder that’s already been marked with the breadcrumb.
To easily delete every breadcrumb file on your computer, go into ```clean-up-AI-transcription-trash-files-everywhere.bat``` and uncomment/add ```gosub DeleteEverywhere .GetAllLRCsRunHereAlready``` and run.

### 🌟 [create-srt-from-playlist.bat](../create-srt-from-playlist) (called via ```get-karaoke *{playlist}*```):

Create karaoke files for **all songs** *in a playlist* that do not have them — Traverses a playlist, running ```create-SRT``` on every file in the playlist. Files are run in random order, to prevent alphabetical bias, and transcriptions are done automatically if lyrics are pre-approved (or if lyriclessness is pre-approved).


### 🌟 [create-SRT-without-lyrics-or-voice-detection-for-an-entire-folder-tree.bat](../create-SRT-without-lyrics-or-voice-detection-for-an-entire-folder-tree.bat):

Rarely used side-utility: Creates karaoke files for **all songs** in a *folder tree* without using lyric files or voice detection (VAD). This is useful for large repositories of sound clips, small samples from movies, or audiobooks..... Where you just want to get a lot done without the extra overhead of operating the Lyric Alignment system, andwithout the extra time delay of loading the VAD (voice detection) model. This will get a LOT done FAST, but it will be sloppy.

</details>


<details><summary>Click here to view the karaoke repair command lists & descriptions.</summary>  
										 
## 🌟 Karaoke Repair

### 🌟 [WhisperTimeSync.bat](../WhisperTimeSync.bat) [{bad_subtitle_file} {good_text_file} {optional_audio_file}] or [{audio_file to imply subtitles and lyrics from the filename of}] / wtsthis.bat / wtst.bat:

Use the incorporated instance of the [WhisperTimeSync](https://github.com/EtienneAb3d/WhisperTimeSync) project to fix mis-transcriptions in the SRT file by using the TXT lyrics as an official point of truth.  This is tricky, and the original project is fraught with implementation issues.  This script guides us through the steps to avoid those issues, including giving an option to directly enqueue songs into ⚡ WinAmp 🦙 to preview how the lyrics are being displayed in [MiniLyrics](https://minilyrics.en.softonic.com/), comparing the final timestamps of both files, and opening the before and after in our text editor so that we can manually review the re-sync’ed lyrics.  

Final review includes using the special modes incorporated into the [print_with_columns.py](../print_with_columns.py) created specifically for comparing old subtitles to new subtitles. These include a mode where the screen alternates between the before/after subtitles, and a mode where the timestamps are synced in a 2-column side-by-side display of the before/after subtitles. That way we can be dang sure the [WhisperTimeSync](https://github.com/EtienneAb3d/WhisperTimeSync)hronized new subtitles are actuallyb etter than the old ones, which are backed up to the current folder prior to being replaced.


### 🌟 [WhisperTimeSync-currently-playing-song.bat](../WhisperTimeSync-currently-playing-song.bat):

If ⚡ WinAmp 🦙 Integration is enabled, runs [WhisperTimeSync.bat](../WhisperTimeSync.bat) on the currently-playing song.


### 🌟 [whispertimesync-postprocessor.py](../whispertimesync-postprocessor.py):

A postprocessor for the subtitles generated by [WhisperTimeSync](https://github.com/EtienneAb3d/WhisperTimeSync).
For instance, if repeated choruses at the end of the song are not present in a TXT file, then [WhisperTimeSync](https://github.com/EtienneAb3d/WhisperTimeSync)’s output won’t include those, even though they would be picked up by WhisperAI itself.  This detects that situation and adds the missing tail from the old file to the new file, saving it in place (after backing up the original).


### 🌟 [srt_comparator.py](../srt_comparator.py):

Compares 2 (or more) SRT files in chronological order.
Each timestamp encountered is shown, with the version of subtitles from each compared file in its own color.

Suppressing identical lines with the ```--hide-identical-lines``` option reduces the output to _just_ the different lines, which provides a functional audit of just what it was that [WhisperTimeSync-helper.bat](../WhisperTimeSync-helper.bat) fixed or did not fix.

We also use the ```--low-res-timestamps``` option to ignore small (less than 1 second) timestmap differences.

The ```---show-filenames``` / ```--key``` option can also be used to clarify confusion.



### 🌟 [visual-comparison.bat](../visual-comparison.bat):

Compares 2 (or more) SRT files visually.

The 2 files are rendered in column view, then redrawn over each other.

It gets ugly if the 2 columns are different widths, but this often lets you visually see what was changed in a very quick way.

</details>


## 🌟 Karaoke-related Reports

<details><summary>Click here to view our 2 report scripts.</summary>  

If you would like to check your overall lyric/karaoke progress as a percentage of your whole music collection, run [report-lyric-and-subtitle-percentage-completion.bat](../report-lyric-and-subtitle-percentage-completion.bat) from the root folder of your music collection. It generates a log file (```lyric-subtitle-compliance.log```) that allows you to track your progress over time.

If you would like to check how many transcriptions were initiated on a certain day, run [how-many-AI-transcriptions-have-run-today.bat](../how-many-AI-transcriptions-have-run-today.bat) 

</details>



## 🌟 Sample specific “task-runner” scripts:

<details><summary>Click here to view 2 sample scripts for more specific alignment work</summary>  

### 🌟 [work-incoming-karaoke.bat](../work-incoming-karaoke.bat)

Goes to my incoming folder and works all the folders in random order, generating karaoke in THOROUGH mode, becuase I do care to double-check these and don’t want them to run while asleep.  This is how I work on new/incoming music.

### 🌟 [work-nonmusic-karaoke.bat](../work-nonmusic-karaoke.bat)

Goes to my NON-MUSIC/audiobooks folder and works all the folders in random order, generating karaoke in NON-THOROUGH mode, because I don’t care to double-check these and want them to run while asleep.  This is how I transcribed all my audiobooks in my sleep.

</details>


-----------------------------------------------------------------------------------------------------------------------------------------------

# 👉👉👉 *Auditing Commands* for *Lyrics*:

#### These commands find & obtain missing lyric files.

<details><summary>Click here to view command list & descriptions.</summary>  

### 🌟 [review-lyrics / review-all-TXTs / review-TXTs.bat](../review-files.bat):

Reviews all lyric files in current folder, using ```print-with-columns``` to reduce scrolling up.

To add visual representation stripe, use the “-st”, “-stU”, “stL”, and “-stB” parameters for default stripe, upper stripe, lower stripe, and both stripes.

To keep the timestamps in an SRT file visible in the final review, use the “```--KeepTimestamps```” parameter. Double-dashed to set it apart from parameter that are ultimately passed on to print-with-columns.



### 🌟 dlsa / dls / [display-lyric-status.bat](../display-lyric-status.bat) {*lyric_filename* or “all” or “audio” or “*”}:

Displays the lyric/lyriclessness status (approved, unapproved, or unset) for all lyric/audio files in current folder. 

To have this happen automatically when changing into a folder, ```alias cd=call cd-alias.bat```,  then create ```autorun.bat``` in the *base folder* of your music collection, containing the command:
```@if exist *.txt (call display-lyric-status)```
or
```@if exist *.txt;*.mp3;*.flac;*.wav (call display-lyric-status all)```
![image](https://github.com/user-attachments/assets/350dbe7c-5649-40ca-a355-ec73a8e34030)
![image](https://github.com/user-attachments/assets/0ccdebd6-7e26-4a2b-91ee-c3e0cfe9f147)


### 🌟 cfml / cmlf / [check-for-missing-lyrics](../check-for-missing-lyrics.bat):

Displays a list of files in the *current folder* which are missing *approved lyric* files 

(Does not display files that have been pre-approved to be lyricless aka “lyriclessness approved” state)


### 🌟 Lyric Auditor: cpfml / cpmlf / [check-playlist-for-missing-lyrics](../get-playlist-for-missing-lyrics.bat):

Displays a list of files in a *playlist* which are missing *approved lyric* files.

Does not display songs that have been pre-approved to be in “lyriclessness” state. These are songs we’ve given up our search on. (todo: verify through testing that pre-approved lyricless songs do not show up here)

![image](https://github.com/user-attachments/assets/42fb6e4e-2cea-48e1-bbc8-499454c201ae)

### 🌟 [display-lyriclessness-status.bat](../display-lyriclessness-status.bat):

Displays the “lyric*lessness*” status of a songfile. A song is in “lyriclessness approved” state if we have officially given up on our lyric search. The “lyriclessness approved” state allows the AI to transcribe our songs *without* a text file prompt, when running in automatic mode. 

In other words: For our transcribe-while-sleeping process to work with songs we can’t find lyrics for, we need to approve the fact that there will be no lyrics. This displays whether that has been done or not.


### 🌟 [display-lyriclessness-status-for-file.bat](../display-lyriclessness-status-for-file.bat):

Displays the lyric*lessness* status of a song.  This is to track whether we’ve officially given up on our lyric search for a song.  


### 🌟 [convert-playlist-to-only-songs-that-do-not-have-karaoke-but-do-have-lyrics.bat](../convert-playlist-to-only-songs-that-do-not-have-karaoke-but-do-have-lyrics.bat):

Not very useful to the end-user, but this does what the title says. Converts a playlist to only songs that have karaoke (LRC/SRT) sidecar files, but which do not have lyric (TXT) sidecar files. The main purpose for this is to be able to find testdata for [srt2txt.bat](../srt2txt.bat) / [srt2txt.py](../srt2txt.py) and [lrc2txt.bat](../lrc2txt.bat)/ [lrc2txt.py](../lrc2txt.py)


### 🌟 Lyric-related Reports:

If you would like to check your overall lyric/karaoke progress as a percentage of your whole music collection, run [report-lyric-and-subtitle-percentage-completion.bat](../report-lyric-and-subtitle-percentage-completion.bat) from the root folder of your music collection. It generates a log file (```lyric-subtitle-compliance.log```) that allows you to track your progress over time.
<img width="844" height="1645" alt="image" src="https://github.com/user-attachments/assets/8b7aa3d2-934f-4f98-bcaa-ce35ba5ba3e5" />

If you would like to check how many lyric approvals you did on a certain day, just for that sense of accomplishment, run [report-lyric-approval-progress.bat](../report-lyric-approval-progress.bat), which will tell you how many lyric[less] approvals you did on a specific calendar day.


</details>

-----------------------------------------------------------------------------------------------------------------------------------------------

# 👉👉👉 *Auditing Commands* for *Karaoke*:

#### These commands find & obtain missing karaoke files.

<details><summary>Click here to view command list & descriptions.</summary>  

### 🌟 [delete-bad-ai-transcriptions](../delete-bad-ai-transcriptions):

This searches for bad karaoke transriptions in the current folder & deletes them with a configurable prompting level. 

This is automatically run at various points (such as before and/or after creating karaoke files), and should also be run on the entire music collection when the project is completed. 
<img width="1521" height="138" alt="image" src="https://github.com/user-attachments/assets/3d00fab8-48b4-4c28-8977-8c3a7e104222" />

Bad karaoke transcriptions include:
  1. Files that contain certain commonly-hallucinated-by-AI phrases can be consistently serached for to find bad transcriptions. “And now we’re back” is one of them, but no fewer than 5 different hallucations are regularly searched for
  2. Either LRCget or LyricsGenius likes to put Chris DeBurg’s “Lady In Red” and Voivoid’s “Black City” as the LRC file for a TON of songs—and I don’t know why. It became a systemic project issue. This will flag these errors as well, unless the filename has “Lady In Red” or “Black City” in it, in which case it’s the right song and the check is skipped.
  3. TODO anything else?

### 🌟 [bad-transcription-hunter.bat](../bad-transcription-hunter.bat):

This searches an entire folder tree (in random order) for bad karaoke transcriptions.

#### These commands find & obtain missing karaoke files.



### 🌟 [review-SRTs-and-TXTs.bat / review-transcriptions.bat](../review-SRTs-and-TXTs.bat):

Checks each subtitle file against its sidecar LRC/TXT files, using ```print-with-columns``` to eliminate most scrolling up, pausing to ask if we want to delete lyrics/SRT/LRC, approve/disapprove lyrics/SRT, play, or rename files.
<img width="2988" height="1579" alt="image" src="https://github.com/user-attachments/assets/e63558dc-e8f7-418e-a18f-c7578b6d686d" />

### 🌟 [review-subtitles.bat / review-all-SRTs / review-all-subtitles / review-SRTs / review-LRCs](../review-subtitles.bat):

Reviews all karaoke files in current folder, using ```print-with-columns``` to eliminate most scrolling up.
Just spits out all the SRT files without pausing in between.

![image](https://github.com/user-attachments/assets/9b579cf2-ca93-4684-aec5-35df8c793143)
<img width="1779" height="1586" alt="image" src="https://github.com/user-attachments/assets/5da5ac3b-cbed-457a-8a09-707c01d067e4" />

### 🌟 cfmk / [check-for-missing-karaoke](../check-for-missing-karaoke.bat):

Displays a list of files in the *current folder* which are missing *karaoke* files, defaulting to use ```these.m3u``` is the playlist to check.
Pass a playlist filename to use a playlist other than ```these.m3u```
Add the ```fast``` parameter to skip the search & deletion of bad AI files.

![image](https://github.com/user-attachments/assets/61e1f155-a798-4668-945a-7d7dd2ac06dc)


### 🌟 convert-playlist-to-only-songs-that-do-not-have-karaoke.bat {playlist} [convert-playlist-to-only-song-that-do-not-have-karaoke.bat](../convert-playlist-to-only-song-that-do-not-have-karaoke.bat):

Creates a new playlist consisting of all the files in the original playlist that do not have karaoke sidecar files.
It then asks if we want to start getting karaoke or lyrics for that playlist.

### 🌟 convert-playlist-to-only-songs-that-do-not-have-lyrics.bat {playlist} [convert-playlist-to-only-song-that-do-not-have-lyrics.bat](../convert-playlist-to-only-song-that-do-not-have-lyrics.bat):

Creates a new playlist consisting of all the files in the original playlist that do not have lyric sidecar files.
Asks if we want to start getting lyrics for that playlist.


### 🌟 subtitle-integrity-checker.bat {SRT file} [subtitle-integrity-checker.bat](../subtitle-integrity-checker.bat):

Checks a SRT file for overlapping timestamps, and zero-time timestamps, and displays results in a graph.
Used to further reconcile *WhisperTimeSync*-reconciled SRT files.
(Good lyrics ➜ Bad SRT ➜ WhisperTimeSync fixes SRT based on lyrics ➜ subtitle-integrity-checker looks for things WhisperTimeSync may have screwed up (since it does).



### 🌟 Karaoke-related Reports

If you would like to check your overall lyric/karaoke progress as a percentage of your whole music collection, run [report-lyric-and-subtitle-percentage-completion.bat](../report-lyric-and-subtitle-percentage-completion.bat) from the root folder of your music collection. It generates a log file (```lyric-subtitle-compliance.log```) that allows you to track your progress over time.

If you would like to check how many transcriptions were initiated on a certain day, run [how-many-AI-transcriptions-have-run-today.bat](../how-many-AI-transcriptions-have-run-today.bat) 
<img width="1024" height="321" alt="image" src="https://github.com/user-attachments/assets/b86bdaf9-4f79-4dcd-9992-e8daf100a219" />



</details>

-----------------------------------------------------------------------------------------------------------------------------------------------


# 👉👉👉 ⚡️ *[WinAmp](https://forums.winamp.com/forum/winamp/winamp-discussion/306661-winamp-5-666-released-build-3516) 🦙 Integration* Commands:

#### These commands allows us to operate on “the song we are currently listening to” rather than a specific file or playlist.

<details><summary>Click here to view command list & descriptions.</summary>  

### 🌟 [get-lyrics-for-currently-playing-song ](../get-lyrics-for-currently-playing-song.bat):

Get lyrics for *the song currently being played* in ⚡️ [WinAmp](https://forums.winamp.com/forum/winamp/winamp-discussion/306661-winamp-5-666-released-build-3516) 🦙.


### 🌟 srtthis / [create-srt-file-for-currently-playing-song.bat](../create-srt-file-for-currently-playing-song.bat):

Creates karaoke for *the song currently being played* in ⚡️ [WinAmp](https://forums.winamp.com/forum/winamp/winamp-discussion/306661-winamp-5-666-released-build-3516) 🦙.


### 🌟 Karaoke insertion fudger / MiniLyrics fixer - [eccsrt2lrc2clip.bat](../eccsrt2lrc2clip.bat):

In certain very rare situations, [MiniLyrics](https://minilyrics.en.softonic.com/) does not display new karaoke we create. This is because [MiniLyrics](https://minilyrics.en.softonic.com/) primarily uses LRC instead of SRT, so if an LRC was already there, and you create an SRT, it tends to ignore the SRT,e ven if you delete the LRC. 

When this happens, the SRT must be converted to LRC, copied to the clipboard, and pasted into the [MiniLyrics](https://minilyrics.en.softonic.com/) lyric window manually, so that the data goes wherever it is [MiniLyrics](https://minilyrics.en.softonic.com/) is storing it (we don’t know! It’s been out of development for 10+ yrs and is am ysterious product). 

This script handles that by detecting the current song playing, converting it’s SRT to LRC, copying the SRT’s contents to the clipboard, and automatically opening [MiniLyrics](https://minilyrics.en.softonic.com/)’s lyric editor window. 

All the user has to do is paste, then save.

</details>

-----------------------------------------------------------------------------------------------------------------------------------------------

# 👉👉 *Under-The-Hood*: Project-Specific Utility Commands 

Other important commands specific to this project.

<details><summary>Click here to view command list & descriptions.</summary>  

### 🌟 Sidecar-File Auditor [CheckAFilelistForFilesMissingSidecarFilesOfTheProvidedExtension](../check_a_filelist_for_files_missing_sidecar_files_of_the_provided_extensions.py):

A generalized utility that, in our case, is being used to process a playlist to create a new playlist consisting of *ONLY* the songs that do not have karaoke files. This helps us focus our efforts.

EXAMPLE:
```
check_a_filelist_for_files_missing_sidecar_files_of_the_provided_extensions.py PlayList.m3u *.srt;*.lrc ``CreateSRTFileWrite
```
^^^ This example goes through the file ```PlayList.m3u```, checks for all files that do not have karaoke files (i.e. no ```*.srt``` or ```*.lrc``` sidecar file), creates a ```PlayList-without lrc srt.m3u``` consisting of those files.  Bbecause the `````CreateSRTFileWrite``` option was used, it also generates a script to actually create the missing karaoke files.  The ``GetLyricsFileWrite``` option can instead be used to *ONLY* obataining lyrics, and save the karaoke generation for later.

![image](https://github.com/user-attachments/assets/5b368467-b23b-4039-b3df-c4dc85e90ad5)


### 🌟 [approve-lyrics / approve-lyric-file {lyric_file}](../approve-lyric-file.bat) / [disapprove-lyrics / disapprove-lyric-file {lyric_file}](../disapprove-lyric-file.bat):

Marks lyric file with approval/disapproval so that we can pre-approve lyric files in advance of transcription process. Uses [Alternate Data Streams](https://superuser.com/questions/186627/anybody-have-a-legitimate-use-for-alternate-data-streams-in-ntfs) to store approval tags in a database-less, file-less way.

![image](https://github.com/user-attachments/assets/c48e2ed3-c1fb-4760-8ba8-c9accf691178)

### 🌟 [approve-subtitles / approve-subtitle-file {subtitle_file}](../approve-subtitle-file.bat) / [disapprove-subtitles / disapprove-subtitle-file {subtitle_file}](../disapprove-subtitle-file.bat):

Same as above but for karaoke files. Not particularly used by this system.

### 🌟 [approve-lyriclessness / approve-lyriclessness-for-file {audio_file}](../approve-lyriclessness-for-file.bat) / [disapprove-lyriclessness / approve-lyriclessness-for-file {audio_file}](../approve-lyriclessness-for-file.bat) {force | all | ask | wildcard | filename}:

**Remember:** The only way to batch transcribe in an unattended fashion (aka “encode while you sleep”) is to pre-approve lyric files.

But what if lyrics can’t be found and we still want to proceed with batch encode?  

In that case, we must pre-approve that the *song* is *lyricless* — in a state of “**lyriclessness**” — because there is no lyric file to approve.

This script marks a *song file* with *lyriclessness* approval/disapproval so that we can do that.

Invoke it with ```approve-lyriclessness ask``` if you want it to ask individually for each file (along with a chance for one-key listening preview and one-key renaming/marking file as an instrumental, which helps with our stats).  This can be a great first step for processing a folder of files.  We can also use ```ask-if-instrumentals.bat``` to similar effect, for marking files that are instrumentals [which will make our transcriber script ignore them!]


&nbsp;

### 🌟 converter: [srt2lrc.py](../srt2lrc.py):

A *batch* SRT-file to LRC-file converter that’s better than all the other ones on the internet. Used by [eccsrt2lrc2clip.bat](../eccsrt2lrc2clip.bat) in the very rare event of [MiniLyrics](https://minilyrics.en.softonic.com/) not properly importing an ```SRT``` file.

### 🌟 converter: [srt2txt.bat](../srt2txt.bat) / [srt2txt.py](../srt2txt.py):

A ```SRT``` to ```TXT``` coverter. Pass filename to convert single file or ```all``` to convert all SRT files into TXT. Used when we already have SRT files for a song (say, from a download), but don’t have a TXT version of the lyrics.  One is automatically created to ensure file uniformity. Configurable thresholds for joining subtitle lines together into 1 text line (if they are really close together in time, i.e. under ≈0.5 seconds), or for adding a blank line between lyrics (if the subtitles are really far in time from each other, i.e. over ≈3 seconds)

### 🌟 converter: [lrc2txt.bat](../lrc2txt.bat)/ [lrc2txt.py](../lrc2txt.py):

A ```LRC``` to ```TXT``` converter. Pass filename to convert single file or ```all``` to convert all LRC files into TXT. Used when we already have LRC files for a song (say, from a download), but don’t have a TXT version of the lyrics. One is automatically created to ensure file uniformity. Estimates where line breaks should occur based im time thresholds (currently .65s=new line, 4.75s=blank line).


</details>

-----------------------------------------------------------------------------------------------------------------------------------------------

# 👉👉 *Under-The-Hood*: Non-Project-Specific utility commands:

<details><summary>Click here to view command list & descriptions.</summary>  

### 🌟 [print_with_columns.py](../print_with_columns.py), called by [print-with-columns.bat](../print-with-columns.bat)/[newspaper.bat](../newspaper.bat):

📰 Newspaper-style column-based file viewer 📰 —— Displays text in column (“newspaper”) format with columns to use as little vertical space as possible.

A useful replacement for the ```type```/```cat``` command, created to review lyrics & karaoke for this project without the *constant* interruption of having to scroll up! It was *constant*.

Used by ([review-file.bat](../review-file.bat)/([review-files.bat](../review-files.bat) which do additional things like optionally strip off the timestamps of a subtitle file for prettier viewing.

This one was a surprising amount of work.

&nbsp;
</details>



### 🌟 [google.py](../google.py):

Invokes a google search in primary browser, all while properly preserving the quotes given at the command line. 
Way harder to do than it should be.

### 🌟 [insert-before-each-line.py](../insert-before-each-line.pl) / [insert-after-each-line.py](../insert-after-each-line.pl):

Inserts text before/after each line of STDIN. Used for script generation.   
Put ```{{{{QUOTE}}}}``` in the argument to turn it into a quote mark in the final output.
![image](https://github.com/user-attachments/assets/e3423665-783c-45e2-b275-7837d93d5ad9)

The Perl version is 30% faster than Python version, but less reliable, especially with emoji & weirder file encodings.

### 🌟 [lyric-postprocessor.pl](../lyric-postprocessor.pl):

Downloaded lyrics postprocessor. Cleans up non-lyric trash that inevitably creeps into these.

Add ```-1``` option to turn on  squishing of lyrics into a single line for use in AI prompts
Add ```-0``` option to turn off squishing of lyrics into a single line for use in AI prompts [DEFAULT]
Add ```-A``` option to display allllll the lines,  not just the unique lines [DEFAULT]
Add ```-U``` option to display only unique lines, instead of using all lines
Add ```-L``` option to turn on  lyric-specific processing [DEFAULT]
Add ```-N``` option to turn off lyric-specific processing 
Add ```-N``` option to turn off adding a character to the end of each line 
Add ```-L``` option to turn on  adding a character to the end of each line [DEFAULT]***

***[character is “.” for this system, to manipulate WhisperAI’s ```--sentence``` parameter into breaking subtitles at lyrical lines and to compensate for lyrics not usually being punctuated]

</details>

-----------------------------------------------------------------------------------------------------------------------------------------------


# 👉👉 *Under-The-Hood*: Lyric/Subtitle-System-Specific Pre/Post-Processor/Fetch Utility Commands:

Preprocessors / Postprocessors developed for this project.

<details><summary>Click here to view command list & descriptions.</summary>  

### 🌟 [get-lyrics-with-lyricsgenius-json-processor.pl](../get-lyrics-with-lyricsgenius-json-processor.pl):

The lyric downloader we use for Genius saves lyrics as a ```JSON file```. This extracts the actual lyrics from that file, with minimal processing.

### 🌟 [lyric-postprocessor.pl](../lyric-postprocessor.pl):

A lyric postprocessor that removes tons of junk from downloaded lyrics, only shows unique lines (to help fit into WhisperAI’s 224-token prompt limit), and smushes all the lyrics into a single line (for use as a command line option). Started as a spiritual fork of ``uniq``` that doesn’t require file sorting (to avoid using up the 224 max tokens for WhisperAI with repeating lyrics), and grew into full-fledged lyric preprocessor that does much lyric massaging. Including putting a period at the end of each line, which is later removed by our subtitle postprocessor.


### 🌟 [subtitle-postprocessor.pl](../subtitle-postprocessor.pl):

The final subtitle postprocessor—originally called ```remove-period-at-ends-of-lines.pl```—which removes periods from end of each line in a subtitle. It preserves the periods at the end of the line if the are for common abbreviations like “Mr.”, “Dr.”, “approx.”, etc

**Rationale:** We add “invisible” periods to the end of each line of lyrics, so that WhisperAI’s ```--sentence``` option is influenced by where lyric posters post the line breaks in their lyrics. It absolutely helped. A lot. Hours were spent determiing this and, and it was obvious from the first [of many] tests.   We then remove these periods (making them “invisible”) afterward, because they are ugly and often not even gramatically correct — just correct for *timing* purposes.  

This also also has some extra karaoke postprocessing functionality slipped in:
    - de-censoring some curse words that WhisperAI censors (suppress this with ```--leave-censorship``` or ```-L```)
    - removing any line that is a common WhisperAI hallucination

### 🌟 [fix-subtitles-for-currently-playing-song.bat](../fix-subtitles-for-currently-playing-song.bat) [or ```fts``` for “fix these subtitles”]:

If ⚡ WinAmp 🦙 Integration is enabled, runs [subtitle-postprocessor.pl](../subtitle-postprocessor.pl) on the currently playing song.



### 🌟 [lrc-postprocessor.pl](../lrc-postprocessor.pl):

Postprocessor for [downloaded] LRC files.


</details>

-----------------------------------------------------------------------------------------------------------------------------------------------

# 👉👉 *Under-The-Hood*: Existing commands also used by this system:

## Various commands that were already a part of my “Clairevironment”:

### Click to expand:

<details><summary>🌈Psychedelic color-cycler with 👂WhisperAI-specific postprocessing</summary>  

### 🌟 [copy-move-post.py](../copy-move-post.py):

Inspired by ```glow.com``` in the 1980s DOS era, a cosmetic postprocessor which employs ANSI color-cycling to inbue a psychedelic effect onto text by cycling the colors of the primary text color through the visible spectrum. Originally written to combat “hangxiety” — anxiety over whether your code has hung — by affecting screenoutput without actually generating any “real” output. Then enhanced to postprocess the output to the ```move``` and ```copy``` commands with emoji, color, italics, double-height text for summaries, and more. Finally, enhanced again with explicit postprocessing for WhisperAI’s transcription output.

Uses my [claire_console.py](../clairecjs_utils/claire_console.py) library to achieve the color-cycling.

&nbsp;
</details>





<details><summary>⚡ WinAmp 🦙 integration to operate on “song currently playing”</summary>  

### 🌟 [go-to-currently-playing-song-dir.bat](../go-to-currently-playing-song-dir.bat):

Used in this project for ⚡ [WinAmp](https://forums.winamp.com/forum/winamp/winamp-discussion/306661-winamp-5-666-released-build-3516) 🦙 integration only. Changes current folder to same folder that the song we are listening to is in.  (The change-folder script is actually generated by [edit-currently-playing-attrib.bat](../edit-currently-playing-attrib.bat))

&nbsp;
### 🌟 [edit-currently-playing-attrib-helper.pl](../edit-currently-playing-attrib-helper.pl):

Used in this project for 🦙 *[WinAmp](https://forums.winamp.com/forum/winamp/winamp-discussion/306661-winamp-5-666-released-build-3516)* 🦙 integration only, by ```go-to-currently-playing-song-dir.bat``` to determine the folder of the current song playing. Processes the ```winamp_now_playing.txt``` file generated by the [WinampNowPlayingToFile plugin](https://github.com/Aldaviva/WinampNowPlayingToFile) to determine this information. 
This method was used becuase API calls would limit us to only using this on the same computer that is running [WinAmp](https://forums.winamp.com/forum/winamp/winamp-discussion/306661-winamp-5-666-released-build-3516), and we want to be able to run this from *other* computers in the household, without having to poke through any kind of security. This is a very ad-hoc organic spaghetti script that isn’t at all nice-looking, but was fixedu p a lot in 2024 to branch past all the horribly ugly legacy 2008, 2009, 2012, and 2013 code, which all worked with the [Last.FM](https://www.last.fm/user/ClioCJS) logfile, an approach we have discontinued because it would create a big hassle every time Last.FM updated their logfile format.


&nbsp;
</details>

<details><summary>pre-rendered beautiful rainbow 🌈 horizontal dividers</summary>  

### 🌟 [divider.bat](../display-horizontal-divider.bat):

Pre-rendered [pretty rainbow-ized horizontal dividers](../dividers/) to separate out output into sections.
![image](https://github.com/user-attachments/assets/ca684639-3df9-4f9c-9e82-17af0a5bb320)

&nbsp;
</details>

<details><summary>Prompting System with automatic default-answer timeouts</summary>  

### 🌟 [askYN.bat](../askYN.bat):

The Yes/No prompting system with automatic-default-answer prompt timeouts.
![image](https://github.com/user-attachments/assets/fbff4fcd-f9da-4395-bfa1-bc95b85a7b18)

&nbsp;
</details>

<details><summary>Messaging System for warnings/errors/success/debug/etc</summary>  

### 🌟 [print-message.bat](../print-message.bat):

The messaging system (used by [warning.bat](../warning.bat), [debug.bat](../debug.bat), [error.bat](../error.bat), [fatal_error.bat](../fatalerror.bat), [success.bat](../success.bat), [celebration.bat](../celebration.bat), [important.bat](../important.bat), [important_less.bat](../important_less.bat), [advice](../advice.bat), [unimportant](../unimportant.bat), etc)

![image](https://github.com/user-attachments/assets/a3335d4e-9359-4584-a4ba-2a306907cb30)

&nbsp;
</details>

<details><summary>File Randomizer / Shuffler (to eliminate alphabetical bias)</summary>  

### 🌟 [randomize-file.pl](../randomize-file.pl.bat):

Scrambles the lines of STDIN.  One could think of it as shuffling/randomizing a playlist/filelist.  Used to do things in random orders.
![image](https://github.com/user-attachments/assets/e64933d7-c8e9-4b9c-a128-1bd40bc53116)

&nbsp;
</details>

<details><summary>Alternate Data Stream file tag editor (for lyric approval)</summary>  

### 🌟 [add-ADS-tag-to-file.bat](../add-ADS-tag-to-file.bat) / [remove-ADS-tag-from-file.bat](../remove-ADS-tag-from-file.bat) / [display-ADS-tag-from-file.bat](../display-ADS-tag-from-file.bat):

Commands for displaying tags, and for adding/removing tags to files using [Alternate Data Streams](https://superuser.com/questions/186627/anybody-have-a-legitimate-use-for-alternate-data-streams-in-ntfs). Used for lyric [dis]approval.
![image](https://github.com/user-attachments/assets/d21f1af0-b2bf-479c-940f-7f62252ef6ce)

&nbsp;
</details>





<details><summary>Validators (for variables, commands, functions, & file extensions)</summary>  

### 🌟 [validate-environment-variables {list of env-var names}](../validate-environment-variable.bat):

Validates whether environment variables (and the files they point to!) exist.
![image](https://github.com/user-attachments/assets/837b847e-9562-4adf-a981-1ad67497b2f7)

### 🌟 [validate-in-path {list of commands}](../validate-in-path.bat):

Validates whether commands (be they internal, alias, or not) are in the path
![image](https://github.com/user-attachments/assets/e05721d4-617c-456e-ab35-19b6b81be036)

### 🌟 [validate-is-extension {filename} {list of extensions}](../validate-is-extension.bat):

Validates whether a file has an acceptable file extension.  
![image](https://github.com/user-attachments/assets/36358ff3-f956-444e-b106-dc7014ee9e7d)

### 🌟 [validate-is-function {list of functions}](../validate-function.bat):

Validates whether a TCC user %@function is defined or not
![image](https://github.com/user-attachments/assets/b877db1e-d797-4f26-b36e-f83f57933469)

&nbsp;

</details>









<details><summary>Visual Layer (ansi / űńîçőḑѐ / emoji functions)</summary>  

### 🌟 [bigecho.bat](../bigecho.bat):

Echos text in double-height (using VT100 double-height ANSI codes). Requires ```set-ansi```.
![image](https://github.com/user-attachments/assets/9cde5587-3033-4fb1-917a-2a82986c6fa8)

### 🌟 [set-ansi.bat](../set-ansi.bat):

Sets envirionment variables (or user functions) for all the ansi codes we know to exist, as well as for our messaging system ([print-message.bat](../print-message.bat)). Read the VT100 and VT220 manuals all the way through for this.

### 🌟 [set-emojis.bat](../set-emojis.bat):

Sets all the emoji we care to set, using the [emoji.env](../emoji.env) file to add new emoji.

### 🌟 [fast_cat.exe](../cat_fast.exe):

Version of ```cat.exe``` deemed to be the fastest. I have several versions of the unix ```cat``` command, but this is the one I use for speediness. Piping things to ```fast_cat``` or ```cat_fast``` fixes ANSI rendering errors and is a required step for modern color rendering if you use [TCC](https://jpsoft.com/all-downloads/all-downloads.html) in conjunction with Windows Terminal.


&nbsp;

</details>



<details><summary>Conditional Deletion</summary>  


### 🌟 [delete-zero-byte-files.bat](../delete-zero-byte-files.bat) {filemask}:

Deletes all 0-byte files matching a filemask. Removes 0-byte files to save us having to check EVERY file for non-zero-ness.
![image](https://github.com/user-attachments/assets/d77d8e9c-af57-42f6-95b8-4dc94205c370)

### 🌟 [del-if-exists.bat](../del-if-exists.bat):

Delete a file, but only if it exists.

![image](https://github.com/user-attachments/assets/cad43e13-7a44-4a70-89ec-fc1304ecfab8)

&nbsp;

</details>



<details><summary>Miscellaneous</summary>  


### 🌟 [environm.bat](../environm.bat):

An absolute mess, but this is the command line initialization script that is run every time our command line is opened. Most anything I create won’t work without this being run.


### 🌟 [run-piped-input-as-bat.bat](../run-piped-input-as-bat.bat):

Receives piped input and runs it as if it were typed to the command line. Dangerous stuff!


### 🌟 [change-single-quotes-to-double-apostrophes.py](../change-single-quotes-to-double-apostrophes.py):

Changes single quotes (```"```) into double-apostrophes (```''```). 
Quote conversion offloaded into python script to avoid command-line complications with varoius quote symbols.
![image](https://github.com/user-attachments/assets/64a42984-11c3-4207-99db-502f8f1b169a)

&nbsp;

### 🌟 [mp3index.bat](../mp3index.bat):

Prints a list of all audio files (e.g. mp3, flac, wav, midi, mod, etc) *or* all vocal files (i.e. audio files that are capable of having vocals) (e.g. mp3, flac, wav, NOT midi, NOT mod, etc). 
Technically should be called “```audio_file_index.bat```”... but isn’t. 
![image](https://github.com/user-attachments/assets/7a1262a5-66bf-445d-b611-cd936035b93b)
&nbsp;

</details>


-----------------------------------------------------------------------------------------------------------------------------------------------
-----------------------------------------------------------------------------------------------------------------------------------------------


🏁🏁🏁 🔚 

![image](https://github.com/user-attachments/assets/9abdb1a5-c50a-424c-b151-144046fedd93)





TODO: update about section to include list of obstacles while doing this -- hallucination-prevention was tough. so was encoding. and concurrency. instrumentals. etc.
NOTE: New hallucation patterns must be added to: delete-bad-AI-transcriptions.bat lyric-postprocessor.pl subtitle-postprocessor.pl remove-period-at-ends-of-lines.pl
			NEW HALLUCNATION: I’m sorry, I don’t know what I’m doing - very uncommon? do we bother? cover both smart/dumb apostrophes

TODO: mention about local repo search: c:\lyrics\M\Metallica\Metallica - One.txt search
TODO: IDEA: Go thru existing lyrics & subtitles, if non-english language charcaters are found, take the line, run through translation API, then add english version in parenthesis at end of line .... But what happens with a mixed-language line then? Nothing, just treat it the same.



TODO: search for other todos below

TODO: subtitle_length.py add to docs and 




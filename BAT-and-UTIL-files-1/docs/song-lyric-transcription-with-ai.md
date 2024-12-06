# 🎆 AI Lyric Transcription System For Windows 🎆

## ✨ Goals: ✨

  1. 🥅 *General*: 🥅 To see the lyrics 📄 to music 🎵 highlighted ↔ as they are sung 🎤
  1. 🥅 *Technical*: 🥅 To automate AI transcription of music into karaoke files
  1. 🥅 *Specific*: 🥅 To have the [MiniLyrics](https://minilyrics.en.softonic.com/) program correctly display lyrics as they are sung.
  1. 🥅 *Detailed*: 🥅 To obtain and approve accurate lyrics for songs, which are then used as a prompt to improve the accuracy of WhisperAI's transcription of audio files into karaoke/subtitle files.

-----------------------------------------------------------------------------------------------------------------------------------------------

## 📓 Terminology: 📓

<details><summary>Click here to view full definitions of “karaoke files” and “sidecar files”</summary>  

&nbsp;

📑 *Karaoke Files*: 📑 We generally call both ```SRT files``` and ```LRC files``` “karaoke files”, which is a colloquial shorthand for “files capable of displaying the lyrics *as* they are sung”. This system generates ```SRT``` files, but includes a batch converter that converts ```SRT``` to ```LRC```.

&nbsp;

🏎 *Sidecar Files*: 🏎 A file of the *same* name, but *different* extension.

For example, ```filename.mp3``` might have a sidecar file named ```filename.txt```, which would typically be lyrics for a song, and a sidecar file named ```filename.jpg```, which would typically be the cover art to the song.  

Another example is when a program like ```whatever.exe``` has a ```whatever.ini`` *INI file* for its settings; That *INI* file is a sidecar file the *EXE* file. 
</details>

-----------------------------------------------------------------------------------------------------------------------------------------------

# ✔️ Requirements: ✔️

<details><summary>Click here to view the full requirements, which are primarily: Whisper, TCC, my scripts, and an optional WinAmp plugin</summary>  
  
  &nbsp; 
  
1. 👂 The [latest Faster-Whisper-XXL binaries](https://github.com/Purfview/whisper-standalone-win/releases/tag/Faster-Whisper-XXL)

    - The command ``faster-whisper-xxl.exe`` — our AI transriber — must be in your ```path```.

&nbsp;    

2. 💻 [JPSoft's TakeCommand (TCC) command-line v31+](https://jpsoft.com/all-downloads/all-downloads.html).  
    - Install TCC:
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

3. 🖥 [Windows Terminal](https://jpsoft.com/all-downloads/all-downloads.html).  
    - Needed to support our colorful presentation
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


4. ⌨️ My full [Clairevironment](https://github.com/ClaireCJS/clairecjs_bat/) (a big ball of stuff which includes this project).
    - Technically you probably only need about 100 of these files.  
    - This folder has it's own ```sort``` and ```uniq``` executables (from [Cygwin](https://www.cygwin.com)) to ensure consistency
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

5. ☯️ Optional: For [automatic cleanup](../BAT-and-UTIL-files-1/clean-up-AI-transcription-trash-files) of leftover AI files across an entire computer:
    - Always be running  the ```Everything``` service, which comes with TakeCommand ([TCC](https://jpsoft.com/all-downloads/all-downloads.html))
    - Use ```start-everything.bat``` or ```start EVERYTHING.EXE -startup``` to start it, if it doesn't start automatically. 

&nbsp;

5. ⚡️ Optional: For 🦙 *[WinAmp](https://forums.winamp.com/forum/winamp/winamp-discussion/306661-winamp-5-666-released-build-3516)* 🦙 integration:
    - Install the [WinampNowPlayingToFile plugin](https://github.com/Aldaviva/WinampNowPlayingToFile)
    - Configure the [WinampNowPlayingToFile plugin](https://github.com/Aldaviva/WinampNowPlayingToFile) so that the 2ⁿᵈ line of its output file is the full filename of the currently playing song. 
    - This allows instant no-resource any-computer access to the location of which song file is currently playing in [WinAmp](https://forums.winamp.com/forum/winamp/winamp-discussion/306661-winamp-5-666-released-build-3516), allowing us to have commands that operate on “whatever song we are currently listening to” from any computer in the household. 🦙
      - Currently doesn't work if the music is paused, but a future update to the WinAmpNowPlayingToFile plugin is headed down the pipeline

&nbsp;

</details>

-----------------------------------------------------------------------------------------------------------------------------------------------

# ⚙️ HOW TO USE ⚙️

From a running TCC command line, use whatever system commands you'd like from the list below.

Generally speaking, it will be: ```create-srt audio_file.mp3``` or ```create-missing-karaoke``` or ```get-lyrics```.


-----------------------------------------------------------------------------------------------------------------------------------------------


# ⚙️ SYSTEM COMMANDS ⚙️

### NOTE: Many commands have several different aliases, for convenience-of-remembering.

#### 🍀 Four main types of commands exist for this system:

  1. 🎤️ Lyric alignment  ([get-lyrics](../BAT-and-UTIL-files-1/get-lyrics.bat),  [get-missing-lyrics](../BAT-and-UTIL-files-1/check-for-missing-lyrics.bat) etc)
  1. 🧏 Karaoke generation  ([create-srt](../BAT-and-UTIL-files-1/create-srt-from-file.bat), [get-karaoke-for-playlist](../BAT-and-UTIL-files-1/get-karaoke-for-playlist.bat), etc)
  1. 🕵 Lyric   Auditing ([review-lyrics](../BAT-and-UTIL-files-1/review-files.bat), [display-lyric-status.bat](../BAT-and-UTIL-files-1/display-lyric-status.bat), etc)
  1. 🕵 Karaoke Auditing ([review-subtitles](../BAT-and-UTIL-files-1/review-subtitles.bat), [check-for-missing-karaoke](../BAT-and-UTIL-files-1/check-for-missing-karaoke.bat), etc)
  
🍀 Two lesser types of commands exist for this system:

  1. ⚡ [WinAmp](https://forums.winamp.com/forum/winamp/winamp-discussion/306661-winamp-5-666-released-build-3516) 🦙 integration commands (to work with the song that is currently playing in ⚡️ [WinAmp](https://forums.winamp.com/forum/winamp/winamp-discussion/306661-winamp-5-666-released-build-3516) 🦙)
  1. ⚙️ Subordinate commands (*under-the-hood* stuff not generally invoked directly)

-----------------------------------------------------------------------------------------------------------------------------------------------

# 👉👉👉 *Lyric Alignment* commands:

#### These commands manage the lyric files which we download to improve transcription accuracy.


<details><summary>Click here to view command list & descriptions.</summary>  

### 🌟 [get-lyrics {*songfile*} / get-lyrics-for-song {*songfile*} / get-lyrics-via-multiple-sources {*songfile*}](../BAT-and-UTIL-files-1/get-lyrics-via-multiple-sources.bat):

Obtains the lyrics for a particular song file. 
- These transcriptions work **much** better when you have a lyric set. 
- This checks local sidecar files, local lyric repository, Genius, and Google — to obtain lyric files with as much ease possible.

### 🌟 [get-lyrics-for-currently-playing-song ](../BAT-and-UTIL-files-1/get-lyrics-for-currently-playing-song.bat):

If 🦙 *[WinAmp](https://forums.winamp.com/forum/winamp/winamp-discussion/306661-winamp-5-666-released-build-3516)* 🦙 integration is enabled, get lyrics for *the song currently being played*.


### 🌟 [get-missing-lyrics-here.bat](../BAT-and-UTIL-files-1/get-missing-lyrics-here.bat) / [get-missing-lyrics](../BAT-and-UTIL-files-1/get-missing-lyrics-here.bat) / [gmlh](../BAT-and-UTIL-files-1/get-missing-lyrics-here.bat) / [gml](../BAT-and-UTIL-files-1/get-missing-lyrics-here.bat):

Gets lyrics for all the files *in the current folder* that do not have *approved* lyric files.
(Uses [check-for-missing-lyrics.bat](../BAT-and-UTIL-files-1/check-for-missing-lyrics.bat).)


### 🌟 [get-lyrics-for-playlist.bat](../BAT-and-UTIL-files-1/get-lyrics-for-playlist.bat):

Gets lyrics for all the files *in a playlist* that do not have *approved* lyric files, in random order to avoid alphabetical bias.  
(Uses [check-for-missing-lyrics.bat](../BAT-and-UTIL-files-1/check-for-missing-lyrics.bat).)




</details>

-----------------------------------------------------------------------------------------------------------------------------------------------


# 👉👉👉 *Karaoke Generation* commands:

#### These commands creates the karaoke files that are the primary goal of this project! 🎈

<details><summary>Click here to view command list & descriptions.</summary>  

### 🌟 create-srt {*songfile*} / [create-srt-from-file {*songfile*}](../BAT-and-UTIL-files-1/create-srt-from-file.bat):

**Create karaoke for one audio file.**
Performs the AI transcription process for a single song file.
Run without parameters to see various options, including but not limited to  ```ai``` (skips the lyrics component), ```fast``` (shortens prompt timer lengths), ```force``` (generate it even if it already exists), and ```LyricsApproved``` (consider all lyric files to be *pre-approved* even if not explicitly marked as such).


### 🌟 srtthis / [create-srt-file-for-currently-playing-song.bat](../BAT-and-UTIL-files-1/create-srt-file-for-currently-playing-song.bat):

If 🦙 *[WinAmp](https://forums.winamp.com/forum/winamp/winamp-discussion/306661-winamp-5-666-released-build-3516)* 🦙 integration is enabled, creates karaoke file for *the song currently being played*.


### 🌟 cmk / cmkf / [create-missing-karaoke-files / create-the-missing-karaokes-here](../BAT-and-UTIL-files-1/create-the-missing-karaokes-here.bat):

Create karaoke files for **all songs** *in the current folder* that do not have them


### 🌟 ❗TODO❗ [get-karaoke-for-playlist.bat](../BAT-and-UTIL-files-1/get-karaoke-for-playlist.bat):

Create karaoke files for **all songs** *in a playlist* that do not have them — Traverses a playlist, running ```create-SRT``` on every file in the playlist. (In random order, to prevent alphabetical bias.)


### 🌟 ❗TODO❗ create-karaoke-automatically-from-approved-lyrics.bat {folder to recurse through]:

Create karaoke files for **all songs** in a *folder tree* that do not have them, as long as their lyric file has been previously approved. This is intended so one can spend 100% of time aligning/approving lyrics (i.e. with ```get-lyrics-for-playlist.bat```), then go to bed and run this to generate everything that has pre-approved lyrics, saving the karaoke generation for another time (like when you are asleep). 



### 🌟 [create-SRT-without-lyrics-or-voice-detection-for-an-entire-folder-tree.bat](../BAT-and-UTIL-files-1/create-SRT-without-lyrics-or-voice-detection-for-an-entire-folder-tree.bat):

Rarely used side-utility: Creates karaoke files for **all songs** in a *folder tree* without using lyric files or voice detection (VAD). This is useful for folders of hundreds sound clips and small samples, where you just want to get a lot done without the extra overhead of lyrics and without the extra time delay of loading the VAD model.

</details>

-----------------------------------------------------------------------------------------------------------------------------------------------

# 👉👉👉 *Auditing Commands* for *Lyrics*:

#### These commands find & obtain missing lyric files.

<details><summary>Click here to view command list & descriptions.</summary>  

### 🌟 [review-lyrics / review-all-TXTs / review-TXTs.bat](../BAT-and-UTIL-files-1/review-files.bat):

Reviews all lyric files in current folder, using ```print-with-columns``` to reduce scrolling up.


### 🌟 dls / [display-lyric-status.bat](../BAT-and-UTIL-files-1/display-lyric-status.bat):

Displays the lyric status (approved, unapproved, or unset) for all lyric files in current folder. 
To have this happen automatically when changing into a folder,  ```alias cd=call cd-alias.bat```,  then create ```autorun.bat``` in the base of your collection, containing the command:
```@if exist *.txt (call display-lyric-status)```
![image](https://github.com/user-attachments/assets/0ccdebd6-7e26-4a2b-91ee-c3e0cfe9f147)



### 🌟 cfml / cmlf / [check-for-missing-lyrics](../BAT-and-UTIL-files-1/check-for-missing-lyrics.bat):

Displays a list of files in the *current folder* which are missing *approved lyric* files


### 🌟 Lyric Auditor: cpfml / cpmlf / [check-playlist-for-missing-lyrics](../BAT-and-UTIL-files-1/get-playlist-for-missing-lyrics.bat):

Displays a list of files in a *playlist* which are missing *approved lyric* files.

![image](https://github.com/user-attachments/assets/42fb6e4e-2cea-48e1-bbc8-499454c201ae)

</details>

-----------------------------------------------------------------------------------------------------------------------------------------------

# 👉👉👉 *Auditing Commands* for *Karaoke*:

#### These commands find & obtain missing karaoke files.

<details><summary>Click here to view command list & descriptions.</summary>  

### 🌟 [review-subtitles / review-all-SRTs / review-SRTs.bat / review-LRCs.bat](../BAT-and-UTIL-files-1/review-subtitles.bat):

Reviews all karaoke files in current folder, using ```print-with-columns``` to eliminate most scrolling up.

![image](https://github.com/user-attachments/assets/9b579cf2-ca93-4684-aec5-35df8c793143)


### 🌟 cfmk / [check-for-missing-karaoke](../BAT-and-UTIL-files-1/check-for-missing-karaoke.bat):

Displays a list of files in the *current folder* which are missing *karaoke* files

![image](https://github.com/user-attachments/assets/61e1f155-a798-4668-945a-7d7dd2ac06dc)


### 🌟 Playlist Auditor: [CheckAFilelistForFilesMissingSidecarFilesOfTheProvidedExtension](../BAT-and-UTIL-files-1/check_a_filelist_for_files_missing_sidecar_files_of_the_provided_extensions.py):

Processes a playlist to create a new playlist consisting of only the songs missing karaoke files.

EXAMPLE:
```
check_a_filelist_for_files_missing_sidecar_files_of_the_provided_extensions.py PlayList.m3u *.srt;*.lrc ``CreateSRTFileWrite
```
^^^ This example goes through the file ```PlayList.m3u```, checks for all files that do not have karaoke files (i.e. no ```*.srt``` or ```*.lrc``` sidecar file), creates a ```PlayList-without lrc srt.m3u``` consisting of those files.  Bbecause the `````CreateSRTFileWrite``` option was used, it also generates a script to actually create the missing karaoke files.  The ``GetLyricsFileWrite``` option can instead be used to *ONLY* obataining lyrics, and save the karaoke generation for later.

![image](https://github.com/user-attachments/assets/5b368467-b23b-4039-b3df-c4dc85e90ad5)

</details>

-----------------------------------------------------------------------------------------------------------------------------------------------


# 👉👉👉 ⚡️ *[WinAmp](https://forums.winamp.com/forum/winamp/winamp-discussion/306661-winamp-5-666-released-build-3516) 🦙 Integration* Commands:

#### These commands allows us to operate on “the song we are currently listening to” rather than a specific file or playlist.

<details><summary>Click here to view command list & descriptions.</summary>  

### 🌟 [get-lyrics-for-currently-playing-song ](../BAT-and-UTIL-files-1/get-lyrics-for-currently-playing-song.bat):

Runs ```get-lyrics``` on *the song currently being played* in ⚡️ [WinAmp](https://forums.winamp.com/forum/winamp/winamp-discussion/306661-winamp-5-666-released-build-3516) 🦙.


### 🌟 srtthis / [create-srt-file-for-currently-playing-song.bat](../BAT-and-UTIL-files-1/create-srt-file-for-currently-playing-song.bat):

Runs ```create-srt``` on *the song currently being played* in ⚡️ [WinAmp](https://forums.winamp.com/forum/winamp/winamp-discussion/306661-winamp-5-666-released-build-3516) 🦙.


### 🌟 Karaoke insertion fudger - [eccsrt2lrc2clip.bat](../BAT-and-UTIL-files-1/eccsrt2lrc2clip.bat):

In certain very rare situations, [MiniLyrics](https://minilyrics.en.softonic.com/) does not auto-import the generated SRT file.  Because [MiniLyrics](https://minilyrics.en.softonic.com/) primarily uses LRC instead of SRT, it can sometimes miss an SRT. When this happens, the SRT must be converted to LRC, copied to the clipboard, and pasted into the [MiniLyrics](https://minilyrics.en.softonic.com/) lyric window manually. This script handles that by detecting the current song playing, converting it's SRT to LRC, copying it to the clipboard, and automatically opening [MiniLyrics](https://minilyrics.en.softonic.com/)'s lyric editor window. All the user has to do is paste and save.

</details>

-----------------------------------------------------------------------------------------------------------------------------------------------

# 👉👉 *Under-The-Hood*: Project-Specific Utility Commands 

Other important commands specific to this project.

<details><summary>Click here to view command list & descriptions.</summary>  

### 🌟 [srt2lrc.py](../BAT-and-UTIL-files-1/srt2lrc.py):

A *batch* SRT-file to LRC-file converter. Used by [eccsrt2lrc2clip.bat](../BAT-and-UTIL-files-1/eccsrt2lrc2clip.bat)


### 🌟 [srt2txt.py](../BAT-and-UTIL-files-1/srt2txt.py):

A *single-file* SRT-file to TXT-file converter. 


### 🌟 [approve-lyrics / approve-lyric-file {lyric_file}](../BAT-and-UTIL-files-1/approve-lyric-file.bat) / [disapprove-lyrics / disapprove-lyric-file {lyric_file}](../BAT-and-UTIL-files-1/disapprove-lyric-file.bat):

Marks lyric file with approval/disapproval so that we can pre-approve lyric files in advance of transcription process. Uses [Alternate Data Streams](https://superuser.com/questions/186627/anybody-have-a-legitimate-use-for-alternate-data-streams-in-ntfs) to store approval tags in a database-less, file-less way.

![image](https://github.com/user-attachments/assets/c48e2ed3-c1fb-4760-8ba8-c9accf691178)

### 🌟 [approve-subtitles / approve-subtitle-file {subtitle_file}](../BAT-and-UTIL-files-1/approve-subtitle-file.bat) / [disapprove-subtitles / disapprove-subtitle-file {subtitle_file}](../BAT-and-UTIL-files-1/disapprove-subtitle-file.bat):

Same as above but for karaoke files.

</details>

-----------------------------------------------------------------------------------------------------------------------------------------------

# 👉👉 *Under-The-Hood*: Non-Project-Specific utility commands:

<details><summary>Click here to view command list & descriptions.</summary>  

### 🌟 [print_with_columns.py](../BAT-and-UTIL-files-1/print_with_columns.py) / [newspaper.bat](../BAT-and-UTIL-files-1/newspaper.bat):

Created to review lyrics & karaoke for this project without the interruption of having to scroll up!

Displays text in column (“newspaper”) format with columns.
A useful replacement for the ```type``` command.


### 🌟 [google.py](../BAT-and-UTIL-files-1/google.py):

Invokes a google search in primary browser, all while properly preserving the quotes given at the command line. 
Way harder to do than it should be.

### 🌟 [insert-before-each-line.py](../BAT-and-UTIL-files-1/insert-before-each-line.py) / [insert-after-each-line.py](../BAT-and-UTIL-files-1/insert-after-each-line.py):

Inserts text before/after each line of STDIN. Used for script generation.   
Put ```{{{{QUOTE}}}}``` in the argument to turn it into a quote mark in the final output.

### 🌟 [unique-lines.pl](../BAT-and-UTIL-files-1/unique-lines.pl):

Display each *unique* line in a file. Much like the ```uniq``` command except that no pre-sorting is required.
[Also has postprocessor functionality listed below]

</details>

-----------------------------------------------------------------------------------------------------------------------------------------------


# 👉👉 *Under-The-Hood*: Pre/Post-Processor/Fetch Utility Commands:

Preprocessors / Postprocessors developed for this project.

<details><summary>Click here to view command list & descriptions.</summary>  

### 🌟 [get-lyrics-with-lyricsgenius-json-processor.pl](../BAT-and-UTIL-files-1/get-lyrics-with-lyricsgenius-json-processor.pl):

The lyric downloader we use for Genius saves lyrics as a ```JSON file```. This extracts the actual lyrics from that file, with minimal preprocessing.

### 🌟 [unique-lines.pl](../BAT-and-UTIL-files-1/unique-lines.pl):

A lyric postprocessor that removes tons of junk from downloaded lyrics, only shows unique lines (to help fit into WhisperAI's 224-token prompt limit), and smushes all the lyrics into a single line (for use as a command line option). Started as a spiritual fork of ``uniq``` that doesn't require file sorting (to avoid using up the 224 max tokens for WhisperAI with repeating lyrics), and grew into full-fledged lyric preprocessor that does much lyric massaging. Including putting a period at the end of each line, which is later removed by our subtitle postprocessor.


### 🌟 [remove-period-at-ends-of-lines.pl](../BAT-and-UTIL-files-1/remove-period-at-ends-of-lines.pl):

The final subtitle postprocessor, which removes periods from end of each line in a subtitle. 
Preserves periods for words like “Mr.”, “Dr.”, “approx”, etc

**Rationale:** We add “invisible” periods to the end of each line of lyrics, so that WhisperAI's ```--sentence``` option is influenced by where lyric posters post the line breaks in their lyrics. It absolutely helped. A lot. Hours were spent determiing this and, and it was obvious from the first [of many] tests.   We then remove these periods (making them “invisible”) afterward, because they are ugly and often not even gramatically correct — just correct for *timing* purposes.  

This also also has some extra functionality slipped in to de-censoring some curse words that WhisperAI censors.
This functoinality can be suppressed with the ```--leave-censorship``` or ```-L``` options.

</details>

-----------------------------------------------------------------------------------------------------------------------------------------------

# 👉👉 *Under-The-Hood*: Existing commands also used by this system:

Various commands that were already a part of my “Clairevironment”.

Click to expand:

<details><summary>🌈Psychedelic color-cycler with 👂WhisperAI-specific postprocessing</summary>  

### 🌟 [copy-move-post.py](../BAT-and-UTIL-files-1/copy-move-post.py):

A cosmetic postprocessor which employes ANSI color-cycling to inbue a psychedelic effect onto text by cycling the colors of the primary text color through the visible spectrum. Originally written to combat “hangxiety” — anxiety over whether your code has hung — by affecting screenoutput without actually generating any “real” output. Then enhanced to postprocess the output to the ```move``` and ```copy``` commands with emoji, color, italics, double-height text for summaries, and more. Finally, enhanced again with explicit postprocessing for WhisperAI's transcription output.

Uses my [claire_console.py](../BAT-and-UTIL-files-1/clairecjs_utils/claire_console.py) library to achieve the color-cycling.

&nbsp;
</details>

<details><summary>⚡ WinAmp 🦙 integration to operate on “song currently playing”</summary>  

### 🌟 [go-to-currently-playing-song-dir.bat](../BAT-and-UTIL-files-1/go-to-currently-playing-song-dir.bat):

Used in this project for ⚡ [WinAmp](https://forums.winamp.com/forum/winamp/winamp-discussion/306661-winamp-5-666-released-build-3516) 🦙 integration only. Changes current folder to same folder that the song we are listening to is in.  (The change-folder script is actually generated by [edit-currently-playing-attrib.bat](../BAT-and-UTIL-files-1/edit-currently-playing-attrib.bat))

&nbsp;
### 🌟 [edit-currently-playing-attrib-helper.pl](../BAT-and-UTIL-files-1/edit-currently-playing-attrib-helper.pl):

Used in this project for 🦙 *[WinAmp](https://forums.winamp.com/forum/winamp/winamp-discussion/306661-winamp-5-666-released-build-3516)* 🦙 integration only, by ```go-to-currently-playing-song-dir.bat``` to determine the folder of the current song playing. Processes the ```winamp_now_playing.txt``` file generated by the [WinampNowPlayingToFile plugin](https://github.com/Aldaviva/WinampNowPlayingToFile) to determine this information. 
This method was used becuase API calls would limit us to only using this on the same computer that is running [WinAmp](https://forums.winamp.com/forum/winamp/winamp-discussion/306661-winamp-5-666-released-build-3516), and we want to be able to run this from *other* computers in the household, without having to poke through any kind of security. This is a very ad-hoc organic spaghetti script that isn't at all nice-looking, but was fixedu p a lot in 2024 to branch past all the horribly ugly legacy 2008, 2009, 2012, and 2013 code, which all worked with the [Last.FM](https://www.last.fm/user/ClioCJS) logfile, an approach we have discontinued because it would create a big hassle every time Last.FM updated their logfile format.


&nbsp;
</details>

<details><summary>$\textcolor{red}{\textsf{Red}}$  horizontal dividers, pre-rendered beautiful rainbow</summary>  



$\textcolor{red}{\textsf{pre}}$%$\textcolor{orange}{\textsf{-re}}$%
$\textcolor{yellow}{\textsf{nde}}$%
$\textcolor{lime}{\textsf{red}}$%
$\textcolor{green}{\textsf{ rai}}$
$\textcolor{teal}{\textsf{nbow}}$
$\textcolor{cyan}{\textsf{ hor}}$%
$\textcolor{blue}{\textsf{izon}}$%
$\textcolor{violet}{\textsf{tal}}$%
$\textcolor{magenta}{\textsf{ div}}$%
$\textcolor{pink}{\textsf{iders}}$



$\textcolor{red}{\textsf{pre}}$%
$\textcolor{orange}{\textsf{-re}}$%
$\textcolor{yellow}{\textsf{nde}}$%
$\textcolor{lime}{\textsf{red}}$%
$\textcolor{green}{\textsf{ rai}}$%
$\textcolor{teal}{\textsf{nbow}}$%
$\textcolor{cyan}{\textsf{ hor}}$%
$\textcolor{blue}{\textsf{izon}}$%
$\textcolor{violet}{\textsf{tal}}$%
$\textcolor{magenta}{\textsf{ div}}$%
$\textcolor{pink}{\textsf{iders}}$


$\textcolor{orange}{\textsf{Orange}}$ 
$\textcolor{Yellow}{\textsf{Yellow}}$ 


### 🌟 [divider.bat](../BAT-and-UTIL-files-1/display-horizontal-divider.bat):

Pre-rendered [pretty rainbow-ized horizontal dividers](../BAT-and-UTIL-files-1/dividers/) to separate out output into sections.
&nbsp;
</details>

<details><summary>Prompting System with automatic default-answer timeouts</summary>  

### 🌟 [askYN.bat](../BAT-and-UTIL-files-1/askYN.bat):

The Yes/No prompting system with automatic-default-answer prompt timeouts.
&nbsp;
</details>

<details><summary>Messaging System for warnings/errors/success/debug/etc</summary>  

### 🌟 [print-message.bat](../BAT-and-UTIL-files-1/print-message.bat):

The messaging system (used by [warning.bat](../BAT-and-UTIL-files-1/warning.bat), [debug.bat](../BAT-and-UTIL-files-1/debug.bat), [error.bat](../BAT-and-UTIL-files-1/error.bat), [fatal_error.bat](../BAT-and-UTIL-files-1/fatalerror.bat), [success.bat](../BAT-and-UTIL-files-1/success.bat), [celebration.bat](../BAT-and-UTIL-files-1/celebration.bat), [important.bat](../BAT-and-UTIL-files-1/important.bat), [important_less.bat](../BAT-and-UTIL-files-1/important_less.bat), [advice](../BAT-and-UTIL-files-1/advice.bat), [unimportant](../BAT-and-UTIL-files-1/unimportant.bat), etc)

&nbsp;

</details>

<details><summary>File Randomizer / Shuffler</summary>  
### 🌟 [randomize-file.pl](../BAT-and-UTIL-files-1/randomize-file.pl.bat):

Scrambles the lines of STDIN.  One could think of it as shuffling/randomizing a playlist/filelist.  Used to do things in random orders.

&nbsp;
</details>
<details><summary>Alternate Data Stream file tag editor</summary>  

### 🌟 [add-ADS-tag-to-file.bat](../BAT-and-UTIL-files-1/add-ADS-tag-to-file.bat) / [remove-ADS-tag-from-file.bat](../BAT-and-UTIL-files-1/remove-ADS-tag-from-file.bat) / [display-ADS-tag-from-file.bat](../BAT-and-UTIL-files-1/display-ADS-tag-from-file.bat):

Commands for displaying tags, and for adding/removing tags to files using [Alternate Data Streams](https://superuser.com/questions/186627/anybody-have-a-legitimate-use-for-alternate-data-streams-in-ntfs). Used for lyric [dis]approval.

&nbsp;
</details>





<details><summary>Validators (for variables, commands, functions, & file extensions)</summary>  

### 🌟 [validate-environment-variables {list of env-var names}](../BAT-and-UTIL-files-1/validate-environment-variable.bat):

Validates whether environment variables (and the files they point to!) exist.

### 🌟 [validate-in-path {list of commands}](../BAT-and-UTIL-files-1/validate-in-path.bat):

Validates whether commands (be they internal, alias, or not) are in the path

### 🌟 [validate-is-extension {filename} {list of extensions}](../BAT-and-UTIL-files-1/validate-is-extension.bat):

Validates whether a file has an acceptable file extension.  

### 🌟 [validate-is-function {list of functions}](../BAT-and-UTIL-files-1/validate-function.bat):

Validates whether a TCC user %@function is defined or not

&nbsp;
</details>









<details><summary>Visual Layer (ansi / űńîçőḑѐ / emoji functions)</summary>  

### 🌟 [bigecho.bat](../BAT-and-UTIL-files-1/bigecho.bat):

Echos text in double-height (using VT100 double-height ANSI codes). Requires ```set-ansi```.

### 🌟 [set-ansi.bat](../BAT-and-UTIL-files-1/set-ansi.bat):

Sets envirionment variables (or user functions) for all the ansi codes we know to exist, as well as for our messaging system ([print-message.bat](../BAT-and-UTIL-files-1/print-message.bat)). Read the VT100 and VT220 manuals all the way through for this.

### 🌟 [set-emojis.bat](../BAT-and-UTIL-files-1/set-emojis.bat):

Sets all the emoji we care to set, using the [emoji.env](../BAT-and-UTIL-files-1/emoji.env) file to add new emoji.

### 🌟 [fast_cat.exe](../BAT-and-UTIL-files-1/cat_fast.exe):

Version of ```cat.exe``` deemed to be the fastest. I have several versions of the unix ```cat``` command, but this is the one I use for speediness. Piping things to ```fast_cat``` or ```cat_fast``` fixes ANSI rendering errors and is a required step for modern color rendering if you use [TCC](https://jpsoft.com/all-downloads/all-downloads.html) in conjunction with Windows Terminal.


&nbsp;

</details>




		  
<details><summary></summary>  
&nbsp;
</details>
<details><summary></summary>  
&nbsp;
</details>
<details><summary></summary>  
&nbsp;
</details>
&nbsp;
<details><summary></summary>  



<details><summary>Click here to view the remaining command list & descriptions.</summary>  


### 🌟 [run-piped-input-as-bat.bat](../BAT-and-UTIL-files-1/run-piped-input-as-bat.bat):

Receives piped input and runs it as if it were typed to the command line. Dangerous stuff!



### 🌟 [delete-zero-byte-files.bat](../BAT-and-UTIL-files-1/delete-zero-byte-files.bat) {filemask}:

Deletes all 0-byte files matching a filemask. Removes 0-byte files to save us having to check EVERY file for non-zero-ness.

### 🌟 [del-if-exists.bat](../BAT-and-UTIL-files-1/del-if-exists.bat):

Delete a file, but only if it exists.


&nbsp;


### 🌟 [change-single-quotes-to-double-apostrophes.py](../BAT-and-UTIL-files-1/change-single-quotes-to-double-apostrophes.py):

Changes single quotes (```"```) into double-apostrophes (```''```). 
Quote conversion offloaded into python script to avoid command-line complications with varoius quote symbols.

&nbsp;

### 🌟 [mp3index.bat](../BAT-and-UTIL-files-1/mp3index.bat):

Prints a list of all audio files (mp3, flac, wav, etc).
Technically should be called “```audio_file_index.bat```”. 





&nbsp;
</details>


-----------------------------------------------------------------------------------------------------------------------------------------------
-----------------------------------------------------------------------------------------------------------------------------------------------


🏁🏁🏁 🔚 
![image](https://github.com/user-attachments/assets/9abdb1a5-c50a-424c-b151-144046fedd93)



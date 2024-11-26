# AI Lyric Transcription System For Windows

## ✨ Goals:

🥅 *General goal*: To see the lyrics to music highlighted as they are sung

🥅 *Technical goal*: To automate AI transcription of music into karaoke files

🥅 *Specific technical goal*: To have the [MiniLyrics](https://minilyrics.en.softonic.com/) program correctly display lyrics as they are sung.

🥅 *Detailed technical goal*: To obtain and approve accurate lyrics for songs, which are then used as a prompt to improve the accuracy of WhisperAI's transcription of audio files into karaoke/subtitle files.

## 📓 Terminology:

📑 *Karaoke Files*: We generally call both ```SRT files``` and ```LRC files``` "karaoke files", which is a colloquial shorthand for "files capable of displaying the lyrics *as* they are sung". This system generates SRT files, but includes a batch converter that converts SRT to LRC.

🏎 *Sidecar Files*: A file of the *same* name, but *different* extension. For example, ```filename.mp3``` might have a sidecar file named ```filename.txt```, which would typically be lyrics for a song, and a sidecar file named ```filename.jpg```, which would ```filename.mp3``` that would tpically be the cover art to the song.

## ⚙️ Requirements:

1. 👂 The [latest Faster-Whisper-XXL binaries](https://github.com/Purfview/whisper-standalone-win/releases/tag/Faster-Whisper-XXL). 
    The command ``faster-whisper-xxl.exe`` — our AI transriber — must be in your path.

1. 💻 [JPSoft's TakeCommand (TCC) command-line v31+](https://jpsoft.com/all-downloads/all-downloads.html), installable with Winget via the command: ```winget install JPSoft.tcmd```.  (If not installed to ```c:\tcmd```, you may need to ```mklink c:\TCMD "c:\Program Files\TCMD31"```, substituting in the folder where TCC was installed.)

1. ⌨️ My full [Clairevironment](https://github.com/ClaireCJS/clairecjs_bat/) (this project). It is built on top of my own personal environment layer and cannot exist outside of it.  ```git.exe clone https://github.com/ClaireCJS/clairecjs_bat/``` then move the BAT-file folder (#1, not #2) into ```c:\bat\``` .... Technically you probably only need about 40 of these files, but detangling things is a lot of effort.

1. 💾 [Cygwin](https://www.cygwin.com) or other comparable version of ```sort.exe``` and ```uniq.exe```. 

1. ☯️ Optional: For [automatic file-trash cleanup across an entire computer](../BAT-and-UTIL-files-1/clean-up-AI-transcription-trash-files.bat), you will need the ```Everything``` service to track files. It comes with TakeCommand (TCC). (Use ```start-everything.bat``` to start it, if it doesn't start automatically.)

1. ⚡️ Optional: For 🦙 *[WinAmp](https://forums.winamp.com/forum/winamp/winamp-discussion/306661-winamp-5-666-released-build-3516)* 🦙 integration: The [WinampNowPlayingToFile plugin](https://github.com/Aldaviva/WinampNowPlayingToFile), configured so that the 2ⁿᵈ line of its output file is the full filename of the currently playing song. This allows instant no-resource any-computer access to the location of which song file is currently playing in [WinAmp](https://forums.winamp.com/forum/winamp/winamp-discussion/306661-winamp-5-666-released-build-3516), allowing us to have commands that operate on "whatever song we are currently listening to". 🦙

____________________________________________________________________________________________________________
____________________________________________________________________________________________________________


# SYSTEM COMMANDS

### 🌟 NOTE: Many commands have several different aliases, for convenience-of-remembering.

## Several types of commands for this system:

  1. 🎤️ Lyric alignment commands ([get-missing-lyrics](../BAT-and-UTIL-files-1/check-for-missing-lyrics.bat), [display-lyric-status.bat](../BAT-and-UTIL-files-1/display-lyric-status.bat), etc)
  1. 🧏 Karaoke generation commands ([create-srt](../BAT-and-UTIL-files-1/create-srt-from-file.bat), [get-karaoke-for-playlist.bat](../BAT-and-UTIL-files-1/get-karaoke-for-playlist.bat), etc)
  1. 🕵 Auditing commands (to find files that do not have lyrics or karaoke)
  1. ⚡ [WinAmp](https://forums.winamp.com/forum/winamp/winamp-discussion/306661-winamp-5-666-released-build-3516) 🦙 integration commands (to work with the song that is currently playing in ⚡️ [WinAmp](https://forums.winamp.com/forum/winamp/winamp-discussion/306661-winamp-5-666-released-build-3516) 🦙)
  1. ⚙️ Subordinate commands (under the hood stuff not generally invokved directly)

____________________________________________________________________________________________________________
____________________________________________________________________________________________________________

# Lyric Alignment commands:

These commands manage the lyric files that are used to improve prompt accuracy.

### 🌟 [get-lyrics-for-playlist.bat](../BAT-and-UTIL-files-1/get-lyrics-for-playlist.bat)

Gets lyrics for all the files *in a playlist* that do not have *approved* lyric files, in random order to avoid alphabetical bias.  
(Uses [check-for-missing-lyrics.bat](../BAT-and-UTIL-files-1/check-for-missing-lyrics.bat).)

### 🌟 [gml](../BAT-and-UTIL-files-1/get-missing-lyrics-here.bat) / [gmlh](../BAT-and-UTIL-files-1/get-missing-lyrics-here.bat) / [get-missing-lyrics](../BAT-and-UTIL-files-1/get-missing-lyrics-here.bat) / [get-missing-lyrics-here](../BAT-and-UTIL-files-1/get-missing-lyrics-here.bat)

Gets lyrics for all the files *in the current folder* that do not have *approved* lyric files.
(Uses [check-for-missing-lyrics.bat](../BAT-and-UTIL-files-1/check-for-missing-lyrics.bat).)


### 🌟 [get-lyrics {songfile} / get-lyrics-for-song {songfile} / get-lyrics-via-multiple-sources {songfile}](../BAT-and-UTIL-files-1/get-lyrics-via-multiple-sources.bat)

Obtains the lyrics for a particular song, to foster proper AI transcription. These transcriptions work much better when you have a lyric set. This checks local sidecar files, local lyric repository, Genius, and Google, to obtain lyric files with as much ease possible.


### 🌟 dls / [display-lyric-status.bat](../BAT-and-UTIL-files-1/display-lyric-status.bat)

Displays the lyric status (approved, unapproved, or unset) for all lyric files in current folder. 
To have this happen automatically when changing into a folder, simply Alias the ```cd``` command into ```call ```[cd-alias.bat](../BAT-and-UTIL-files-1/cd-alias) — and then create a file called ```autorun.bat``` in the base folder of your music collection, containing the command ```@if exist *.txt (call display-lyric-status)```.



____________________________________________________________________________________________________________


# Karaoke Generation commands:

These commands creates the karaoke files that are the primary goal of this project!

### 🌟 create-srt {songfile} / [create-srt-from-file {songfile}](../BAT-and-UTIL-files-1/create-srt-from-file.bat)

Performs the AI transcription process for a single song file.
Run without parameters to see various options, including but not limited to  "ai" (skips lyrics process), "fast" (shortens prompt timer lengths), and "force" (generate it even thoughi t already exists).


### 🌟 cmk / cmkf / [create-missing-karaoke-files / create-the-missing-karaokes-here](../BAT-and-UTIL-files-1/create-the-missing-karaokes-here.bat)

Create karaoke files for all songs *in the current folder* that do not have them

### 🌟 TODO [get-karaoke-for-playlist.bat](../BAT-and-UTIL-files-1/get-karaoke-for-playlist.bat)

Create karaoke files for all songs *in a playlist* that do not have them — Traverses a playlist, running ```create-SRT``` on every file in the playlist. (In random order, to prevent alphabetical bias.)

### 🌟 TODO create-karaoke-automatically-from-approved-lyrics.bat {folder to recurse through]

Create karaoke files for all songs in a *folder tree* that do not have them, as long as their lyric file has been previously approved. This is intended so one can spend 100% of time aligning/approving lyrics (i.e. with ```get-lyrics-for-playlist.bat```), then go to bed and run this to generate everything that has pre-approved lyrics, saving the karaoke generation for another time (like when you are asleep). 

### 🌟 [create-SRT-without-lyrics-or-voice-detection-for-an-entire-folder-tree.bat](../BAT-and-UTIL-files-1/create-SRT-without-lyrics-or-voice-detection-for-an-entire-folder-tree.bat)

Rarely used, but: Creates karaoke files for all songs in a *folder tree* without using lyric files or voice detection (VAD). This is useful for folders of sound clips and small samples, where you just want to get a lot done without the extra overhead of lyrics and without the extra time delay of loading the VAD model.

____________________________________________________________________________________________________________

# Auditing Commands:

These commands find &Y obtain missing karaoke & lyric files.

### 🌟 [review-subtitles / review-all-SRTs / review-SRTs.bat / review-LRCs.bat](../BAT-and-UTIL-files-1/review-subtitles.bat)

Reviews all karaoke files in current folder, using ```print-with-columns``` to eliminate most scrolling up.

![image](https://github.com/user-attachments/assets/9b579cf2-ca93-4684-aec5-35df8c793143)


### 🌟 cfmk / [check-for-missing-karaoke](../BAT-and-UTIL-files-1/check-for-missing-karaoke.bat)

Displays a list of files in the *current folder* which are missing *karaoke* files

### 🌟 cfml / cmlf / [check-for-missing-lyrics](../BAT-and-UTIL-files-1/check-for-missing-lyrics.bat)

Displays a list of files in the *current folder* which are missing *approved lyric* files

### 🌟 Lyric Auditor: cpfml / cpmlf / [check-playlist-for-missing-lyrics](../BAT-and-UTIL-files-1/get-playlist-for-missing-lyrics.bat)

Displays a list of files in a *playlist* which are missing *approved lyric* files.


### 🌟 Karaoke Auditor: [CheckAFilelistForFilesMissingSidecarFilesOfTheProvidedExtension](../BAT-and-UTIL-files-1/check_a_filelist_for_files_missing_sidecar_files_of_the_provided_extensions.py)

Processes a playlist to create a new playlist consisting of only the songs missing karaoke files.

EXAMPLE:
```
check_a_filelist_for_files_missing_sidecar_files_of_the_provided_extensions.py PlayList.m3u *.srt;*.lrc ``CreateSRTFileWrite
```
^^^ This example goes through the file ```PlayList.m3u```, checks for all files that do not have karaoke files (i.e. no ```*.srt``` or ```*.lrc``` sidecar file), creates a ```PlayList-without lrc srt.m3u``` consisting of those files.  Bbecause the `````CreateSRTFileWrite``` option was used, it also generates a script to actually create the missing karaoke files.  The ``GetLyricsFileWrite``` option can instead be used to *ONLY* obataining lyrics, and save the karaoke generation for later.


____________________________________________________________________________________________________________


# ⚡️ [WinAmp](https://forums.winamp.com/forum/winamp/winamp-discussion/306661-winamp-5-666-released-build-3516) 🦙 Integration Commands:

These commands allows us to operate on "the song we are currently listening to" rather than a specific file or playlist.

### 🌟 [get-lyrics-for-currently-playing-song ](../BAT-and-UTIL-files-1/get-lyrics-for-currently-playing-song.bat)

Runs ```get-lyrics``` on the song currently being played in ⚡️ [WinAmp](https://forums.winamp.com/forum/winamp/winamp-discussion/306661-winamp-5-666-released-build-3516) 🦙.


### 🌟 srtthis / [create-srt-file-for-currently-playing-song.bat](../BAT-and-UTIL-files-1/create-srt-file-for-currently-playing-song.bat)

Runs ```create-srt``` on the song currently being played in ⚡️ [WinAmp](https://forums.winamp.com/forum/winamp/winamp-discussion/306661-winamp-5-666-released-build-3516) 🦙.


### 🌟 Karaoke insertion fudger - [eccsrt2lrc2clip.bat](../BAT-and-UTIL-files-1/eccsrt2lrc2clip.bat)

In certain very rare situations, [MiniLyrics](https://minilyrics.en.softonic.com/) does not auto-import the generated SRT file.  Because [MiniLyrics](https://minilyrics.en.softonic.com/) primarily uses LRC instead of SRT, it can sometimes miss an SRT. When this happens, the SRT must be converted to LRC, copied to the clipboard, and pasted into the [MiniLyrics](https://minilyrics.en.softonic.com/) lyric window manually. This script handles that by detecting the current song playing, converting it's SRT to LRC, copying it to the clipboard, and automatically opening [MiniLyrics](https://minilyrics.en.softonic.com/)'s lyric editor window. All the user has to do is paste and save.



_________________________________________

# Under-The-Hood: Critical Utility commands

Other important commands deveoped for this project.

### 🌟 [approve-lyrics / approve-lyric-file {lyric_file}](../BAT-and-UTIL-files-1/approve-lyric-file.bat) / [disapprove-lyrics / disapprove-lyric-file {lyric_file}](../BAT-and-UTIL-files-1/disapprove-lyric-file.bat)

Marks lyric file with approval/disapproval so that we can pre-approve lyric files in advance of transcription process. Uses [Alternate Data Streams](https://superuser.com/questions/186627/anybody-have-a-legitimate-use-for-alternate-data-streams-in-ntfs) to store approval tags in a database-less, file-less way.

### 🌟 [print_with_columns.py](../BAT-and-UTIL-files-1/print_with_columns.py) / [newspaper.bat](../BAT-and-UTIL-files-1/newspaper.bat)

Displays text in column ("newspaper") format so that lyric/karaoke review does not involve constantly scrolling up.

### 🌟 [google.py](../BAT-and-UTIL-files-1/google.py)

Invokes a google search in primary browser, all while properly preserving quotes. Way harder to pull off than it sounds.

### 🌟 [insert-before-each-line.py](../BAT-and-UTIL-files-1/insert-before-each-line.py) / [insert-after-each-line.py](../BAT-and-UTIL-files-1/insert-after-each-line.py)

Inserts text before or after each line of STDIN. Used for script generation. 

### 🌟 [srt2lrc.py](../BAT-and-UTIL-files-1/srt2lrc.py)

A *batch* SRT-file to LRC-file converter. Used by [eccsrt2lrc2clip.bat](../BAT-and-UTIL-files-1/eccsrt2lrc2clip.bat)

____________________________________________________________________________________________________________

# Under-The-Hood: Adjunct Utility commands

### 🌟 [srt2txt.py](../BAT-and-UTIL-files-1/srt2txt.py)

A *single-file* SRT-file to TXT-file converter

____________________________________________________________________________________________________________


# Under-The-Hood: Pre/Post-Processor Utility Commands:

Pre/Postprocessors developed for this project.

### 🌟 [get-lyrics-with-lyricsgenius-json-processor.pl](../BAT-and-UTIL-files-1/get-lyrics-with-lyricsgenius-json-processor.pl)

Extracts lyrics from our freshly-downloaded-from-Genius.com JSON files, with minimal preprocessing.


### 🌟 [unique-lines.pl](../BAT-and-UTIL-files-1/unique-lines.pl)

A lyric postprocessor that removes tons of junk from downloaded lyrics, only shows unique lines (to help fit into WhisperAI's 224-token prompt limit), and smushes all the lyrics into a single line (for use as a command line option). Started as a version of ``uniq``` that doesn't require file sorting, and grew into full-fledged lyric preprocessor.


### 🌟 [remove-period-at-ends-of-lines.pl](../BAT-and-UTIL-files-1/remove-period-at-ends-of-lines.pl)

A subtitle postprocessor that removes periods from end of each line in a subtitle. Preserves periods for words like "Mr."
We add "invisible" periods to the end of each line of lyrics so that WhisperAI's ```--sentence``` option works better. We then remove these periods (making them "invisible") afterward, because they are ugly.  Also has a side effect of de-censoring some curse words, which can be suppressed with the ```--leave-censorship``` or ```-L``` option.

____________________________________________________________________________________________________________

# Under-The-Hood: Existing commands also used by this system:

Various commands that are already a part of my "Clairevironment".

### 🌟 [askYN.bat](../BAT-and-UTIL-files-1/askYN.bat)

The Yes/No prompting system with prompt timeouts.


### 🌟 [print-message.bat](../BAT-and-UTIL-files-1/print-message.bat)

The messaging system (used by [warning.bat](../BAT-and-UTIL-files-1/warning.bat), [debug.bat](../BAT-and-UTIL-files-1/debug.bat), [error.bat](../BAT-and-UTIL-files-1/error.bat), [fatal_error.bat](../BAT-and-UTIL-files-1/fatalerror.bat), [success.bat](../BAT-and-UTIL-files-1/success.bat), [celebration.bat](../BAT-and-UTIL-files-1/celebration.bat), [important.bat](../BAT-and-UTIL-files-1/important.bat), [important_less.bat](../BAT-and-UTIL-files-1/important_less.bat), [advice](../BAT-and-UTIL-files-1/advice.bat), [unimportant](../BAT-and-UTIL-files-1/unimportant.bat), etc)


### 🌟 [copy-move-post.py](../BAT-and-UTIL-files-1/copy-move-post.py)

A cosmetic postprocessor which employes ANSI color-cycling to inbue a psychedelic effect onto text by cycling the colors of the primary text color through the visible spectrum. Originally written to postprocess the output to the ```move``` and ```copy``` commands, with a mode added explicitly for postprocessing Whisper's output into something waaaay more visually interesting.

Uses my [claire_console.py](../BAT-and-UTIL-files-1/clairecjs_utils/claire_console.py) library to achieve the color-cycling.


### 🌟 [divider.bat](../BAT-and-UTIL-files-1/display-horizontal-divider.bat)

[Pretty rainbow-ized horizontal dividers](../BAT-and-UTIL-files-1/dividers/) to separate out output into sections.


### 🌟 [delete-zero-byte-files.bat](../BAT-and-UTIL-files-1/delete-zero-byte-files.bat) {filemask} 

Deletes all 0-byte files matching a filemask. Removes 0-byte files to save us having to check EVERY file for non-zero-ness.


### 🌟 [add-ADS-tag-to-file.bat](../BAT-and-UTIL-files-1/add-ADS-tag-to-file.bat) / [remove-ADS-tag-from-file.bat](../BAT-and-UTIL-files-1/remove-ADS-tag-from-file.bat) / [display-ADS-tag-from-file.bat](../BAT-and-UTIL-files-1/display-ADS-tag-from-file.bat)

Commands for displaying tags, and for adding/removing tags to files using [Alternate Data Streams](https://superuser.com/questions/186627/anybody-have-a-legitimate-use-for-alternate-data-streams-in-ntfs). Used for lyric [dis]approval.


### 🌟 [run-piped-input-as-bat.bat](../BAT-and-UTIL-files-1/run-piped-input-as-bat.bat)

Receives piped input and runs it as if it were a BAT file. Dangerous stuff!


### 🌟 [validate-environment-variables {list of env-var names}](../BAT-and-UTIL-files-1/validate-environment-variable.bat)

Validates whether environment variables (and the files they point to!) exist.


### 🌟 [validate-in-path {list of commands}](../BAT-and-UTIL-files-1/validate-in-path.bat)

Validates whether commands (be they internal, alias, or not) are in the path


### 🌟 [validate-is-extension {filename} {list of extensions}](../BAT-and-UTIL-files-1/validate-is-extension.bat)

Validates whether a file has an acceptable file extension.  


### 🌟 [validate-is-function {list of functions}](../BAT-and-UTIL-files-1/validate-function.bat)

Validates whether a TCC user %@function is defined or not


### 🌟 [bigecho.bat](../BAT-and-UTIL-files-1/bigecho.bat)

Echos, but in VT100-double-heighttext.


### 🌟 [set-ansi.bat](../BAT-and-UTIL-files-1/set-ansi.bat)

Sets all the ansi codes we know to exist.


### 🌟 [set-emojis.bat](../BAT-and-UTIL-files-1/set-emojis.bat)

Sets all the emoji we care to set, using the [emoji.env](../BAT-and-UTIL-files-1/emoji.env) file to add new emoji.


### 🌟 [mp3index.bat](../BAT-and-UTIL-files-1/mp3index.bat)

Technically should be called "audio_file_index.bat". Prints to STDOUT a list of all songfiles (mp3, flac, wav, etc).


### 🌟 [cat_fast.exe](../BAT-and-UTIL-files-1/cat_fast.exe)

Version of ```cat.exe``` deemed to be the fastest. I have several versions of the unix ```cat``` command, but this is the one I use for speediness.


### 🌟 [change-single-quotes-to-double-apostrophes.py](../BAT-and-UTIL-files-1/change-single-quotes-to-double-apostrophes.py)

Quote conversion offloaded into python script to avoid command-line complications with quote symbols. 


### 🌟 [del-if-exists.bat](../BAT-and-UTIL-files-1/del-if-exists.bat)

Delete a file, but only if it exists.


### 🌟 [edit-currently-playing-attrib-helper.pl](../BAT-and-UTIL-files-1/edit-currently-playing-attrib-helper.pl)

Used by ```go-to-currently-playing-song-dir.bat``` to determine the folder of the current song playing. Processes the ```winamp_now_playing.txt``` file generated by the [WinampNowPlayingToFile plugin](https://github.com/Aldaviva/WinampNowPlayingToFile) to determine this information. (API calls would limit us to only using this on the same computer as [WinAmp](https://forums.winamp.com/forum/winamp/winamp-discussion/306661-winamp-5-666-released-build-3516), which is a restriction we do not want).  This is a very ad-hoc organic spaghetti script that isn'at all nice-looking, but the 2024 update branches past the ugly legacy 2008, 2009, 2012, and 2013 updates, which were all designed to work with the [Last.FM](https://www.last.fm/user/ClioCJS) logfile.

### 🌟 [go-to-currently-playing-song-dir.bat](../BAT-and-UTIL-files-1/go-to-currently-playing-song-dir.bat)

For [winamp](https://forums.winamp.com/forum/winamp/winamp-discussion/306661-winamp-5-666-released-build-3516) integration, changes current folder to same folder that the song we are listening to is in.  (The change-folder script is actually generated by [edit-currently-playing-attrib.bat](../BAT-and-UTIL-files-1/edit-currently-playing-attrib.bat))

### 🌟 [randomize-file.pl](../BAT-and-UTIL-files-1/randomize-file.pl.bat)

Scrambles the lines of STDIN.  One could think of it as shuffling/randomizing a playlist/filelist.  Used to do things in random orders.





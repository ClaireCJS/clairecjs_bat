# AI Lyric Transcription System For Windows

## Goal:

General goal: To automate AI transcription of music such that lyrics are displayed as they are sung

Specific goal: To have the [MiniLyrics](https://minilyrics.en.softonic.com/) program correctly display lyrics as they are sung.

## Terminology:

Karaoke Files: We generally call the files we generate "karaoke file", which is shorthand for "file capable of displaying the lyrics as they are sung". This includes LRC files and SRT files.  This system generates SRT files, but post-converts them to LRC in some situations.

Sidecar Files: A file of the same name, but different extension. For example, "filename.txt" is a TXT sidecar file to "filename.mp3".

## Requirements:

1. The [latest Faster-Whisper-XXL binaries](https://github.com/Purfview/whisper-standalone-win/releases/tag/Faster-Whisper-XXL). 
    The command ``faster-whisper-xxl.exe`` must be in your path.

1. [TakeCommand (TCC) command-line v31+](https://jpsoft.com/all-downloads/all-downloads.html), which can also be installed with Winget via the command: ```winget install JPSoft.tcmd```.

1. My full [Clairevironment](https://github.com/ClaireCJS/clairecjs_bat/) (this project). It is built on top of my own personal environment layer and cannot exist outside of it.  ```git.exe -clone https://github.com/ClaireCJS/clairecjs_bat/``` then move the BAT-file folder (#1, not #2) into ```c:\bat\```

1. Cygwin or other comparable version of ```sort``` and ```uniq``` utilities

1. For automatic file-trash cleanup across an entire computer, you will need the ```everything``` service to track files. (Use ```start-everything.bat``` to start it)

1. For WinAmp integration: the [WinampNowPlayingToFile plugin](https://github.com/Aldaviva/WinampNowPlayingToFile), configured so that the 2ⁿᵈ line of its output file is the full filename of the currently playing song. This allows instant no-resource any-computer access to the location of which song file is currently playing in WinAmp, allowing us to have commands that operate on "whatever song we are currently listening to".

____________________________________________________________________________________________________________

# NOTE: Many commands have several different aliases, for convenience-of-remembering.
____________________________________________________________________________________________________________

# Lyric Alignment Commands:


### [get-lyrics {songfile} / get-lyrics-for-song {songfile} / get-lyrics-via-multiple-sources {songfile}](../get-lyrics-via-multiple-sources.bat)

Obtains the lyrics for a particular song, to foster proper AI transcription. These transcriptions work much better when you have a lyric set. This checks local sidecar files, local lyric repository, Genius, and Google, to obtain lyric files with as much ease possible.

### [approve-lyrics / approve-lyric-file {lyric_file}](../approve-lyric-file.bat) / [disapprove-lyrics / disapprove-lyric-file {lyric_file}](../disapprove-lyric-file.bat)

Mark lyric file with approval/disapproval so that we can pre-approve lyric files in advance of transcription process. Uses [Alternate Data Streams](https://superuser.com/questions/186627/anybody-have-a-legitimate-use-for-alternate-data-streams-in-ntfs) to store approval tags in a database-less, file-less way.

### TODO [get-lyrics-for-playlist.bat](../get-lyrics-for-playlist.bat)

Obtain lyrics for all songs in a playlist that do not have them — Traverses a playlist, running ```get-lyrics``` on every file in the playlist. (In random order, to prevent alphabetical bias.)

____________________________________________________________________________________________________________


# Karaoke Creation Commands:


### create-srt {songfile} / [create-srt-from-file {songfile}](../create-srt-from-file.bat)

Performs the AI transcription process for a single song file.
Run without parameters to see various options, including but not limited to  "ai" (skips lyrics process), "fast" (shortens prompt timer lengths), and "force" (generate it even thoughi t already exists).


### cmk / cmkf / [create-missing-karaoke-files / create-the-missing-karaokes-here](../create-the-missing-karaokes-here.bat)

Create karaoke files for all songs *in the current folder* that do not have them

### TODO [get-karaoke-for-playlist.bat](../get-lyrics-for-playlist.bat)

Create karaoke files for all songs *in a playlist* that do not have them — Traverses a playlist, running ```create-SRT``` on every file in the playlist. (In random order, to prevent alphabetical bias.)

### TODO create-karaoke-automatically-from-approved-lyrics.bat {folder to recurse through]

Create karaoke files for all songs in a *folder tree* that do not have them, as long as their lyric file has been previously approved. This is intended so one can spend 100% of time aligning/approving lyrics (i.e. with ```get-lyrics-for-playlist.bat```), then go to bed and run this to generate everything that has pre-approved lyrics, saving the karaoke generation for another time (like when you are asleep). 



____________________________________________________________________________________________________________

# Karaoke Auditing Commands

### [review-subtitles / review-all-SRTs / review-SRTs.bat / review-LRCs.bat](../review-subtitles.bat)

Reviews all karaoke files in current folder, using ```print-with-columns``` to eliminate most scrolling up.

![image](https://github.com/user-attachments/assets/9b579cf2-ca93-4684-aec5-35df8c793143)


### cfmk / [check-for-missing-karaoke](../check-for-missing-karaoke.bat)

Displays a list of files in the current folder which are missing karaoke files


### [karaoke auditor - CheckAFilelistForFilesMissingSidecarFilesOfTheProvidedExtension](../check_a_filelist_for_files_missing_sidecar_files_of_the_provided_extensions.py)

Creates a list of files *in a playlist* which are missing their karaoke files.

EXAMPLE:
```
check_a_filelist_for_files_missing_sidecar_files_of_the_provided_extensions.py PlayList.m3u *.srt;*.lrc ``CreateSRTFileWrite
```
^^^ This example goes through the file ```PlayList.m3u```, checks for all files that do not have karaoke files (i.e. no ```*.srt``` or ```*.lrc``` sidecar file), creates a ```PlayList-without lrc srt.m3u``` consisting of those files.  Bbecause the `````CreateSRTFileWrite``` option was used, it also generates a script to actually create the missing karaoke files.  The ``GetLyricsFileWrite``` option can instead be used to *ONLY* obataining lyrics, and save the karaoke generation for later.


____________________________________________________________________________________________________________


# WinAmp Integration Commands

### [get-lyrics-for-currently-playing-song ](../get-lyrics-for-currently-playing-song.bat)

Runs ```get-lyrics``` on the song currently being played in WinAmp.


### srtthis / [create-srt-file-for-currently-playing-song.bat](../create-srt-file-for-currently-playing-song.bat)

Runs ```create-srt``` on the song currently being played in WinAmp.


### Karaoke insertion fudger - [eccsrt2lrc2clip.bat](../eccsrt2lrc2clip.bat)

In certain very rare situations, MiniLyrics does not auto-import the generated SRT file.  Because MiniLyrics primarily uses LRC instead of SRT, it can sometimes miss an SRT. When this happens, the SRT must be converted to LRC, copied to the clipboard, and pasted into the MiniLyrics lyric window manually. This script handles that by detecting the current song playing, converting it's SRT to LRC, copying it to the clipboard, and automatically opening MiniLyrics's lyric editor window. All the user has to do is paste and save.


____________________________________________________________________________________________________________


# Pre/Post-Processor Utility Commands:

### [get-lyrics-with-lyricsgenius-json-processor.pl](../get-lyrics-with-lyricsgenius-json-processor.pl)

Extracts lyrics from our freshly-downloaded-from-Genius.com JSON files, with minimal preprocessing.


### [unique-lines.pl](../unique-lines.pl)

A lyric postprocessor that removes tons of junk from downloaded lyrics, only shows unique lines (to help fit into WhisperAI's 224-token prompt limit), and smushes all the lyrics into a single line (for use as a command line option). Started as a version of ``uniq``` that doesn't require file sorting, and grew into full-fledged lyric preprocessor.


### [remove-period-at-ends-of-lines.pl](../remove-period-at-ends-of-lines.pl)

A subtitle postprocessor that removes periods from end of each line in a subtitle. Preserves periods for words like "Mr."
We add "invisible" periods to the end of each line of lyrics so that WhisperAI's ```--sentence``` option works better. We then remove these periods (making them "invisible") afterward, because they are ugly.  Also has a side effect of de-censoring some curse words, which can be suppressed with the ```--leave-censorship``` or ```-L``` option.

_________________________________________

# Other Critical Utility commands

### [print_with_columns.py](../print_with_columns.py) / [newspaper.bat](../newspaper.bat)

Displays text in column ("newspaper") format so that lyric/karaoke review does not involve constantly scrolling up.

### [google.py](../google.py)

Invokes a google search in primary browser, all while properly preserving quotes. Way harder to pull off than it sounds.

### [insert-before-each-line.py](../insert-before-each-line.py) / [insert-after-each-line.py](../insert-after-each-line.py)

Inserts text before or after each line of STDIN. Used for script generation. 

### [srt2lrc.py](../srt2lrc.py)

A *batch* SRT-file to LRC-file converter. Used by [eccsrt2lrc2clip.bat](../eccsrt2lrc2clip.bat)

____________________________________________________________________________________________________________


# Adjunct Utility commands

### [srt2txt.py](../srt2txt.py)

A *single-file* SRT-file to TXT-file converter

____________________________________________________________________________________________________________

# Existing commands also used by this system:

Various commands that are already a part of my "Clairevironment".


### [askYN.bat](../askYN.bat)

The Yes/No prompting system with prompt timeouts.


### [print-message.bat](../print-message.bat)

The messaging system (used by [warning.bat](../warning.bat), [debug.bat](../debug.bat), [error.bat](../error.bat), [fatal_error.bat](../fatalerror.bat), [success.bat](../success.bat), [celebration.bat](../celebration.bat), [important.bat](../important.bat), [important_less.bat](../important_less.bat), [advice](../advice.bat), [unimportant](../unimportant.bat), etc)


### [copy-move-post.py](../copy-move-post.py)

A cosmetic postprocessor which employes ANSI color-cycling to inbue a psychedelic effect onto text by cycling the colors of the primary text color through the visible spectrum. Originally written to postprocess the output to the ```move``` and ```copy``` commands, with a mode added explicitly for postprocessing Whisper's output into something waaaay more visually interesting.

Uses my [claire_console.py](../clairecjs_utils/claire_console.py) library to achieve the color-cycling.


### [divider.bat](../display-horizontal-divider.bat)

[Pretty rainbow-ized horizontal dividers](../dividers/) to separate out output into sections.


### [delete-zero-byte-files.bat](../delete-zero-byte-files.bat) {filemask} 

Deletes all 0-byte files matching a filemask. Removes 0-byte files to save us having to check EVERY file for non-zero-ness.


### [add-ADS-tag-to-file.bat](../add-ADS-tag-to-file.bat) / [remove-ADS-tag-from-file.bat](../remove-ADS-tag-from-file.bat) / [display-ADS-tag-from-file.bat](../display-ADS-tag-from-file.bat)

Commands for displaying tags, and for adding/removing tags to files using [Alternate Data Streams](https://superuser.com/questions/186627/anybody-have-a-legitimate-use-for-alternate-data-streams-in-ntfs). Used for lyric [dis]approval.


### [run-piped-input-as-bat.bat](../run-piped-input-as-bat.bat)

Receives piped input and runs it as if it were a BAT file. Dangerous stuff!


### [validate-environment-variables {list of env-var names}](../validate-environment-variable.bat)

Validates whether environment variables (and the files they point to!) exist.


### [validate-in-path {list of commands}](../validate-in-path.bat)

Validates whether commands (be they internal, alias, or not) are in the path


### [validate-is-extension {filename} {list of extensions}](../validate-is-extension.bat)

Validates whether a file has an acceptable file extension.  


### [validate-is-function {list of functions}](../validate-function.bat)

Validates whether a TCC user %@function is defined or not


### [bigecho.bat](../bigecho.bat)

Echos, but in VT100-double-heighttext.


### [set-ansi.bat](../set-ansi.bat)

Sets all the ansi codes we know to exist.


### [set-emojis.bat](../set-emojis.bat)

Sets all the emoji we care to set, using the [emoji.env](../emoji.env) file to add new emoji.


### [mp3index.bat](../mp3index.bat)

Technically should be called "audio_file_index.bat". Prints to STDOUT a list of all songfiles (mp3, flac, wav, etc).


### [cat_fast.exe](../cat_fast.exe)

Version of ```cat.exe``` deemed to be the fastest. I have several versions of the unix ```cat``` command, but this is the one I use for speediness.


### [change-single-quotes-to-double-apostrophes.py](../change-single-quotes-to-double-apostrophes.py)

Quote conversion offloaded into python script to avoid command-line complications with quote symbols. 


### [del-if-exists.bat](../del-if-exists.bat)

Delete a file, but only if it exists.







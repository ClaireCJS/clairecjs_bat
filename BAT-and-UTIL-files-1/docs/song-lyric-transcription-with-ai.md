# AI Lyric Transcription System For Windows

## Goal

General goal: To automate AI transcription of music such that lyrics are displayed as they are sung

Specific goal: To have the [MiniLyrics](https://minilyrics.en.softonic.com/) program correctly display lyrics as they are sung.

## Terminology

Karaoke Files: We generally call the files we generate "karaoke file", which is shorthand for "file capable of displaying the lyrics as they are sung". This includes LRC files and SRT files.  This system generates SRT files, but post-converts them to LRC in some situations.

Sidecar Files: A file of the same name, but different extension. For example, "filename.txt" is a TXT sidecar file to "filename.mp3".

## Requirements

1. The [latest Faster-Whisper-XXL binaries](https://github.com/Purfview/whisper-standalone-win/releases/tag/Faster-Whisper-XXL). 
    The command ``faster-whisper-xxl.exe`` must be in your path.

1. [TakeCommand (TCC) command-line v31+](https://jpsoft.com/all-downloads/all-downloads.html). 
    Can also install with Winget with the command: ```winget install JPSoft.tcmd```.

1. My full [Clairevironment](https://github.com/ClaireCJS/clairecjs_bat/) (this project). It is built on top of my own personal environment layer and cannot exist outside of it.

1. For WinAmp integration: the [WinampNowPlayingToFile plugin](https://github.com/Aldaviva/WinampNowPlayingToFile), configured so that the 2ⁿᵈ line of its output file is the full filename of the currently playing song. This allows instant no-resource any-computer access to the location of which song file is currently playing in WinAmp, allowing us to have commands that operate on "whatever song we are currently listening to".


## Lyric Commands:

Many commands have several different aliases, for convenience-of-remembering.

# get-lyrics {songfile} / get-lyrics-for-song  {songfile}

Obtains the lyrics for a particular song, to foster proper AI transcription. These transcriptions work much better when you have a lyric set. This checks local sidecar files, local lyric repository, Genius, and Google, to obtain lyric files with as muche ase as possible.


## Karaoke Commands:


# create-srt {songfile} / create-srt-from-file {songfile}

Performs the AI transcription process for a single song file.
Run without parameters to see various options, including but not limited to  "ai" (skips lyrics process), "fast" (shortens prompt timer lengths), and "force" (generate it even thoughi t already exists).


# cfmk / check-for-missing-karaoke

Displays a list of files in the current folder which are missing karaoke files

# cmk / cmkf / create-missing-karaoke-files / create-the-missing-karaokes-here

Create all missing karaokes in the current folder



## WinAmp Integration Commands

# get-lyrics-for-currently-playing-song 

Runs ```get-lyrics``` on the song currently being played in WinAmp.


# srtthis / create-srt-file-for-currently-playing-song.bat

Runs ```create-srt``` on the song currently being played in WinAmp.





## Audit & Fudge Commands


# karaoke auditor

Audits a filelist to see which files in that filelist do not have karaoke files associated with them.  Is used by ```check-for-missing-karaoke-files```, but can be used for other purposes via:

```
check_a_filelist_for_files_missing_a_sidecar_files_of_the_provided_extensions.py PlayList.m3u *.srt;*.lrc createsrtfilewrite
```

This example goes through the filelist file ```PlayList.m3u``` and checks for all files that do not have ```*.srt``` or ```*.lrc``` sidecar files. When ```createsrtfilewrite``` option is used, it generates a script to create the missing karaoke.  This is what ```create-missing-karaoke-files``` uses to create it script.

#  Karaoke insertion fudger - eccsrt2lrc2clip.bat

In certain very rare situations, MiniLyrics does not auto-import the generated SRT file.  Because MiniLyrics primarily uses LRC instead of SRT, it can sometimes miss an SRT. When this happens, the SRT must be converted to LRC, copied to the clipboard, and pasted into the MiniLyrics lyric window manually. This script handles that by detecting the current song playing, converting it's SRT to LRC, copying it to the clipboard, and automatically opening MiniLyrics's lyric editor window. All the user has to do is paste and save.


## Utility commands

# srt2txt.py

A SRT-file to TXT-file converter

# [google.py](..\google.py)

Invokes a google search in primary browser, all while properly preserving quotes. Way harder to pull off than it sounds.

# insert-[before|after]-each-line.py

Inserts text before or after each line of STDIN. Used for script generation. 

# unique-lines.pl

A lyric postprocessor that removes tons of junk from downloaded lyrics, only shows unique lines (to help fit into WhisperAI's 224-token prompt limit), and smushes all the lyrics into a single line (for use as a command line option). Started as a version of ``uniq``` that doesn't require file sorting, and grew into full-fledged lyric preprocessor.


# remote-period-at-ends-of-lines.pl

Postprocessor Perl script to remove periods from end of each line in a subtitle. Preserves periods for words like "Mr."
We add "invisible" periods to the end of each line of lyrics so that WhisperAI's ```--sentence`` option works better. We then remove these periods (making them "invisible") afterward, because they are ugly.  Also has a side effect of de-censoring some curse words, which can be suppressed with the ```--leave-censorship``` or ```-L``` option.


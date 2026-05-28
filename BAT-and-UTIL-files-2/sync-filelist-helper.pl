#!perl

#USAGE: sync-filelist-helper.pl FILELIST.txt D:\DESTINATION\FOLDER\
#USAGE: Refer to code for controlling behavior via environment variable or via trigger file


#HISTORY: This is the generalized 2ⁿᵈ edition of the more-specialized “sync-mp3-playlists-to-location-helper.pl”, which only sync’ed playlists [and not the files], whereas this usually/also sync audio files.



##### CONFIGURATION: BEHAVIOR:

my $COPY_SIDECARS                      = 1;							#set to “1” to copy sidecar files (i.e. subtitles, art, lyrics, any file with same base but diff extension)
my $PUT_EACH_SONG_IN_RANDOM_FOLDER     = 0;							#set to “1” for each file to be individually copied to a random folder name, which allows a smulated shuffle on the MANY standalone speakers (almost all of them) that don’t have shuffle functionality
my $COLLAPSE_FILES_TO_ROOT_WHEN_DONE   = 0;							#set to “1” to move all files to the root folder when done; useful for players that can only do random in a single folder
my $COPY_FLACS                         = 1;							#set to “0” to not copy FLAC files, if you are dealing with an older player that doesn’t support them
my $COPY_IF_TARGET_FILE_EXISTS         = 1;							#set to “1” to run the copy /u command on target files even if they exist. Although this won’t copy if the file is the same, the comparison to determine that takes time, and this can REALLLLLLLLY slow down an update that may only be 1% of the files to take possibly as long as the same amount of time for updating 100% of the files... So we usually keep this set to 0!

##### CONFIGURATION: INTERNALS:

my $COPY                           = "*copy /u /g /h /j /k /Nst";	#set to “copy” if you must - but for me, /u makes it an update copy, which only copies if the file is newer. Significantly saves time. /g=percentage progress. /h=copy hidden, /j=restartable, /Ns=no summary ("1 file copied" suppressed), no updating JPSTREE.IDX
my $MKDIR                          = "mkdir /s /Nt";				#set to   “md” if you must - but you're gonna need to add whatver option lets you this make multiple folders inside each other at once, i.e. creating "c:\one\two\three\four" in one command, not four.  The /Nt is a TCC-specific speedup.
my $SLASH                          = "\\";							#set to    “/” if you must [Unix folk]
my $ALLOW_COPY_TO_SAME_DRIVE       = 0;								#set to “1" if you want to allow copy to the same harddrive, WHICH CAN BE REALLY BAD, this was set to 0 for my own protection...  HISTORY: 2025/06/21 - changed this back to original inception value of 0 after a disaster .... 2022/03/17 - changed this to 1 for testing purposes ... original pre-2022 inception value was 0
my $BACKSLASHES                    = 1;								#set to 1 if you want all filename slashes to be turned into backslashes (usually better for Windows)


# ✨✨✨✨✨✨✨ ALTERNATE WAYS TO PASS PARAMETERS - BY ENVIRONMENT VARIABLE AND BY TRIGGER FILE ✨✨✨✨✨✨✨
# ✨✨✨✨✨✨✨ ALTERNATE WAYS TO PASS PARAMETERS - BY ENVIRONMENT VARIABLE AND BY TRIGGER FILE ✨✨✨✨✨✨✨
# ✨✨✨✨✨✨✨ ALTERNATE WAYS TO PASS PARAMETERS - BY ENVIRONMENT VARIABLE AND BY TRIGGER FILE ✨✨✨✨✨✨✨

##### ENVIRONMENT VARIABLE BEHAVIOR ARGUMENTS, WHICH OVERRIDE COMMAND-LINE ARGUMENTS:

if ("1" == "$ENV{PUT_EACH_SONG_IN_RANDOM_FOLDER}"         ) { $PUT_EACH_SONG_IN_RANDOM_FOLDER   = 1; }			
if ("1" == "$ENV{DO_PUT_EACH_SONG_IN_RANDOM_FOLDER}"      ) { $PUT_EACH_SONG_IN_RANDOM_FOLDER   = 1; }			
if ("1" == "$ENV{DONT_PUT_EACH_SONG_IN_RANDOM_FOLDER}"    ) { $PUT_EACH_SONG_IN_RANDOM_FOLDER   = 0; }			
if ("1" == "$ENV{DO_NOT_PUT_EACH_SONG_IN_RANDOM_FOLDER}"  ) { $PUT_EACH_SONG_IN_RANDOM_FOLDER   = 0; }			
if ("1" == "$ENV{COLLAPSE_FILES_TO_ROOT_WHEN_DONE}"       ) { $COLLAPSE_FILES_TO_ROOT_WHEN_DONE = 1; }
if ("1" == "$ENV{DO_COLLAPSE_FILES_TO_ROOT_WHEN_DONE}"    ) { $COLLAPSE_FILES_TO_ROOT_WHEN_DONE = 1; }
if ("1" == "$ENV{DONT_COLLAPSE_FILES_TO_ROOT_WHEN_DONE}"  ) { $COLLAPSE_FILES_TO_ROOT_WHEN_DONE = 0; }
if ("1" == "$ENV{DO_NOT_COLLAPSE_FILES_TO_ROOT_WHEN_DONE}") { $COLLAPSE_FILES_TO_ROOT_WHEN_DONE = 0; }
if ("1" == "$ENV{COPY_IF_TARGET_FILE_EXISTS}"             ) { $COPY_IF_TARGET_FILE_EXISTS       = 1; }			
if ("1" == "$ENV{DO_COPY_IF_TARGET_FILE_EXISTS}"          ) { $COPY_IF_TARGET_FILE_EXISTS       = 1; }			
if ("1" == "$ENV{DONT_COPY_IF_TARGET_FILE_EXISTS}"        ) { $COPY_IF_TARGET_FILE_EXISTS       = 0; }			
if ("1" == "$ENV{DO_NOT_COPY_IF_TARGET_FILE_EXISTS}"      ) { $COPY_IF_TARGET_FILE_EXISTS       = 0; }			
if ("1" == "$ENV{COPY_SIDECARS}"                          ) { $COPY_SIDECARS                    = 1; }
if ("1" == "$ENV{DO_COPY_SIDECARS}"                       ) { $COPY_SIDECARS                    = 1; }
if ("1" == "$ENV{DONT_COPY_SIDECARS}"                     ) { $COPY_SIDECARS                    = 0; }
if ("1" == "$ENV{DO_NOT_COPY_SIDECARS}"                   ) { $COPY_SIDECARS                    = 0; }
if ("1" == "$ENV{COPY_FLACS}"                             ) { $COPY_FLACS                       = 1; }
if ("1" == "$ENV{DO_COPY_FLACS}"                          ) { $COPY_FLACS                       = 1; }
if ("1" == "$ENV{DONT_COPY_FLACS}"                        ) { $COPY_FLACS                       = 0; }
if ("1" == "$ENV{DO_NOT_COPY_FLACS}"                      ) { $COPY_FLACS                       = 0; }

##### GET FILESYSTEM ARGUMENTS, WHICH OVERRIDE ENVIRONMENT VARIABLE ARGUMENTS:
if (-e "$destinationDriveLetter:\__ mp3 sync option - collapse __") { $COLLAPSE_FILES_TO_ROOT_WHEN_DONE = 1; }
if (-e "$destinationDriveLetter:\__ each song in random folder __") { $PUT_EACH_SONG_IN_RANDOM_FOLDER   = 1; }

# ✨✨✨✨✨✨✨ ALTERNATE WAYS TO PASS PARAMETERS - BY ENVIRONMENT VARIABLE AND BY TRIGGER FILE ✨✨✨✨✨✨✨
# ✨✨✨✨✨✨✨ ALTERNATE WAYS TO PASS PARAMETERS - BY ENVIRONMENT VARIABLE AND BY TRIGGER FILE ✨✨✨✨✨✨✨
# ✨✨✨✨✨✨✨ ALTERNATE WAYS TO PASS PARAMETERS - BY ENVIRONMENT VARIABLE AND BY TRIGGER FILE ✨✨✨✨✨✨✨


##### GET COMMAND-LINE ARGUMENTS:
my $filelist               =  $ARGV[0];
my $destination            =  $ARGV[1];
   $destination            =~ s/^"//g;
   $destination            =~ s/"$//g;
my $destinationDriveLetter =  $destination;
   $destinationDriveLetter =~ s/^"//g;
   $destinationDriveLetter =~ s/"$//g;
   $destinationDriveLetter =~ s/^(.).*$/$1/;		#just the letter, no colon afterward

##### VALIDATE COMMAND-LINE ARGUMENTS:
if (!-e $filelist)    { die("FATAL ERROR: $filelist"    . "doesn't exist!\nBe careful! Some devices are case-sensitive!\n\n"); }
if (!-d $destination) { die("FATAL ERROR: $destination" . "doesn't exist!\nBe careful! Some devices are case-sensitive!\n\n"); }

##### DETERMINE FOLDER DIVIDER CHARACTER:
my $DIVIDER                  = "/" ;
if ($BACKSLASHES) { $DIVIDER = "\\"; } 

##### READ IN FILELIST:
open      (FILELIST,"$filelist") || die("FATAL ERROR: could not open $filelist\n\n");
my @FILES=<FILELIST>;
close     (FILELIST);

##### TRAVERSE FILELIST:
use strict;
my $folder="";
my $newfile="";
my $fileonly="";
my $newFolder="";
my $COMMANDSET="";
my $driveLetterAfter="";
my $driveLetterBefore="";
my %FOLDERS_CREATED=();
my @QUEUEDCOMMANDS =();
print "\@Echo OFF\n";
print "call car.bat\n";		# protection against filenames with caret (“^”) symbol in them 
print "rem * destinationDrive is \"$destinationDriveLetter\"\n\n";
print "echo \%ANSI_COLOR_IMPORTANT\%* Making directories...\%ANSI_COLOR_NORMAL\% \n\n";
my $file;
my $file_without_extension;
my $filenum=0;
foreach $file (@FILES) {
	next if $file =~ /^#EXT/;
	chomp $file;
	$filenum++;
	print "\n\nrem ************ processing file $filenum $file ***************** \n ";

	if ($BACKSLASHES) { $file =~ s/\//\\/g; }			# Convert filename to backslashes, if necessary

	##### Separate source folder and source filename:
	$folder   = $file;
	$fileonly = $file;
	$folder   =~ s/^(.*[\\\/])([^\\\/]*$)/$1/i;
	$fileonly =~ s/^(.*[\\\/])([^\\\/]*$)/$2/i;
	$file =~ s/^([\\\/])/C:$1/;									    #add C: to beginning of entries with no drive letter - THIS COULD BE VERY PROBLEMATIC IN THE LONG RUN. MIGHT WANT TO MAKE THIS ENV-VAR CONTROLLABLE LATER, IF THAT BECOMES A PROBLEM.

	$file_without_extension = $file;
	$file_without_extension =~ s/\..{2,5}$//g;
	#DEBUG: print "rem File without extension is $file_without_extension\n";

	##### Transform source folder into destination folder:			#UPDATES TO CODE GENERALLY WILL BE IN THIS SECTION
		##### WARNING! CLAIREVIRONMENT [sorta kinda] REQUIRES ANY UPDATES TO BELOW TO ALSO BE MADE TO SYNC-MP3-PLAYLISTS-TO-LOCATION-HELPER.PL, which is the original deprecated version of this
		##### WARNING! CLAIREVIRONMENT [sorta kinda] REQUIRES ANY UPDATES TO BELOW TO ALSO BE MADE TO SYNC-MP3-PLAYLISTS-TO-LOCATION-HELPER.PL, which is the original deprecated version of this
		##### WARNING! CLAIREVIRONMENT [sorta kinda] REQUIRES ANY UPDATES TO BELOW TO ALSO BE MADE TO SYNC-MP3-PLAYLISTS-TO-LOCATION-HELPER.PL, which is the original deprecated version of this
		##### WARNING! CLAIREVIRONMENT [sorta kinda] REQUIRES ANY UPDATES TO BELOW TO ALSO BE MADE TO SYNC-MP3-PLAYLISTS-TO-LOCATION-HELPER.PL, which is the original deprecated version of this
		##### WARNING! CLAIREVIRONMENT [sorta kinda] REQUIRES ANY UPDATES TO BELOW TO ALSO BE MADE TO SYNC-MP3-PLAYLISTS-TO-LOCATION-HELPER.PL, which is the original deprecated version of this
		##### WARNING! CLAIREVIRONMENT [sorta kinda] REQUIRES ANY UPDATES TO BELOW TO ALSO BE MADE TO SYNC-MP3-PLAYLISTS-TO-LOCATION-HELPER.PL, which is the original deprecated version of this
		##### WARNING! CLAIREVIRONMENT [sorta kinda] REQUIRES ANY UPDATES TO BELOW TO ALSO BE MADE TO SYNC-MP3-PLAYLISTS-TO-LOCATION-HELPER.PL, which is the original deprecated version of this
		##### WARNING! CLAIREVIRONMENT [sorta kinda] REQUIRES ANY UPDATES TO BELOW TO ALSO BE MADE TO SYNC-MP3-PLAYLISTS-TO-LOCATION-HELPER.PL, which is the original deprecated version of this
		##### WARNING! CLAIREVIRONMENT [sorta kinda] REQUIRES ANY UPDATES TO BELOW TO ALSO BE MADE TO SYNC-MP3-PLAYLISTS-TO-LOCATION-HELPER.PL, which is the original deprecated version of this
		##### WARNING! CLAIREVIRONMENT [sorta kinda] REQUIRES ANY UPDATES TO BELOW TO ALSO BE MADE TO SYNC-MP3-PLAYLISTS-TO-LOCATION-HELPER.PL, which is the original deprecated version of this
		##### WARNING! CLAIREVIRONMENT [sorta kinda] REQUIRES ANY UPDATES TO BELOW TO ALSO BE MADE TO SYNC-MP3-PLAYLISTS-TO-LOCATION-HELPER.PL, which is the original deprecated version of this
		##### WARNING! CLAIREVIRONMENT [sorta kinda] REQUIRES ANY UPDATES TO BELOW TO ALSO BE MADE TO SYNC-MP3-PLAYLISTS-TO-LOCATION-HELPER.PL, which is the original deprecated version of this
		##### WARNING! CLAIREVIRONMENT [sorta kinda] REQUIRES ANY UPDATES TO BELOW TO ALSO BE MADE TO SYNC-MP3-PLAYLISTS-TO-LOCATION-HELPER.PL, which is the original deprecated version of this
		##### WARNING! CLAIREVIRONMENT [sorta kinda] REQUIRES ANY UPDATES TO BELOW TO ALSO BE MADE TO SYNC-MP3-PLAYLISTS-TO-LOCATION-HELPER.PL, which is the original deprecated version of this
		##### WARNING! CLAIREVIRONMENT [sorta kinda] REQUIRES ANY UPDATES TO BELOW TO ALSO BE MADE TO SYNC-MP3-PLAYLISTS-TO-LOCATION-HELPER.PL, which is the original deprecated version of this
		##### WARNING! CLAIREVIRONMENT [sorta kinda] REQUIRES ANY UPDATES TO BELOW TO ALSO BE MADE TO SYNC-MP3-PLAYLISTS-TO-LOCATION-HELPER.PL, which is the original deprecated version of this
		##### WARNING! CLAIREVIRONMENT [sorta kinda] REQUIRES ANY UPDATES TO BELOW TO ALSO BE MADE TO SYNC-MP3-PLAYLISTS-TO-LOCATION-HELPER.PL, which is the original deprecated version of this

						 
	$newFolder =  $folder;
	$newFolder =~ s/[A-Z]?:?\\new\\music\\changerrecent\\/$destination/ig;									
	$newFolder =~ s/[A-Z]?:?\\new\\music\\/$destination/ig;									
	$newFolder =~ s/[A-Z]?:?\\_PROCESSING\\/$destination/ig;									
	$newFolder =~ s/[A-Z]?:?[\\\/]testing([\\\/])J?1 - ONEDIR JUDGE WITH CAROLYN/$destination$1MISC/gi;		#special case, not the best line to copy-paste for other transformations
	$newFolder =~ s/[A-Z]?:?[\\\/]testing([\\\/])J?2 - ALREADY-IN-ATTRIB-BUT-NEED-JUDGMENT-WITH-CAROLYN/$destination$1MISC/gi;		#special case, not the best line to copy-paste for other transformations
	$newFolder =~ s/[A-Z]?:?[\\\/]testing([\\\/])/$destination/gi;
	$newFolder =~ s/[A-Z]?:?[\\\/]media[\\\/]mp3-processing[\\\/]check4norm[\\\/]changerrecent[\\\/]/$destination/gi;
	$newFolder =~ s/[A-Z]?:?[\\\/]media[\\\/]mp3-processing[\\\/]CHECK4~1[\\\/]changerrecent[\\\/]/$destination/gi;
	$newFolder =~ s/[A-Z]?:?[\\\/]media[\\\/]MP3-PR~1[\\\/]CHECK4~1[\\\/]changerrecent[\\\/]/$destination/gi;
	$newFolder =~ s/[A-Z]?:?[\\\/]media[\\\/]mp3-processing[\\\/]check4norm[\\\/]NEXT[\\\/]/$destination/gi;
	$newFolder =~ s/[A-Z]?:?[\\\/]media[\\\/]mp3-processing[\\\/]check4norm[\\\/]NEXT.INPROGRESS[\\\/]/$destination/gi;
	$newFolder =~ s/[A-Z]?:?[\\\/]media[\\\/]mp3-processing[\\\/]CHECK4~1[\\\/]NEXT.INPROGRESS[\\\/]/$destination/gi;
	$newFolder =~ s/[A-Z]?:?[\\\/]media[\\\/]MP3-PR~1[\\\/]CHECK4~1[\\\/]NEXT.INPROGRESS[\\\/]/$destination/gi;
	$newFolder =~ s/[A-Z]?:?[\\\/]Converted Audio Files[\\\/]NEXT.INPROGRESS[\\\/]/$destination/gi;
	$newFolder =~ s/[A-Z]?:?[\\\/]new[\\\/]/$destination/gi;
	$newFolder =~ s/[A-Z]?:?[\\\/]media[\\\/]mp3-processing[\\\/]check4norm[\\\/]/$destination/gi;
	$newFolder =~ s/[A-Z]?:?[\\\/]media[\\\/]mp3-processing[\\\/]CHECK4~1[\\\/]/$destination/gi;
	$newFolder =~ s/[A-Z]?:?[\\\/]media[\\\/]MP3-PR~1[\\\/]CHECK4~1[\\\/]/$destination/gi;
	$newFolder =~ s/[A-Z]?:?[\\\/]media[\\\/]mp3-processing[\\\/]READY-FOR-TAGGING[\\\/]in base attrib correctly,but untagged \(KEEP IN THIS FOLDER WHEN MOVING TO TESTING\)/$destination/gi;
	$newFolder =~ s/[A-Z]?:?[\\\/]media[\\\/]mp3-processing[\\\/]READY-FOR-TAGGING[\\\/]/$destination/gi;	
	$newFolder =~ s/[\\\/]Converted Audio Files[\\\/]/\\/gi;
	$newFolder =~ s/[\\\/]NEXT.INPROGRESS[\\\/]/\\/gi;
	$newFolder =~ s/[A-Z]?:?[\\\/]CHECK4~1[\\\/]NEXT[\\\/]/$destination/gi;
	$newFolder =~ s/[A-Z]?:?[\\\/]CHECK4~1[\\\/]NEXT.INPROGRESS[\\\/]/$destination/gi;
	$newFolder =~ s/[A-Z]?:?[\\\/]CHECK4~1[\\\/]NEXT-A~1[\\\/]/$destination/gi;
	$newFolder =~ s/[A-Z]?:?[\\\/]CHECK4~1[\\\/]/$destination/gi;
	$newFolder =~ s/[A-Z]?:?[\\\/]mp3/$destination/gi;							# 20140819 moved to end
	$newFolder =~ s/[\\\/][\\\/]/$SLASH/g;										# fix extra slash deposits made by anything above
	$newFolder =~ s/CAROLYN-PROCESS[^\\\/]*//;

	### Do these after the last	ones:
	$newFolder =~ s/\Qc:$destination\E/$destination/i;							# strip c: off beginning of destination is after it, i.e. if destination was g:\, convert “c:g:” ➜ “g:”
	$newFolder =~ s/\Q$destination$destination\E/$destination/i;				# convert repeating drive letters i.e. “g:\g:\g:\” ➜ “g:\” ... use \Q and \E to prevent filenames from being interpreted as regexes
	$newFolder =~ s/^(.*)([A-Z]:.*$)/$2/;										# Because we don't branch for each of the above substitutions, sometimes we end up with the target folder prefixing twice
	$newFolder =~ s/\\mp3music\\/\\mp3\\/ig;									# Because we don't branch for each of the above substitutions, sometimes we end up with the target folder prefixing twice
	
	#### All the above $newFolder might be for nothing, because if we set this optin, this is what’s supposed to happen:
    if ($PUT_EACH_SONG_IN_RANDOM_FOLDER) {
        # build a 16-char random string from 0–9, a–z
        my @chars    = ('0'..'9','a'..'z');
        my $randdir = join '', map { $chars[ int rand @chars ] } 1..16;
        $newFolder  = $destination . $SLASH . $randdir;							# that becomes your only subfolder under the main $destination
        $newFolder  = $destination . $SLASH . $randdir;							# that becomes your only subfolder under the main $destination
    }
	print "\@rem      *** DEBUG: newFolder for “$folder” is “$newFolder” ***\n";

	##### Sanity check for missing folder substitution patterns:
	$driveLetterBefore =    $folder; $driveLetterBefore =~ s/^(.).*$/$1/;
	$driveLetterAfter  = $newFolder; $driveLetterAfter  =~ s/^(.).*$/$1/;
	if (!$ALLOW_COPY_TO_SAME_DRIVE) {
		if (uc($driveLetterBefore) eq uc($driveLetterAfter)) { print "echo ERROR=copying to same drive makes no sense for $folder to $newFolder!\n\ncall alarmbeep\n\npause\n\n"; }
	}

	##### Create target filename:
	if ($COPY_SIDECARS) {
		if ($COLLAPSE_FILES_TO_ROOT_WHEN_DONE==0) { $newfile =               "$newFolder"; }
		if ($COLLAPSE_FILES_TO_ROOT_WHEN_DONE==1) { $newfile = "$destinationDriveLetter:$DIVIDER"; }		
	} else {
		if ($COLLAPSE_FILES_TO_ROOT_WHEN_DONE==0) { $newfile =               "$newFolder$DIVIDER$fileonly"; }
		if ($COLLAPSE_FILES_TO_ROOT_WHEN_DONE==1) { $newfile = "$destinationDriveLetter:$DIVIDER$fileonly"; }		
	}
	$newfile =~ s/\\\\/\\/g;																				#erase consecutive dupe folder dividers
	$newfile =~ s/\/\//\//g;																				#erase consecutive dupe folder dividers

	##### INITIALIZE OUR STORED COMMANDS:
	$COMMANDSET = "\n\n\n\n";

	##### Create destination folder, only if necessary:
	$COMMANDSET .= "if not isdir \"$newFolder\"      ($MKDIR \"$newFolder\")\n";							#UNIX people may need to change this!

	##### Copy the file:
	   $file =~ s/\%/%%/g;																					#if file has percent in it, which it really shouldn’t
	$newfile =~ s/\%/%%/g;																					#if file has percent in it, which it really shouldn’t
	$COMMANDSET .= "SET LASTFILE=$file\n";
	$COMMANDSET .= "if \%\@DISKFREE[$destinationDriveLetter:] lt \%\@FILESIZE[\"$file\"] goto :Full\n";
	$COMMANDSET .= "if \"\%\@READY[$destinationDriveLetter:]\" == \"0\" gosub :NotReady\n";
	$COMMANDSET .= "if not exist \"$file\" (call warning \"File does not exist [but maybe you moved it]: '$file'\")\n";

	if (($COPY_FLACS==0) && ($file =~ /\.flac$/i)) {
		$COMMANDSET .= "echo.\n";
		$COMMANDSET .= "\%COLOR_WARNING\% \%+ echo NOT copying FLAC file: \"$file\" \%+ \%COLOR_NORMAL\% \n";
	} else {
	    $COMMANDSET .= "iff exist \"$file\" then\n";										# only copy the file if it exists


		if (!$COPY_IF_TARGET_FILE_EXISTS) { $COMMANDSET .= "        iff not exist \"$newfile\" then \n";	}					# only copy if the target does not exist

				$COMMANDSET .= "                echo.\nechos \%\@ANSI_RANDFG_SOFT[]\%\@RANDCURSOR[]\%\@char[9959] ``\n";
						if ($COPY_SIDECARS) { $COMMANDSET .= "                $COPY \"$file_without_extension.*\" \"$newfile\"\n"; }
						else                { $COMMANDSET .= "                $COPY \"$file\" "         .        "\"$newfile\"\n"; }
				$COMMANDSET .= "                delay /m 100\n";									# slight delay to not quote go 100% of the time				
				$COMMANDSET .= "                call status-bar $destinationDriveLetter:\n";

		if (!$COPY_IF_TARGET_FILE_EXISTS) { $COMMANDSET .= "        endiff\n"; }

	    $COMMANDSET .= "endiff\n";
	}
	push(@QUEUEDCOMMANDS,$COMMANDSET);
	#DEBUG: print "file=$file\nfolderOLD=$folder\nfolderNEW=$newFolder\nfileonly=$fileonly\nnewfile=$newfile\n\n";
}


##### Randomize the copies, so that if we run out of space, we get a random sampling of everything we attempted to copy
print "\nREM (randomizing array: begin)\n";
use List::Util qw(shuffle);
my @QUEUEDCOMMANDSRANDOM = shuffle(@QUEUEDCOMMANDS);			
print "\nREM (randomizing array: end)\n";
my $total_files=@QUEUEDCOMMANDSRANDOM;
my $remain=$total_files;
my $filenum=1;
foreach my $command (@QUEUEDCOMMANDSRANDOM) { 
	print $command; 
	#print "\%COLOR_LESS_IMPORTANT\% \%+ echo * Files remaining: \%\@COMMA[" . $filenum . "] \%+ \%COLOR_NORMAL\% \n\n"; 
	$remain = $total_files - $filenum;
	#print "set  DISPLAY_FREE_SPACE_AS_LOCKED_MESSAGE_ADDITIONAL_MESSAGE= \%BLINK_ON\%\%\@CHAR[9679]\%BLINK_OFF\% \%ITALICS_ON\%" . $remain . "\%ITALICS_OFF\% files remaining\n";
	#print "call status-bar \"\%DISPLAY_FREE_SPACE_AS_LOCKED_MESSAGE_ADDITIONAL_MESSAGE\%\"\n";
	#print "call display-free-space-as-locked-message $destinationDriveLetter\n";
	#this was ugly: print "call status-bar unlock\n";
	$filenum++;
}


print "\n\n";
print "goto :END\n\n";




##### Subroutine for if we run out of space:
print "    :Full\n";
print "        echo.\n";
print "        echo.\n";
print "        echo ..... Annnnnd we're out of space! (ERRORLEVEL=\%ERRORLEVEL\%)\n";
print "        echo ..... Free space is \%\@COMMA[\%\@DISKFREE[$destinationDriveLetter:]]\n";
print "        echo ..... File we were going to copy was: \%LASTFILE\%\n";
print "        echo ..... but its size is \%\@COMMA[\%\@FILESIZE[\"\%LASTFILE\%\"]] ... which doesn't fit in \%\@COMMA[\%\@DISKFREE[$destinationDriveLetter:]]\n";
print "    goto :END\n";
print "\n";
print "    :NotReady\n";
print "        echo.\n";
print "        echo.\n";
print "        echo ..... Annnnnd drive $destinationDriveLetter is no longer ready! WTF! (ERRORLEVEL=\%ERRORLEVEL\%)\n";
print "        echo ..... File we were going to copy was: \%LASTFILE\%\n";
print "        call alarm-beep\n";
print "        echo * Giving a moment to let the drive “spin” back up...\n";
print "        call pause-for-x-seconds 60\n";
print "    return\n";
print "\n";
print ":END\n";
print "call nocar >nul\n";					#weird voodoo to deal with files that have a caret (“^”) in them







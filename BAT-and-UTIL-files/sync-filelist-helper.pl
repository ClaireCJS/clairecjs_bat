use List::Util qw(shuffle);




#This  is a generalized 2nd edition that is deprecated because I've re-written it, but will never go away becuase it's still plugged into some scripts and is not broken.
#There is a specialized 1st edition, which ironically has a more specific filename:    sync-mp3-playlists-to-location-helper.pl

#!perl
my $DEBUG=1;
my $ALLOW_COPY_TO_SAME_DRIVE=1;		#2022/03/17 - changed this because not doing car syncs a lot lately and needed to copy stuff for Beth


################## MAJOR IDEA: Do all the folder making first, then copy the files IN RANDOM ORDER. That way, if we are trying to copy more than will fit, rather than over-representing the stuff at the beginning of the alphabet, we just get some of it


#USAGE: sync-filelist-helper.pl FILELIST.txt D:\DESTINATION\FOLDER\
#		^^^^ Generates script to copy all files from the filelist into the destination folder/directory. Includes creating folders/directories when necessary.

my $BACKSLASHES=1;						#set to 1 if you want all filename slashes to become backslashes
my $MKDIR = "mkdir /s /Nt";				#set to "md" if you must - but you're gonna need to add the option that let's this make multiple folders inside each other at once, i.e. creating "c:\one\two\three\four" in one command, not four.  The /Nt is a TCMD-specific speedup.
my $COPY  = "*copy /u /g /h /j /k /Nst";#set to "cp" if you must - but for me, /u makes it an update copy, which only copies if the file is newer. Significantly saves time. /g=percentage progress. /h=copy hidden, /j=restartable, /Ns=no summary ("1 file copied" suppressed), no updating JPSTREE.IDX
my $SLASH = "\\";						#set to  "/" if you must [Unix folk]

##### GET COMMAND-LINE ARGUMENTS:
my $filelist               =  $ARGV[0];
my $destination            =  $ARGV[1];
my $destinationDriveLetter =  $destination;
   $destinationDriveLetter =~ s/^(.).*$/$1/;		#just the letter, no colon afterward

##### GET ENVIRONMENT ARGUMENTS:
my $FLAC=1;
if ($ENV{"FLAC"} eq "0") { $FLAC=0; }

##### GET FILESYSTEM ARGUMENTS:
my $COLLAPSE=0; 
if (-e "$destinationDriveLetter:\__ mp3 sync option - collapse __") { $COLLAPSE=1; }

##### VALIDATE COMMAND-LINE ARGUMENTS:
if (!-e $filelist)    { die("FATAL ERROR: $filelist"    . "doesn't exist!\nBe careful! Some devices are case-sensitive!\n\n"); }
if (!-d $destination) { die("FATAL ERROR: $destination" . "doesn't exist!\nBe careful! Some devices are case-sensitive!\n\n"); }

##### DETERMINE FOLDER DIVIDER CHARACTER:
my $DIVIDER     = "/";
if ($BACKSLASHES) { $DIVIDER="\\"; } 

##### READ IN FILELIST:
open      (FILELIST,"$filelist") || die("FATAL ERROR: could not open $filelist\n\n");
my @FILES=<FILELIST>;
close     (FILELIST);

##### TRAVERSE FILELIST:
use strict;
my $folder="";
my $newFolder="";
my $newfile="";
my $fileonly="";
my $driveLetterBefore="";
my $driveLetterAfter="";
my $COMMANDSET="";
my %FOLDERS_CREATED=();
my @QUEUEDCOMMANDS =();
print "\@Echo OFF\n";
print "call car\n";
print ":REM: destinationDrive is \"$destinationDriveLetter\"\n";
print "\n\%COLOR_IMPORTANT\% \%+ echo * Making directories... \%+ \%COLOR_NORMAL\% \n\n";
my $file;
my $filenum=0;
foreach $file (@FILES) {
	next if $file =~ /^#EXT/;
	chomp $file;
	$filenum++;
	print ":************ processing file $filenum $file ***************** \n ";

	if ($BACKSLASHES) { $file =~ s/\//\\/g; }			# Convert filename to backslashes, if necessary

	##### Separate source folder and source filename:
	$folder   = $file;
	$fileonly = $file;
	$folder   =~ s/^(.*[\\\/])([^\\\/]*$)/$1/i;
	$fileonly =~ s/^(.*[\\\/])([^\\\/]*$)/$2/i;
	$file =~ s/^([\\\/])/C:$1/;									    #add C: to beginning of entries with no drive letter - THIS COULD BE VERY PROBLEMATIC IN THE LONG RUN. MIGHT WANT TO MAKE THIS ENV-VAR CONTROLLABLE LATER, IF THAT BECOMES A PROBLEM.

	##### Transform source folder into destination folder:			#UPDATES TO CODE GENERALLY WILL BE IN THIS SECTION
		##### WARNING! CLIOVIRONMENT REQUIRES ANY UPDATES TO BELOW TO ALSO BE MADE TO SYNC-MP3-PLAYLISTS-TO-LOCATION-HELPER.PL, which is the generalized/2nd version of this
		##### WARNING! CLIOVIRONMENT REQUIRES ANY UPDATES TO BELOW TO ALSO BE MADE TO SYNC-MP3-PLAYLISTS-TO-LOCATION-HELPER.PL, which is the generalized/2nd version of this
		##### WARNING! CLIOVIRONMENT REQUIRES ANY UPDATES TO BELOW TO ALSO BE MADE TO SYNC-MP3-PLAYLISTS-TO-LOCATION-HELPER.PL, which is the generalized/2nd version of this
		##### WARNING! CLIOVIRONMENT REQUIRES ANY UPDATES TO BELOW TO ALSO BE MADE TO SYNC-MP3-PLAYLISTS-TO-LOCATION-HELPER.PL, which is the generalized/2nd version of this
		##### WARNING! CLIOVIRONMENT REQUIRES ANY UPDATES TO BELOW TO ALSO BE MADE TO SYNC-MP3-PLAYLISTS-TO-LOCATION-HELPER.PL, which is the generalized/2nd version of this
		##### WARNING! CLIOVIRONMENT REQUIRES ANY UPDATES TO BELOW TO ALSO BE MADE TO SYNC-MP3-PLAYLISTS-TO-LOCATION-HELPER.PL, which is the generalized/2nd version of this
		##### WARNING! CLIOVIRONMENT REQUIRES ANY UPDATES TO BELOW TO ALSO BE MADE TO SYNC-MP3-PLAYLISTS-TO-LOCATION-HELPER.PL, which is the generalized/2nd version of this
		##### WARNING! CLIOVIRONMENT REQUIRES ANY UPDATES TO BELOW TO ALSO BE MADE TO SYNC-MP3-PLAYLISTS-TO-LOCATION-HELPER.PL, which is the generalized/2nd version of this
	$newFolder =  $folder;

	$newFolder =~ s/CAROLYN-PROCESS[^\\\/]*//;

	$newFolder =~ s/[A-Z]?:?[\\\/]testing([\\\/])1 - ONEDIR JUDGE WITH CAROLYN/$destination$1MISC/gi;		#special case, not the best line to copy-paste for other transformations
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

	$newFolder =~ s/[A-Z]?:?[\\\/]mp3/$destination/gi;		#20140819 moved to end

	$newFolder =~ s/[\\\/][\\\/]/$SLASH/g;					#fix extra slash deposits made by anything above

	##### Because we don't branch for each of the above substitutions, sometimes we end up with the target folder prefixing twice:
	#my $destinationregex = quotemeta($destination);
	#$newFolder =~ s/$destination$destination/$destination/;
	#$newFolder =~ s/$destination$destination/$destination/;		#technically, this should all be a while(), 
	#$newFolder =~ s/$destination$destination/$destination/;		#but who wants to deal with stopping infinite loops?
	#$newFolder =~ s/$destination$destination/$destination/;
	$newFolder =~ s/^(.*)([A-Z]:.*$)/$2/;		
	$newFolder =~ s/\\mp3music\\/\\mp3\\/ig;
	
	#DEBUG:	
	print ":REM     ## newFolder for $folder is $newFolder\n";

	##### Sanity check for missing folder substitution patterns:
	$driveLetterBefore =    $folder; $driveLetterBefore =~ s/^(.).*$/$1/;
	$driveLetterAfter  = $newFolder; $driveLetterAfter  =~ s/^(.).*$/$1/;
	if (!$ALLOW_COPY_TO_SAME_DRIVE) {
		if (uc($driveLetterBefore) eq uc($driveLetterAfter)) { print "echo ERROR=copying to same drive makes no sense for $folder to $newFolder!\n\ncall alarmbeep\n\npause\n\n"; }
	}
	#TO FIX: \MP3-TE~1\0-BATC~1\MLP\ to \MP3-TE~1\0-BATC~1\MLP\

	##### Create target filename:
	if ($COLLAPSE==0) { $newfile =               "$newFolder$DIVIDER$fileonly"; }
	if ($COLLAPSE==1) { $newfile = "$destinationDriveLetter:$DIVIDER$fileonly"; }
	$newfile =~ s/\\\\/\\/g;	#erase consecutive dupe folder dividers
	$newfile =~ s/\/\//\//g;	#erase consecutive dupe folder dividers

	##### INITIALIZE OUR STORED COMMANDS:
	$COMMANDSET = "\n\n\n\n";

	##### Create destination folder, only if necessary:
	#if ($FOLDERS_CREATED{$newFolder}=="1") {
	#	#do nothing; it's already created
	#} else {
	#	$COMMANDSET .= "if     isdir \"$newFolder\" echo * Exists: $newFolder  \n";		#UNIX people may need to change this!
	#	$COMMANDSET .= "if not isdir \"$newFolder\" echo * Making: $newFolder  \n";		#UNIX people may need to change this!
		$COMMANDSET .= "if not isdir \"$newFolder\"      ($MKDIR \"$newFolder\")\n";		#UNIX people may need to change this!
	#	$FOLDERS_CREATED{$newFolder}="1";
	#}

	##### Copy the file:
	#$file =~ s/c:[\\\/]media/O:\media/i;							#201107 new hades remap kludge
	#Make filenames safe for command-line:
	   $file =~ s/\%/%%/g;
	$newfile =~ s/\%/%%/g;
	$COMMANDSET .= "echo.\n";
	$COMMANDSET .= "SET LASTFILE=$file\n";
	$COMMANDSET .= "if \%\@DISKFREE[$destinationDriveLetter:] lt \%\@FILESIZE[\"$file\"] goto :Full\n";

	if (1) {
		$COMMANDSET .= "call display-free-space-as-locked-message\n";
	} else {
		$COMMANDSET .= "color bright yellow on black\n";
		$COMMANDSET .= "echo * Free Space: \%\@COMMA[\%\@DISKFREE[$destinationDriveLetter:]]\n";
		$COMMANDSET .= "color green on black\n";
	}

	$COMMANDSET .= "if \"\%\@READY[$destinationDriveLetter:]\" eq \"0\" gosub :NotReady\n";

	#TRIED, BUT WAS STUPID, BECAUSE PLAYLISTS SYNC *FIRST* IN OUR SYSTEM: I want to leave 20M free for playlists, so threshold at 25M: 	#$COMMANDSET .= "if \%\@DISKFREE[$destinationDriveLetter:] lt 26214400 goto :Full\n";

	#COMMANDSET .= "if not exist \"$file\" (echo. \%+ echo * WARNING: File does not exist [but maybe you moved it]: $file)\n";
	$COMMANDSET .= "if not exist \"$file\" (echo. \%+ echo * WARNING: File does not exist [but maybe you moved it]: \"$file\")\n";


	if (($FLAC==0) && ($file =~ /\.flac$/i)) {
		$COMMANDSET .= "\%COLOR_WARNING\% \%+ echo NOT copying FLAC file: \"$file\" \%+ \%COLOR_NORMAL\% \n";
	} else {
		$COMMANDSET .= "$COPY \"$file\" \"$newfile\"\n";
	}


#	$COMMANDSET .= "if \%ERRORLEVEL\%==2 goto :Full\n";				#this gave false-positives due to out-of-sync filelists. Thus we moved on to using %@DISKFREE (above)


	push(@QUEUEDCOMMANDS,$COMMANDSET);

	#DEBUG: print "file=$file\nfolderOLD=$folder\nfolderNEW=$newFolder\nfileonly=$fileonly\nnewfile=$newfile\n\n";
}


##### Randomize the copies, so that if we run out of space, we get a random sampling of everything we attempted to copy
print "\nREM (randomizing array: begin)\n";
# Randomly sort the array
#y @QUEUEDCOMMANDSRANDOM = &randarray(@QUEUEDCOMMANDS);		#rem this was horribly inefficient
my @QUEUEDCOMMANDSRANDOM =  shuffle  (@QUEUEDCOMMANDS);		#2023 ChatGPT suggestion

print "\nREM (randomizing array: end)\n";
foreach my $command (@QUEUEDCOMMANDSRANDOM) { print $command; print "\%COLOR_LESS_IMPORTANT\% \%+ echo * Files remaining: \%\@COMMA[" . $filenum-- . "] \%+ \%COLOR_NORMAL\% \n\n"; }


print "\n\n";
print "goto :END\n";
print "\n";
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
print "    return\n";
print "\n";
print ":END\n";
print "call nocar\n";

















###########################################################################################################################
sub randarray {
        my @array = @_;
        my @rand = undef;
        my $seed = $#array + 1;
        my $randnum = int(rand($seed));
        $rand[$randnum] = shift(@array);
		my $i=0;
        while (1) {
                my $randnum = int(rand($seed));
                if ($rand[$randnum] eq undef) {
                        $rand[$randnum] = shift(@array);
                }
				if (($i++ % 100) == 1) { print "REM (thinking) (i=$i)"; }
                last if ($#array == -1);
        }
        return @rand;
}
###########################################################################################################################

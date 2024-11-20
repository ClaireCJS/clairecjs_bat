#!perl
#delete this line when you forget what it means - ### 8_Wandering Heart.mp3 ==> learned ==> on 2022-02-07 at 08:55:58
use utf8;
binmode(STDIN,  ':encoding(UTF-8)');
binmode(STDOUT, ':encoding(UTF-8)');


########## WHAT THIS DOES:
##########	1) Opens up the last.fm log (which can be hardcoded) and determines the song playing.
##########	2) Determines the folder the song is playing in
##########	3) Opens up (using editor defined in %EDITOR environment variable) a file (defined in $ATTRIB_LST below) in the same folder as the mp3 playing
##########	4) Copies the track number of the mp3 to the clipboard


###########  GENERAL NOTE: This fails if a song is not tagged, but as of 2011 that could be fixed with some effort.
########### PERSONAL NOTE: A lot of this functionality is dupliated in get-current-song-playing.pl ... Updates here may need to go there as well.




##### DEBUG STATUS / INFORM THE USER:
my $DEBUG_BAT                        = 0;			#set to   1     for pauses in the actual batfile which is generated, 0 else
my $DEBUG                            = 0;			#set to 0,1,2,3 for more verbose output, like every line found in audioscrobbler log
my $DEBUG_FIND_IN_AUDIOSCROBBLER_LOG = 0;			#set to 0,1,2   for more verbose output
my $DEBUG_CLIPBOARD_TEXT             = 0;           #set to   1     for more debug info about what gets copied to the clipboard

#print "rem :debug     is $DEBUG    \nrem :debug_bat is $DEBUG_BAT\n";


##### CONSTANT:
my $ATTRIB_LST = "attrib.lst";


##### NEAR-CONSTANT:
my $METHOD   = "2024";		#Last.fm likes to change their logfile format. Remember, this method affects code below too, so search for $METHOD to update those pieces of code as well
if ($METHOD eq "2008") { $MUSIC_LOG_SEARCH_FOR = "CScrobbler::OnTrackPlay"                        ; }
if ($METHOD eq "2009") { $MUSIC_LOG_SEARCH_FOR = ": Sent Start for "                              ; }
if ($METHOD eq "2011") { $MUSIC_LOG_SEARCH_FOR = "Failed to extract MBID for"                     ; $MUSIC_LOG_SEARCH_FOR2 = "Starting query FP for"; $MUSIC_LOG_SEARCH_FOR3 = "DISABELEDEvent::TrackChanged"; }	
if ($METHOD eq "2012") { $MUSIC_LOG_SEARCH_FOR = "Line received: START c=.*&a=.*&t=.*"            ; }	
if ($METHOD eq "2013") { $MUSIC_LOG_SEARCH_FOR = "PlayerCommandParser::PlayerCommandParser.*START"; }	
if ($METHOD eq "2024") { $MUSIC_LOG_SEARCH_FOR = "";                                                }	#2024 method does not involve searching through a logfile because we're moving from using Last.FM's log as we have for 16 years, to moving the now-playing.txt file NOW_PLAYING_TXT created by WinAmp's now-playing plugin




##### DRIVE-LETTER REMAPPING STUFF:
my $MACHINE_NAME       =               $ENV{"MACHINENAME"};
my $REMAPENVVAR        =              "REMAP$MACHINE_NAME";
my $REMAP              =         $ENV{$REMAPENVVAR};
my @REMAPS             = split(/\s+/,"$REMAP");
#print "echo name=$MACHINE_NAME, \$REMAPENVVAR=$REMAPENVVAR         REMAP=$REMAP\n\n";

##### SET MODE:
my $MODE_NORMAL   = "NORMAL"     ;
my $MODE_AUTOMARK = "AUTOMARK"   ; 
my $DEFAULT_MODE  = $MODE_NORMAL ;
my $MODE          = $DEFAULT_MODE;
my $AUTOMARK_AS   = ""           ;
if ($ENV{"AUTOMARK"} ne "") { 
	$MODE         = $MODE_AUTOMARK; 
	$AUTOMARK_AS  = $ENV{"AUTOMARKAS"};
	if ($AUTOMARK_AS eq "") {
		my $msg = "FATAL ERROR! Cannot automark without knowing what to mark it as. Environment variable AUTOMARKAS must be set to something!";
		print     "echo $msg\n beep\n pause\n pause\n";
		die($msg);
	}
}
#DEBUG: die "mode is $MODE";


##### COMMAND-LINE ARGUMENTS:
my $MUSIC_LOG      = $ARGV[0];
my $ALL_SONGS_LIST = $ARGV[1];
my $REGEX          = $ARGV[2];						#we can also pass it a regex, to edit the status of songs that AREN'T currently playing
my $COMMENT        = $ENV{"LEARNED_COMMENT"};		#20240702 —— changed this from 'comment' to 'learned_comment' to avoid scope collisions
if ("" eq $MUSIC_LOG) { print "echo * FATAL ERROR 1: First argument must specify filename of MUSIC LOG!!\n"; exit(); }
if ( !-e  $MUSIC_LOG) { print "echo * FATAL ERROR 2: music log OF \"$MUSIC_LOG\" DOES NOT EXIST!!\n"       ; exit(); }
if (($METHOD eq "2008") || ($METHOD eq "2009")) {
	if ("" eq $ALL_SONGS_LIST) { print "FATAL ERROR 3: Second argument must specify filename of ALL SONGS LIST!!\n"; exit(); }
	if ( !-e  $ALL_SONGS_LIST) { print "FATAL ERROR 4: $ALL_SONGS_LIST DOES NOT EXIST!!\n"                         ; exit(); }
}


##### BEGIN:




if ($METHOD eq "2024") {
	#print ("Method 2024 oooh, log is $MUSIC_LOG\n");
	use strict;
	use warnings;
	use Data::Dumper;

	# Open the file and read its contents
	open(my $fh, '<:encoding(UTF-8)', $MUSIC_LOG) or die "Cannot open file '$MUSIC_LOG': $!";
	my @lines = <$fh>;
	close($fh);
	chomp @lines;  # Remove newline characters from each line
	
	# Extract the first two special variables
	my $display_title = shift @lines;
	my $filename = shift @lines;

	# Initialize the hash table
	my %metadata;
	my $i = 0;
	while ($i < @lines) {
		my $line = $lines[$i];

		if ($line =~ /^(\w+)=([\s\S]*)$/) {
			my $field = $1;
			my $value = $2;

			# Check if the next line is end_<field>=1
			if ($i + 1 < @lines && $lines[$i + 1] =~ /^end_${field}=1$/) {
				# Handle multi-line field
				$metadata{$field} = $value;
				$i += 2;  # Skip the end_<field>=1 line
			} else {
				# Handle single-line field
				$metadata{$field} = $value;
				$i += 1;
			}
		} else {
			$i += 1;  # Skip any lines that don't match the pattern
		}
	}

	# Print the first two special variables
	print "✨Display Title: $display_title\n";
	print "✴Filename: $filename\n";

	# Print the entire hash table for debugging
	print "♐Metadata Hash Table:\n";
	print Dumper(\%metadata);
	
}






my $song_regex="";
my $line="";
my $song_found="";
my $found=0;
my $found_regex;
my $line="";
my $last_found="";
my $FOUND_IN_AUDIOSCROBBLER_LOG=0;
my $song = "";
my $FOUND_FULL_PATH="";
my $possible_song_found = "";
my $possible_folder = "";
my @TARGET_FILES=();
my $text_to_copy_to_clipboard__usually_tracknum="";
my $REGEX_GIVEN_AT_COMMAND_LINE=0;
my $path2use="";
if ($REGEX eq "") {
	##### OPEN AUDIOSCROBBLER LOGFILE TO GET LATEST TRACK PLAYED:
	open(LOG,"$MUSIC_LOG") || die("FATAL ERROR 5: COULD NOT OPEN $MUSIC_LOG, despite it existing!");
	if ($DEBUG>2)   { print ":searchfor is $MUSIC_LOG_SEARCH_FOR \n"; }
	while ($line=<LOG>) {
		if ($DEBUG_FIND_IN_AUDIOSCROBBLER_LOG>1) { print ":as.log line is $line\n"; }
		if (
			($line =~ /($MUSIC_LOG_SEARCH_FOR)/) 
			|| 
			(($METHOD eq "2011") && (($line =~ /($MUSIC_LOG_SEARCH_FOR2)/) || ($line =~ /($MUSIC_LOG_SEARCH_FOR3)/)))
		) {
			if ($DEBUG>2)   { print ":found searchfor in line: $line"; }
			$FOUND_IN_AUDIOSCROBBLER_LOG=1;
			$last_found = $line;
		}
	}
	close(LOG);
	chomp $last_found;
	if ($DEBUG_FIND_IN_AUDIOSCROBBLER_LOG) { print ":\$FOUND_IN_AUDIOSCROBBLER_LOG = $FOUND_IN_AUDIOSCROBBLER_LOG\n"; }
	if ($DEBUG)                            { 
		if ($FOUND_IN_AUDIOSCROBBLER_LOG)  { print ":last_found found line is: \"$last_found\"\n"; }
		else                               { print ":searchfor of $MUSIC_LOG_SEARCH_FOR was never found!\n"; }
	}

	
	##### TAKE LINE CONTAINING LAST TRACK PLAYED, FIX IT UP:
	if      ($METHOD eq "2008") {
		$last_found =~ /New song detected - (.*)$/;
		$song=$1;
	} elsif ($METHOD eq "2009") {
		$last_found =~ /Sent Start for (.*)$/i;
		$song=$1;
	} elsif (($METHOD eq "2011") || ($METHOD eq "2011")) {			#this ws 2011 or 2012; temporarily forking 2012 to its own section but leaving this wonky like this as a reminder in case I revert and change my mind years down the line
		$last_found =~ /Sent Start for (.*)$/i;
		if ($1 ne "") { $song=$1; }

		$last_found =~ /Failed to extract MBID for: (.*)$/i;
		if ($1 ne "") { $song=$1; }

		$last_found =~ /Starting query FP for: *\"(.*)\"/i;
		if ($1 ne "") { $song=$1; }

		$last_found =~ /Starting new track \'() \? ()\'/i;
		if ($1 ne "") { $song="$1 - $2"; }
	} else {	#if ($METHOD eq "2012", 2013) {
		$last_found =~ /START c=.*&a=.*&t=.*p=(.*)$/i;
		if ($1 ne "") { 
			$FOUND_FULL_PATH=$1; 
			$path2use = $FOUND_FULL_PATH;
			$path2use =~ s/\//\\/g;
			push (@TARGET_FILES,"$path2use");
		}
		if ($DEBUG) { print ":******* FOUND FULL PATH: $FOUND_FULL_PATH (\$1=$1)\n"; }
	}

	if ($DEBUG) { print "\n:song is [1] $song!\n:FOUND_FULL_PATH=$FOUND_FULL_PATH\n"; }


	if (($METHOD eq "2008") || ($METHOD eq "2009")) {
		##### Because I remove move things in parenthesis, anything that this is a mistake for must be preserved for later. This is a feature added in 2009:
		##### we keep things in parenthesis if they are "live", "demo", "x mix", "x remix", "mix by x", "x version"
		$parenthetical_title_to_save="";
		if (($song =~ /(\([^\)]*Mix\))/i) || ($song =~ /(\([^\)]*Version\))/i) || ($song =~ /(\([^\)]*Mix by [^\)]+\))/i)				## THIS WHOLE
			#testing 20090921:																											## BLOCK   IS 
			|| ($song =~ /(\(live\))/i)																									##  OBSOLETE
			|| ($song =~ /(\(demo\))/i))																								## AS OF 2011
			{																															## THANKS TO
			$parenthetical_title_to_save = $1;																							##  LAST.FM
			#$parenthetical_title_to_save =~ s/\(/\\\(/;	#unnecessary, becuase this is done later									##  REMOVING
			#$parenthetical_title_to_save =~ s/\)/\\\)/;	#unnecessary, becuase this is done later									##  LOGFILE
			if ($DEBUG) { print ":$parenthetical_title_to_save is [AA] $parenthetical_title_to_save!\n"; }								## AMBIGUITY
		}


		######from remove-last-parenthetical-clause.pl
		#TODO: BREAKS HERE!: FIX IT:
		#:song is Dr. Dirty (John Valby) - Greensleeves (Herniated Jingle Balls)!
		#:song is now "Dr. Dirty"!
		#^todo GET THAT BUG
		#I see the problem here. If there are mlutiple parenthesis, I want to remove the last, but have only coded for multiple NESTED parenthesis.
		#When there are two parenthesis that are NOT nested, I should remove 1 or the other, but ****NOT**** everything in between ****BOTH****
		#^^^ so... Is this still a todo, or did I leave that in here as information for myself?

		if    ($song =~ /\)\)$/)          { $song =~ s/\([^\(\)]*\([^\(\)]*\)\)$//; }		#nested parnethesis
		elsif ($song =~ /\(.*\).*\(.*\)/) { $song =~ s/(\(.*\).*)(\(.*\))/$1/; }			#may catch 3-parentehsis songs - MAY HAVE TO UPDATE IN THE FUTURE
		else                              { $song =~ s/\(.*\)//; }							#if only one parenthesis take it out - MAY HAVE TO UPDATE TO ONLY DO THIS IF IT'S AT THE *END* OF THE LINE

		#$song =~ s/\([\(\).]*\)//;
		$song =~ s/\s+$//;
		$song =~ s/^\s+//;
		if ($DEBUG) { print "\n:song is now [2] \"$song\"!\n"; }

		
		##### If there was parenthtical stuff we saved from before (remixes, for example), they were stripped, so now we add it back on:
		$song .= " $parenthetical_title_to_save";



		##### CONVERT SONG INTO A REGULAR EXPRESSION FOR 'GREPPING':
		$song_regex = $song;
	}
} else {
	$song_regex = $REGEX;
	$REGEX_GIVEN_AT_COMMAND_LINE=1;
}

if ($DEBUG>0) { print ":Song regex is now[A5]: $song_regex (RGACL=$REGEX_GIVEN_AT_COMMAND_LINE)\n"; }


if (($METHOD eq "2008") || ($METHOD eq "2009")) {				# || ($REGEX_GIVEN_AT_COMMAND_LINE ==1) meh
	if ($DEBUG>0) { print ": intial song_regex is \"$song_regex\" \n"; }
	if ($song_regex eq "- ") { print "\n\n\n:ERROR! No info in regex! Is the song not tagged??\n"; die("regex of \"$song_regex\" is not substantive... Is the song untagged?"); }

	#FROM convert-id3-to-filenameregex
	#### The magic happens here:
	#worked: $song_regex =~ s/ - /.*/g;
	#200912: 
	$song_regex =~ s/(.*) - (.*)/$1.*$2/g;
	$left=$1; $right=$2;
	print ": Right=$right,left=$left\n";
	$song_regex =~ s/\+/\\+/g;					#turn + to \+ for regexification
	$song_regex =~ s/\s*--\s*/.*/g;
	$song_regex =~ s/\?/.*/g;	#they are usually _ in a filename, but if i put it ina  tag and not a filename, searching would make it fail, so let's not search for an _, let's just search for nothing if ther eis a ?
	$song_regex =~ s/\s*\/\s*/.*/g;

	#### The kludges happen here:
	$song_regex =~ s/^[\-\s]+//;			#the cut point in the audioscrobbler logfile isn't always the smae ... sometimes we get a "- " at the beginning .. so we need to remove that  or the grep we do with that in the future will fail

	#### Also, for example, "The Bangles" really is "Bangles, The". We should just remove "The".
	$song_regex =~ s/^The //i;

	#### Other good ideas to do while we're here:
	$song_regex =~ s/^\s*//;			#also remove leading  spaces...seems like a harmless side-effect
	$song_regex =~ s/\s*$//;			#also remove trailing spaces...seems like a harmless side-effect
	#$song_regex =~ s/\'/\\'/g;
	#parentehsis need to be real parens now; spaces into .
	$song_regex =~ s/\(/\\(/g;
	$song_regex =~ s/\)/\\)/g;
	$song_regex =~ s/ /.*/g;		#was just . but broke on "Sabbat - A Cautionary Tale  (demo)" due to extra space before demo that's not supposed to be there
	
	##### INFORM REGEX FOR DEBUG:
	print "echo regex [A] was $song_regex\necho.\necho.\n";													#OBSOLETE: if ($DEBUG) { print "\n:song_regex is now \"$song_regex\"!\n\n"; }
}

if ($DEBUG>0) { print ":Song regex is now[B5]: $song_regex (RGACL=$REGEX_GIVEN_AT_COMMAND_LINE)\n"; }


##### THE OLD METHOD: LOOK THROUGH OUR SONGS LIST TO FIND THE SONG.  The 2011 last.fm improved logfile format makes this totally unnecessary. UNLESS we're not using that!
if (($METHOD eq "2008") || ($METHOD eq "2009") ||  ($REGEX_GIVEN_AT_COMMAND_LINE ==1)) {
	open(PLAYLIST,"$ALL_SONGS_LIST") || die("FATAL ERROR 6: COULD NOT OPEN $ALL_SONGS_LIST, despite it existing!");
	while ($line=<PLAYLIST>) {
		chomp $line; if ($line =~ /$song_regex/i) { $song_found .= "$line\n"; $found++;	$found_regex=$song_regex;	if ($DEBUG>1) { print ":found song $line\n"; } }
	}
	close(PLAYLIST);
	my $method=1;
	my $SIX=0;						

	my $num_methods=9;				###### INCREASE AS NEW METHODS ARE ADDED!!!
	while (($found==0) && ($method <= $num_methods)) {
		my $try_regex;
		$try_regex = $song_regex;

		if    ( $method == 1) {	$try_regex =~ s/^(.*)(\.\*)(.*)$/$3$2$1/i; }
		elsif ( $method == 2) {	$try_regex =~ s/^(.*)(\.\*)(.*)(\.\*)(.*)$/$1$2$5/i; }
		elsif ( $method == 3) {	$try_regex =~ s/^(.*)\.\*(.*)\.\*(.*)$/$2.*$3.*$1/i; }
		elsif ( $method == 4) {	$try_regex =~ s/^(.*)(\.\*)with.*(\.\*)(.*)(\.\*)(.*)$/$1$2$3$4$5$6/i; }			#if it's "blah blah with blah blah - blah blah blah" we end up with "blah blah - blah blah" - everything after with, but before the last 2 words is taken out
		elsif ( $method == 5) {	$try_regex =~ s/^(.*)(\.\*)with.*(\.\*)(.*)$/$1$2$3$4/i; }							#like 3, but with just the last word instead of the last two words
		elsif ( $method == 7) {	$try_regex = $right . ".*" . $left; }												#comes in play with tribute albums that are song - band
		elsif ( $method == 8) {	$try_regex = $right; }
		elsif ( $method == 9) {	$try_regex = $left; }			
		elsif (($method == 6) && (!$SIX)) {	$try_regex =~ s/feat\.\*[a-z]*//i; $method=1; $SIX=1; }										#remove "feat. bandname" and start over
		#BLANKS (remember to increase $num_methods above!!!!!!!!!!): 
		#elsif ($method == 4) {	$try_regex =~ s/^///i; }
		#elsif ($method == 5) {	$try_regex =~ s/^///i; }

		##### INFORM THE USER/DEBUG:
		print "\necho regex [B$method] was $try_regex\necho.\necho.\n";  #[B1][B2][B3][B4][B5][B6][B7][B8][B9]

		##### COPIED FROM ABOVE; LAZY TONITE:
		open(PLAYLIST,"$ALL_SONGS_LIST") || die("FATAL ERROR 7: COULD NOT OPEN $ALL_SONGS_LIST, despite it existing!");
		while ($line=<PLAYLIST>) {
			chomp $line; 
			if ($line =~ /$try_regex/i) { 
				$song_found .= "$line\n"; 
				$found++;	
				$found_regex=$try_regex;	
				if ($DEBUG) { print ":found song $line!\n"; } 
			}
		}
		close(PLAYLIST);
		$method++;
	}
	chomp $song_found;
	$song_found =~ s/\//\\/g;


	##### THE SONG MAY HAVE MULTIPLE RESULTS, SO GO THROUGH THEM:
	my @songs_found = split(/\n/,"$song_found");
	foreach $possible_song_found (@songs_found) {
		if ($DEBUG>1) { print ":possible_song_found is now \"$possible_song_found\"!\n\n"; }
		$possible_song_found =~ /^(.*)[\\\/]([^\\\/]*)$/;
		$possible_folder = $1;

		$text_to_copy_to_clipboard__usually_tracknum = $possible_song_found;
		$text_to_copy_to_clipboard__usually_tracknum =~ s/^.*[\\\/]//i;
		$text_to_copy_to_clipboard__usually_tracknum =~ s/\....$//i;
		$text_to_copy_to_clipboard__usually_tracknum =~ s/^([0-9]*_*[0-9]*[0-9]_).*$/$1/;		#THE MEAT - HERE'S WHERE WE GET THE # IN BEST CASE SCENARIOS
		$text_to_copy_to_clipboard__usually_tracknum =~ s/^([0-9]*_*[0-9]*[0-9] - ).*$/$1/;		#meat #2 - sometimes it's like this for pre-processed stuff that we haven't named our way, e.g. "01 - First Track" instead of "01_First Track" 
		$text_to_copy_to_clipboard__usually_tracknum =~ s/_$//;							#after a long time, decided trailing underscore is annoying
		$text_to_copy_to_clipboard__usually_tracknum =~ s/^0//;							#after a long time, decided  leading    zero    is annoying

		if ($DEBUG>1) { print ":possible_folder is now \"$possible_folder\"!\n"; }
		if (-e "$possible_folder\\$ATTRIB_LST") {
			if ($DEBUG>1) { print ":possible attrib list found at $possible_folder\\$ATTRIB_LST\"!\n"; }
			push (@TARGET_FILES,"$possible_folder\\$ATTRIB_LST");
		} else {
			if ($DEBUG>1) { print ":possible attrib list NOT found at $possible_folder\\$ATTRIB_LST\"!\n"; }
			#20070922:	adding this line, because we need this to work for 
			#			folders that don't have an $ATTRIB_LST as well!
			push (@TARGET_FILES,"$possible_folder\\$ATTRIB_LST");
		}
	}




##### THE NEW 2011 METHOD IS WAY EASIER THAN ALL OF THE ABOVE!
} elsif (($METHOD eq "2011") || ($METHOD eq "2012") || ($METHOD eq "2013")) {

	if ($DEBUG>0) { print "REM :DEBUG: pushing onto \@TARGET_FILES: \"$song\"\n"; }
	push(@TARGET_FILES,$song);			#SEE HOW EASY THAT WAS?

}



if ($DEBUG>0) { print ":Song regix is now[C5]: $song_regex (RGACL=$REGEX_GIVEN_AT_COMMAND_LINE)\n"; }


#### Will use this later:
$MP3DRIVE = $ENV{MP3DRIVE};


##### NOW WE HAVE OUR RESULTS:
my $target_dir="";
my $filename_nodir="";
my %folder_dealt_with={};
my $actual_tracknum="";
foreach my $target_file (@TARGET_FILES) {
	##### FILE / DIRECTORY:
	if ($DEBUG>0) { print "\n:target_file [orignal] is $target_file\npause\n\n"; }
	if (!-e $target_file) {	$target_file = &remap($target_file);}
	if ($DEBUG>0) { print "\n:target_file [remappd] is $target_file\npause\n\n"; }
	if (($METHOD eq "2008") || ($METHOD eq "2009")) {
		$target_file = &go_up_one_level_where_appropriate($target_file);
	}
	$filename_nodir = $target_file;
	$target_dir =  $target_file;
	$target_dir =~ s!^[^C]:\\mp3!C:\\mp3!ig;
	$target_dir =~ s/^(.*[\\\/])[^\\\/]*$/$1/i;
	$target_dir =~ s/\&\&/&/g;
	if (($ENV{EC_DO_NOT_GO_UP_1_DIR} != 1) && ($ENV{MAKING_KARAOKE} != 1)) {
		$target_dir =  &go_up_one_level_where_appropriate($target_dir);
	}
	if (($METHOD eq "2011") || ($METHOD eq "2012") || ($METHOD eq "2013")) {
		$target_file = $target_dir . $ATTRIB_LST;
	}

	if ($DEBUG>0) { print "\n:target_dir  [1] is $target_dir \npause\n"  ; }
	if ($DEBUG>0) { print "\n:target_file [1] is $target_file\npause\n\n"; }

	##### FILENAME:
	$filename_nodir =~ s/"//g;
	$filename_nodir =~ s/^.*[\\\/]//g;
	$filename_nodir =~ s/\&\&/&/g;
	$filename_nodir =~ s/ *$//g;
	$filename_nodir =~ s/^\"//g;
	$filename_nodir =~ s/\"*$//g;
	$filename_nodir =~ s/ $//g;
	next if $filename_nodir eq "";
	if (($DEBUG>0)||(1)) { print "\nREM ##### filename_nodir is \"" . $filename_nodir. "\"\n\n"; }

	##### IMPORTANT: WE ONLY DEAL WITH EACH DIRECTORY *ONCE* AND ONLY ONCE:
	if    ($folder_dealt_with{$target_dir} == 1) { next; }
	else { $folder_dealt_with{$target_dir}  = 1; }

	##### KLUDGE THE TARGET DIR SO IT'S %MP3DRIVE% BECAUSE OF SOME WEIRD USE CASE ON CAROLYN'S COMPUTER THAT WE CAN'T FIGURE OUT.
	##### %MP3DRIVE% WILL ALWAYS BE THE CORRECT DRIVE ANYWAY, IN ANY AND ALL SITUATIONS THAT WOULD EVER APPLY TO USING THIS:
#	print "rem Is this even happening? [0] target_dir=$target_dir\n";
#	if ($MP3DRIVE ne "") {	$target_dir =~ s/^[A-Z]:/$MP3DRIVE:/ig;	}

	##### CHANGE INTO TARGET DIR:
#	print "rem Is this even happening? [1] target_dir=$target_dir\n";
	print "\"$target_dir\"\n";		#ex: C:\mp3\TV & MOVIES & GAMES\CARTOONS\2000s\Moral Orel\Mark Rivers & Friends - The Music Of Moral Orel (2008)\

	##### TITLE THE WINDOW:
	$title = $target_dir;
	$title =~ s/^.*\\(.*)\\.*\\$/$1/i;
	print "title $title\n";


	##### GIVE AN INDICATION THAT THE SONG WE'RE LOOKING FOR IS HERE:
	if (($METHOD eq "2011") || ($METHOD eq "2012") || ($METHOD eq "2013")) {
		if ($filename_nodir ne "") {
			print "dir /s /k /m /b /f \"$filename_nodir\"\n";
		}
	} else {
		print "dir /s /k /m /b /f \| grep -i \"$found_regex\"\n";				#thd old way
	}


	$target_dir =~ s/\\$//;
	print "set CURRENT_SONG_FILE="     . $filename_nodir                      . "\n";
	print "set CURRENT_SONG_DIR="      . $target_dir                          . "\n";
	print "set CURRENT_SONG_FILENAME=" . $target_dir . "\\" . $filename_nodir . "\n";

	print "\n\n:targetdir is $target_dir \n";
	print    ":targetfile is $target_file\n";
	if (($target_dir =~ /(_*unsorted)[\\\/]*$/i) || ($target_dir =~ /(currently.judging)[\\\/]*$/i)) { 
		my $tmp=$1;
		print "cd..\n"; 
		$target_file =~ s/[\\\/]$tmp//i;
	} 


	##### OPEN UP $ATTRIB_LST WITH EDITOR:
	if (($MODE eq $MODE_NORMAL) && ($ENV{EC_OPT_NOEDITOR} ne "1")) {
		print "\%COLOR_IMPORTANT_LESS%\n";
		print "echo \%EDITOR\% \"" . $target_file . "\"\n";
		print "\%COLOR_WARNING%\n";
		print "     \%EDITOR\% \"" . $target_file . "\"\n";
	} else {
		#If it's in $MODE_AUTOMARK, do not open the editor
	}

	##### COPY THE TRACKNUM/NAME INTO THE CLIPBOARD... YES!
	##### BUT NOT THE STUPID NON-SONG-TITLE-STUFF...NO!
#	if ($METHOD eq "2011") {
		$text_to_copy_to_clipboard__usually_tracknum = $filename_nodir;														
		if ($DEBUG_CLIPBOARD_TEXT) {  print "echo [A] it's $text_to_copy_to_clipboard__usually_tracknum!\n"; }
		if ($text_to_copy_to_clipboard__usually_tracknum =~  /^([0-9]+)_/) {
			$text_to_copy_to_clipboard__usually_tracknum =~ s/^([0-9_]+)_.*$/$1/i;											
			if ($DEBUG_CLIPBOARD_TEXT) {  print "echo [B] it's $text_to_copy_to_clipboard__usually_tracknum!\n"; }
			$actual_tracknum = $text_to_copy_to_clipboard__usually_tracknum;												#grab it at the right moment
			$text_to_copy_to_clipboard__usually_tracknum =~ s/^0//;
		} else {
			$text_to_copy_to_clipboard__usually_tracknum = $filename_nodir;
		}
#	} else {


		if ($DEBUG_CLIPBOARD_TEXT) {  print "echo [C] it's $text_to_copy_to_clipboard__usually_tracknum!\n"; }
		$text_to_copy_to_clipboard__usually_tracknum =~ s/\.\s*/.*/g;				
#		$text_to_copy_to_clipboard__usually_tracknum =~ s/(\([^\)]*Mix\))//i;
#		$text_to_copy_to_clipboard__usually_tracknum =~ s/(\([^\)]*Version\))//i;
#		$text_to_copy_to_clipboard__usually_tracknum =~ s/(\([^\)]*Mix by [^\)]\))//i;
		$text_to_copy_to_clipboard__usually_tracknum =~ s/\(Christmas\)//gi;
		$text_to_copy_to_clipboard__usually_tracknum =~ s/\(phased\)//gi;
		$text_to_copy_to_clipboard__usually_tracknum =~ s/(\(live\))//i;
		$text_to_copy_to_clipboard__usually_tracknum =~ s/(\(demo\))//i;
		$text_to_copy_to_clipboard__usually_tracknum =~ s/(\(from [^\)]* soundtrack\))//i;
		$text_to_copy_to_clipboard__usually_tracknum =~ s/(\(has.*pop!*\))//i;
		$text_to_copy_to_clipboard__usually_tracknum =~ s/(\([0-9]+kbps\))//i;
		$text_to_copy_to_clipboard__usually_tracknum =~ s/(\([12][0-9][0-9][0-9]\))//i;
		$text_to_copy_to_clipboard__usually_tracknum =~ s/ *\.mp3$//i;
		$text_to_copy_to_clipboard__usually_tracknum =~ s/ *\.\**wav$//i;
		$text_to_copy_to_clipboard__usually_tracknum =~ s/ *\.\**flac$//i;
#NO!:   $text_to_copy_to_clipboard__usually_tracknum =~ s/\(/\\(/g;				#201510: decided to remove parens from output altogether, rather than escape them
#NO!:	$text_to_copy_to_clipboard__usually_tracknum =~ s/\)/\\)/g;				#201510: decided to remove parens from output altogether, rather than escape them
		$text_to_copy_to_clipboard__usually_tracknum =~ s/\+/\\+/g;				#turn + to \+ for regexification
		$text_to_copy_to_clipboard__usually_tracknum =~ s/\s*--\s*/.*/g;
		$text_to_copy_to_clipboard__usually_tracknum =~ s/\?/.*/g;				#they are usually _ in a filename, but if i put it ina  tag and not a filename, searching would make it fail, so let's not search for an _, let's just search for nothing if ther eis a ?
		$text_to_copy_to_clipboard__usually_tracknum =~ s/  / /g;
		$text_to_copy_to_clipboard__usually_tracknum =~ s/\s*\/\s*/.*/g;
		$text_to_copy_to_clipboard__usually_tracknum =~ s/ *[\-\&] */.*/g;			
		$text_to_copy_to_clipboard__usually_tracknum =~ s/mp3$//gi;
		$text_to_copy_to_clipboard__usually_tracknum =~ s/\.mid$//gi;
		$text_to_copy_to_clipboard__usually_tracknum =~ s/\.wav$//gi;
		if ($DEBUG_CLIPBOARD_TEXT) {  print "echo [D] it's $text_to_copy_to_clipboard__usually_tracknum!\n"; }
#		$text_to_copy_to_clipboard__usually_tracknum =~ s///gi;
#		$text_to_copy_to_clipboard__usually_tracknum =~ s///gi;
#		$text_to_copy_to_clipboard__usually_tracknum =~ s///gi;
#		$text_to_copy_to_clipboard__usually_tracknum =~ s///gi;
#		$text_to_copy_to_clipboard__usually_tracknum =~ s///gi;

		#PRE-FINAL:
		$text_to_copy_to_clipboard__usually_tracknum =~ s/ *\(/.*/g;
		$text_to_copy_to_clipboard__usually_tracknum =~ s/\) */.*/g;
		$text_to_copy_to_clipboard__usually_tracknum =~ s/_/.*/gi;

		#FINAL:
		$text_to_copy_to_clipboard__usually_tracknum =~ s/ \.\*/.*/g;
		$text_to_copy_to_clipboard__usually_tracknum =~ s/\.\*\.\*/.*/g;
		$text_to_copy_to_clipboard__usually_tracknum =~ s/\.\*$//gi;


		if ($filename_nodir !~ /[0-9]_/) { $text_to_copy_to_clipboard__usually_tracknum .= ":learned";	}
#	}

	if ($MODE eq $MODE_AUTOMARK) {
		$text_to_copy_to_clipboard__usually_tracknum = $actual_tracknum . "_";
		$text_to_copy_to_clipboard__usually_tracknum =~ s/:learned/:$ENV{AUTOMARKAS}/i;
	}

	if ($MODE eq $MODE_NORMAL) {
		print ":::: Normal-Mode-Specific output - BEGIN\n";
		print "echos $text_to_copy_to_clipboard__usually_tracknum >clip:\n";								#`echos` keeps trailing linebreak away, vs `echo`
		print ":::: Normal-Mode-Specific output - END\n";
	} elsif ($MODE eq $MODE_AUTOMARK) {

		print ":::: Automark-Specific output - BEGIN\n";
		if ($text_to_copy_to_clipboard__usually_tracknum ne "_") {
			$FAIL=0;
			##### write out the actual values to our $ATTRIB_LST (attrib.lst) file:
			### Marked:   1_09_This Killer In My House.mp3  as  "learned"   [2022-09-29 at 11:59:47]
			print   "echo."                                                                                   . ">>$ATTRIB_LST\n";	
			#rint "\necho ### $filename_nodir ==%%=> $AUTOMARK_AS ==%%=> on %_isoDate at %_time"              . ">>$ATTRIB_LST\n";							
			print "\necho ### Marked:   \"$filename_nodir\"   as  \"$AUTOMARK_AS\"    [%_isoDate at %_time]"  . ">>$ATTRIB_LST\n";							
			if ($COMMENT ne "") { print "echo ### $COMMENT"                                                   . ">>$ATTRIB_LST\n"; }
			print     "echo $text_to_copy_to_clipboard__usually_tracknum:$AUTOMARK_AS"                        . ">>$ATTRIB_LST\n";	
		} else {
			$FAIL=1;
		}
		#20230626 taking out print "echo.>>$ATTRIB_LST\n";				
		### Remove current song from current winamp playlist:
#		print "if \%AUTOMARKAS\% eq \"learned\" call remove-currently-playing-song-from-playlist\n";			#didn't work as well
		if ($AUTOMARK_AS eq "learned") { print "call remove-currently-playing-song-from-playlist\n"; }
		print "echo.\n";
		print "echo.\n";
		print "echo.\n";
		print "dir /b /s $ATTRIB_LST\n";
		print "echo.\n";
		print "\%COLOR_SUCCESS\%\n";
		print "tail $ATTRIB_LST\n";
		print "\%COLOR_NORMAL\%\n";
		if ($FAIL) {
			#2022/02: This makes sense, but only in the event of us not being able to get a "for sure" tracklist
			#this is experienced as the "no i can't mark this as XXXXX, you must type 'ec' manually" "error"
			#when that "error" happens, then we should do this:
			$text_to_copy_to_clipboard__usually_tracknum = $ENV{"AUTOMARKAS"};
			#However, this clipboard may get overwritten by the next 'ec' anyway

			print "beep\n";
			print "\%COLOR_ALARM\%\n";
			print "echo Didn't work! Must 'ec' or 'ec $text_to_copy_to_clipboard__usually_tracknum' manually!\n";
			print "\%COLOR_NORMAL\%\n";
			print "keystack ec\n";

		}
		print ":::: Automark-Specific output - END\n";
	} else {
		die("MODE of $MODE is unsupported");
	}
	print "echo. \n";
#	print "echo dg $text_to_copy_to_clipboard__usually_tracknum \n";								#`echos` keeps trailing linebreak away, vs `echo`
}




#################################################################################################
sub go_up_one_level_where_appropriate {
	my $target_dir = $_[0];
	$target_dir =~ s/[\\\/]changerrecent//i;
	$target_dir =~ s/[\\\/]changer46mos//i;
	$target_dir =~ s/[\\\/]changer//i;
	$target_dir =~ s/[\\\/]party//i;
	$target_dir =~ s/[\\\/]preferred//i;
	$target_dir =~ s/[\\\/]tolerable//i;
	$target_dir =~ s/[\\\/]best//i;
	$target_dir =~ s/[\\\/]cheese//i;
	$target_dir =~ s/[\\\/]unsorted//i;
	$target_dir =~ s/[\\\/]_unsorted//i;
	$target_dir =~ s/[\\\/]not-preferred//i;
	$target_dir =~ s/[\\\/]not-tolerable//i;
	$target_dir =~ s/[\\\/]not tolerable//i;

	##### 2011 addition when I made "changerrecent\Atari Teenage Riot" to force the new album into changerrecent before it was put into the official album list
	##### This broke certain things, as typically something like "changerrecnet" would only be at THE END of the path, where it could be safely removed.
	##### But now that it's beginning to be done in the MIDDLE of the path, it's not always safe to remove.  

	#### We need to check that the folder actualy exists before returning it now!
	print "rem :DEBUG: go_up_one_level_where_appropriate(".$_[0].")==$target_dir\n";
	if (!-d $target_dir) { return($_[0]); }
	return ($target_dir);
}
#################################################################################################




################################################################################################################
sub remap {
	my $line = $_[0];
	foreach (@REMAPS) {
		if ($_ =~ /,/) {
			($realdriveletter,$mappeddriveletter)=split(/,/,"$_");
			next if $realdriveletter =~ /^$mappeddriveletter$/i;
			push(@real,  $realdriveletter  );
			push(@mapped,$mappeddriveletter);
		}
	}
	for (my $i=0; $i < @real; $i++) {
		if ($line =~ /^($real[$i]:)/i) {
			$line =~ s/$1/$mapped[$i]:/;
			last;
		}
	}
	return($line);
}#endsub remap
################################################################################################################


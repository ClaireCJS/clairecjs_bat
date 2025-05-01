#!/usr/bin/perl

########## WHAT THIS DOES:
##########	1) Opens up the last.fm log (which can be hardcoded) and determines the song playing.
##########	2) Prints what the song is in "artist - title" format


###########  GENERAL NOTE: This fails if a song is not tagged, but as of 2011 that could be fixed with some effort.
########### PERSONAL NOTE: A lot of this functionality is duplicated in edit-currently-playing-attrib-helper.pl ... Updates here may need to go there as well.



##### DEBUG STATUS / INFORM THE USER:
my $DEBUG=0;
my $DEBUG_BAT=0;							#sets up pauses in the actual batfile which is generated
#print ":debug     is $DEBUG    \n:debug_bat is $DEBUG_BAT\n";


##### CONSTANT:
my $target_filename    = "attrib.lst";


##### NEAR-CONSTANT:
#y $METHOD   = "2011";		#Last.fm likes to change their logfile format. Remember, this method affects code below too, so search for $METHOD to update those pieces of code as well
my $METHOD   = "2024";		#no longer using last.fm
if ($METHOD eq "2008") { $AUDIOSCROBBLER_LOG_SEARCH_FOR = "CScrobbler::OnTrackPlay"; }
if ($METHOD eq "2009") { $AUDIOSCROBBLER_LOG_SEARCH_FOR = ": Sent Start for "      ; }
if ($METHOD eq "2011") { $AUDIOSCROBBLER_LOG_SEARCH_FOR = "CScrobbler::ASStart"    ; $AUDIOSCROBBLER_LOG_SEARCH_FOR2 = "Event::TrackChanged"; }	


##### DRIVE-LETTER REMAPPING VOODOO:
my $MACHINE_NAME       = $ENV{"MACHINENAME"};
my $REMAPENVVAR        = "REMAP$MACHINE_NAME";
my $REMAP              = $ENV{$REMAPENVVAR};
my @REMAPS             = split(/\s+/,"$REMAP");
#DEBUG: print "echo name=$MACHINE_NAME, \$REMAPENVVAR=$REMAPENVVAR         REMAP=$REMAP\n\n";


##### COMMAND-LINE ARGUMENTS:
#y $AUDIOSCROBBLER_LOG = $ENV{"MUSICSERVERCDRIVE"} .  ":\\program files\\winamp\\plugins\\AudioScrobbler.log.txt";
my $AUDIOSCROBBLER_LOG = $ENV{"MUSICSERVERCDRIVE"} .  ":\\Documents and Settings\\oh\\Local Settings\\Application Data\\Last.fm\\Client\\WinampPlugin.log";
if ($ENV{"HADES_DOWN"}) {
	$AUDIOSCROBBLER_LOG = $ENV{"HD1000G"}          .  ":\\Users\\oh\\AppData\\Local\\Last.fm\\Client\\Last.fm.log";
	if (!-e $$AUDIOSCROBBLER_LOG) {
		if ($DEBUG) { print "* [AA] \$AUDIOSCROBBLER_LOG of $AUDIOSCROBBLER_LOG does not exist.\n"; }
		$AUDIOSCROBBLER_LOG =                        "c:\\Users\\oh\\AppData\\Local\\Last.fm\\Client\\Last.fm.log";
	} else {
		if ($DEBUG) { print "* [AA] \$AUDIOSCROBBLER_LOG of $AUDIOSCROBBLER_LOG exists.\n"; }
	}
}

##### EMOJI COMPATIBILITY:
#use utf8;
#binmode(STDIN,  ':encoding(UTF-8)');
#binmode(STDOUT, ':encoding(UTF-8)');


##### SET FILES TO READ:
my  $ALL_SONGS_LIST     = $ENV{"ALL_SONGS_PLAYLIST"};
my  $NOW_PLAYING_TXT    = $ENV{"NOW_PLAYING_TXT"};
if (!-e $ALL_SONGS_LIST) {
	my  $ALL_SONGS_LIST     = $ENV{"MP3OFFICIAL"}        . "\\LISTS\\everything.m3u";
	if (!-e $ALL_SONGS_LIST) {
			$ALL_SONGS_LIST =                       "c:\\mp3\\LISTS\\everything.m3u";
	}
}
if (!-e $ALL_SONGS_LIST) {
	die("need all_songs_list defined via ALL_SONGS_PLAYLIST env var");
}	

														#WORK-SPECIFIC KLUDGE:
														if (($METHOD < 2024) && (!-e $AUDIOSCROBBLER_LOG)) {
																if ($DEBUG) { print "* [BB] \$AUDIOSCROBBLER_LOG of $AUDIOSCROBBLER_LOG does not exist.\n"; }
																$AUDIOSCROBBLER_LOG =                    "c:\\Users\\clioc\\AppData\\Local\\Last.fm\\Last.fm Scrobbler.log";
														}
														#LAST-DITCH 1:
														if (($METHOD < 2024) && (!-e $AUDIOSCROBBLER_LOG)) {
																if ($DEBUG) { print "* [CC] \$AUDIOSCROBBLER_LOG of $AUDIOSCROBBLER_LOG does not exist.\n"; }
																my $localappdata = $ENV{"LOCALAPPDATA"};
																$localappdata =~ s/\\/\\\\/g;
																if ($DEBUG) { print "* Last-ditch effort: Trying localappdata=  $localappdata\n"; }
																$AUDIOSCROBBLER_LOG =                    "$localappdata\\Last.fm\\Client\\Last.fm.log";
														}
														#LAST-DITCH 2:
														if (($METHOD < 2024) && (!-e $AUDIOSCROBBLER_LOG)) {
																if ($DEBUG) { print "* [CC] \$AUDIOSCROBBLER_LOG of $AUDIOSCROBBLER_LOG does not exist.\n"; }
																my $localappdata = $ENV{"LOCALAPPDATA"};
																$localappdata =~ s/\\/\\\\/g;
																if ($DEBUG) { print "* Last-ditch effort: Trying localappdata=  $localappdata\n"; }
																$AUDIOSCROBBLER_LOG =                    "$localappdata\\Last.fm\\Client\\WinampPlugin.log";
														}
														if ($METHOD < 2024) {
															if ($AUDIOSCROBBLER_LOG eq "") { print "FATAL ERROR #1: First argument must specify filename of AUDIOSCROBBLER LOG!!\n"; exit(); }
															if (!-e $AUDIOSCROBBLER_LOG)   { print "FATAL ERROR #2: $AUDIOSCROBBLER_LOG DOES NOT EXIST!!\n"; exit; }
															if ($ALL_SONGS_LIST     eq "") { print "FATAL ERROR #3: Second argument must specify filename of ALL SONGS LIST!!\n"; exit(); }
															#LAST.FM CHANGED THEIR LOGFILE TO BE MORE COMPLETE, SO THIS FILE IS NO LONGER NECESSARY FOR OUR DETERMINATION: if (!-e $ALL_SONGS_LIST)       { print "FATAL ERROR: $ALL_SONGS_LIST DOES NOT EXIST!!\n"; exit; }
															if ($DEBUG>0)                  { print "SUCCESS OPENING LOGFILE: $AUDIOSCROBBLER_LOG\n"; }
														}
														if ($METHOD < 2024) {
															##### OPEN AUDIOSCROBBLER LOGFILE TO GET LATEST TRACK PLAYED:
															open(LOG,"$AUDIOSCROBBLER_LOG") || die("FATAL ERROR: COULD NOT OPEN $AUDIOSCROBBLER_LOG, despite it existing!");
															if ($DEBUG>=1) { print "* success opening $AUDIOSCROBBLER_LOG \n* search_for = \"$AUDIOSCROBBLER_LOG_SEARCH_FOR\"\n* search_for2 = \"$AUDIOSCROBBLER_LOG_SEARCH_FOR2\"\n"; }
															my $line="";
															my $last_found="";
															while ($line=<LOG>) {
																if (($line =~ /$AUDIOSCROBBLER_LOG_SEARCH_FOR/) || ($line =~ /$AUDIOSCROBBLER_LOG_SEARCH_FOR2/)) 	{
																	if ($DEBUG) { print ":found line $line"; }
																	$last_found = $line;
																}
															}
															close(LOG);
															chomp $last_found;
															if ($DEBUG) { print "\n:last_found found line is $last_found!\n\n"; }
														}
														if ($METHOD < 2024) {
															##### TAKE LINE CONTAINING LAST TRACK PLAYED, FIX IT UP:
															my $song = "";
															if ($METHOD eq "2011") {
																$last_found =~ /^.*Sent start for (.*)$/i;		#2011B
																$last_found =~ /Event::TrackChanged (.*)$/i;	#2011A
																$song=$1;
																$song =~ s/ [0-9]*:[0-6][0-9]$//;
																$song =~ s/ \? / - /;
															} elsif ($METHOD eq "2009") {
																$last_found =~ /Sent Start for (.*)$/i;
																$song=$1;
															} elsif ($METHOD eq "2008") {
																$last_found =~ /New song detected - (.*)$/;
																$song=$1;
															}
															if ($DEBUG) { print ":song is $song!\n"; }
														}	


if ($METHOD eq "2024") {
	my $display_title;
	my $filename;
	my %metadata;
	my $MUSIC_LOG=$NOW_PLAYING_TXT;
	#print ("Method 2024 oooh, log is $MUSIC_LOG ... regex='$REGEX'\n");
	use strict;
	use warnings;
	use Data::Dumper;																		    
	#pen(my $fh, '<:encoding(UTF-8)', $MUSIC_LOG) or die "Cannot open file '$MUSIC_LOG': $!";	 	# Open the file and read its contents
	open(my $fh,                      $MUSIC_LOG) or die "Cannot open file '$MUSIC_LOG': $!";	 	# Open the file and read its contents
	my @lines = <$fh>;																		    
	close($fh);																				    
	chomp @lines;																					# Remove newline characters from each line
	$display_title = shift @lines;																 	# Extract the first two special variables
	$filename      = shift @lines;																 	# Extract the first two special variables
	my $i = 0;																				    
	while ($i < @lines) {																	    
		my $line = $lines[$i];																    
		if ($line =~ /^(\w+)=([\s\S]*)$/) {													    
			my $field = $1;																	    
			my $value = $2;																	    
			if ($i + 1 < @lines && $lines[$i + 1] =~ /^end_${field}=1$/) {						 	# Check if the next line is end_<field>=1
				$metadata{$field} = $value;														 	# Handle multi-line field
				$i += 2;																		 	# Skip the end_<field>=1 line
			} else {																			 	# Handle single-line field
				$metadata{$field} = $value;													    
				$i += 1;
			}
		} else {
			$i += 1;  # Skip any lines that don't match the pattern
		}
	}


	my   $metadataTitleToUse = $metadata{title } || "";
	my  $metadataArtistToUse = $metadata{artist} || "";
	my  $generated_display_title_separator = " - ";
	my  $generated_display_title = $metadataArtistToUse . $generated_display_title_separator .  $metadataTitleToUse;
	if ($generated_display_title eq $generated_display_title_separator) { $generated_display_title="None"; }
	
	if ($DEBUG>0) {
		print "echo * Display Title: $display_title\n";				# Print the first two special variables
		print "echo * Generated Display Title: $generated_display_title\n";				# Print the first two special variables
		print "echo * Filename: $filename\n";
		print "echo * Metadata Hash Table:\n";						# Print the entire hash table for debugging
		my $meta=Dumper(\%metadata);
		$meta =~ s/^/echo /ig;
		print $meta . "\n";
	}
	
	print $generated_display_title . "\n";
}



my $PROCESS_PARENTHETICALS=0;
if (($METHOD eq "2009") || ($METHOD eq "2008")) { $PROCESS_PARENTHETICALS=1; }

if ($PROCESS_PARENTHETICALS) {	
			#yes = original way =  whitelist = save parentheticals we want, reomve all parentheticals, then add these back - this was necessary due to the old format of the last.fm log being completely ambiguous and adding its own parentheticals past ones in the tag
			#no  =    new   way = blabcklist = only remove parentheticals we don't want = as of 2011, last.fm log file is no longer ambigulous, and this is the better way

	##### Because I remove move things in parenthesis, anything that this is a mistake for must be preserved for later. This is a feature added in 2009:
	$parenthetical_title_to_save="";
	$DO_MORE=1;
	while ($DO_MORE) {
		if (($song =~ /(\([^\)]*Mix\))/i) 
			|| ($song =~ /(\([^\)]*Version\))/i) 
			|| ($song =~ /(\([^\)]*Mix by [^\)]+\))/i) 
			|| ($song =~ /(\(live\))/i)
			|| ($song =~ /(\([^\(]*USA[^\)]*\))/i)
			|| ($song =~ /(\([^\(]*[12][0-9][0-9][0-9][0-1][0-9][0-3][0-9][^\)]*]\))/i)
			|| ($song =~ /(\(The [^\)]*\))/i)
			|| ($song =~ /(\(cleaner\))/i)
			|| ($song =~ /(\(by [^\)]*\))/i)
			|| ($song =~ /(\(a *capella\))/i)
			|| ($song =~ /(\([^\(]*demo[^\)]*\))/i)
			) {
			$parenthetical_title_to_save .= " $1";
			$song =~ s/$1//;
			$DO_MORE=1;
			#OLD: $parenthetical_title_to_save =~ s/\(/\\\(/;#$parenthetical_title_to_save =~ s/\)/\\\)/;	#unnecessary, becuase this is done later
			if ($DEBUG) { print ":\$parenthetical_title_to_save is [AA] $parenthetical_title_to_save!\n"; }
		} else {
			$DO_MORE=0;
		}
	}

	##### Strip parentheticals:
	if    ($song =~ /\)\)$/)          { $song =~ s/\([^\(\)]*\([^\(\)]*\)\)$//; }		#nested parnethesis
	elsif ($song =~ /\(.*\).*\(.*\)/) { $song =~ s/(\(.*\).*)(\(.*\))/$1/; }			#may catch 3-parentehsis songs - MAY HAVE TO UPDATE IN THE FUTURE
	else                              { $song =~ s/\(.*\)//; }							#if only one parenthesis take it out - MAY HAVE TO UPDATE TO ONLY DO THIS IF IT'S AT THE *END* OF THE LINE

	##### If there was parenthtical stuff we saved from before ["(remix)", "(demo)", etc], they were stripped, so now we add it back on:
	$song .= " $parenthetical_title_to_save";
} else {
	#Process parentheticals the new way - which means we remove parentheticals that we explicitly don't like
	#Many songs tested - this block of code is not yet necessary! But with a possible input set of every audio filename on the planet, we may use this yet!
}



##### Final scrub:
$song =~ s/\(\)//g;
$song =~ s/\s+$//;
$song =~ s/^\s+//;
while ($song =~ /  /) { $song =~ s/\s\s/ /g; }

##### This should be precisely what we want now:
print $song;


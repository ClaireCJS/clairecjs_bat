
#### TODO! MAJOR! FLAC FILES DO NOT HAVE GENRES EXTRACTION HANDLED!!!!! OR ANYTHING I GUESS!!!!





















### TODo - band - album list also



### TODO: can i do something like : pretty good:pretty good*2 
##                -- and will the doubling affect through to yet another meta (prettyGoodBuildUpon=prettyGood,farty)

######### These 2 ideas are the same idea, actually, and are currently in testing:

	#### DONE, TESTED, NOT FULLY INTO PRODUCTION YET: 
	#### PROBABILITY - a song will only be in the playlist 5% of the time: 
	#### revolution.action.*shitty mix:changer*0.5,somethingelse*50,etc

	#### TODO: DUPLICITY - a song may appear in the playlist more than once. Typically we'd double it like so:
	#### revolution.action.*best mix ever:2X,foo,bar


#### TODO: finish -p option - rather than processing 1 attrib list, 
####            make it process one directory, set append mode, 
####             and open >> and append to lists instead            (Why?)


######### NEXT TODO - MAKE .DAT FILE OF ARTIST-SONG TAGS SO WE CAN CROSSMATCH EVILLYRICS LRC! sync-filelist helper will need to copy .* instead of .mp3 with  /[!*.bak] modifier










##### CURRENT DEVELOPMENT DEBUGS:
my $DEBUG_ATTRIBUTE_WEIGHTS      = 0;							#reserve value: 0 / other values: 1-2
my $DEBUG_META_ATTRIBUTE_WEIGHTS = 0;							#reserve value: 0 / other values: 1

##### RESERVE DEBUGS:
my $DEBUG_BASE_ATTRIB_PRINT_EACH_LINE=0;                    #reserve value: 0
my $DEBUG_GENRE_2015=0;										#reserve value: 0 / NOTE: this makes indexer.log too big for EditPlus to open!
my $DEBUG_LIST_ALL_ATTRIBUTE_LISTS_BEING_PROCESSED=0;		#reserve value: 0
my $DEBUG_PROCESS_ATTRIBUTELIST_CALLS=0;					#reserve value: 0
my $DEBUG_EVERYTHING=0;										#reserve value: 0		#debugs generation of everything.m3u playlist, does NOT debug all debugs
my $DEBUG_NOW=0;											#reserve value: 0
#my $DEBUG_MAX_LISTS = 20;	#								#reserve value: unset
#my $DEBUG_META = 11;										#reserve value: unset / 0,...,6,10,11
#$DEBUG=10;													#reserve value: unset / standard value: 10
#$DEBUGMMDD=1;												#reserve value: unset / used for developing
##$DEBUG_FILEFIND = 5;										#reserve value: unset / good value = 5 

##### RARELY-USED META DEBUGGING:
#$DEBUG_ATTRIBWATCH_ATTRIBNAME="Dad's picture frame REAL";
#$DEBUG_ATTRIBWATCH_ATTRIBNAME="vintage";
#$DEBUG_ATTRIBWATCH_ATTRIBNAME="changer.*6.*mos";
#$DEBUG_ATTRIBWATCH_ATTRIBNAME="NotLast6Months";
#$DEBUG_ATTRIBWATCH_ATTRIBNAME=".*6mos.*";
#$DEBUG_ATTRIBWATCH_ATTRIBNAME="last6mos";

##### THIS ONE DEBUG MUST ALWAYS BE SET BECAUSE I'M LAZY... TO "TURN IT OFF" SIMPLY HAVE IT SET TO A RANDOM STRING OF CHARACTERS:
 $DEBUG_FILEWATCH_FILENAME="�qadasdfrts";  #reserve value: you have to leave this set (uncommented) when not debugging -- use random keypresses to ensure it never pops up (weak, yes) - start with a unicode character so it always mismatches right away 
#$DEBUG_FILEWATCH_FILENAME="postcard.*gun.*cazy";  #you have to leave this set (uncommented) when not debugging -- use random keypresses to ensure it never pops up (weak, yes)
#$DEBUG_FILEWATCH_FILENAME="Nirvana.*live.*roma.*polly";
#$DEBUG_FILEWATCH_FILENAME="Silent.Lucidity";
#$DEBUG_FILEWATCH_FILENAME="Slayer.*South.*Heaven.*Silent.*Scream";
#$DEBUG_FILEWATCH_FILENAME="Demento.*09.*wrapping";
#$DEBUG_FILEWATCH_FILENAME="Meaty.*Christmas";							#20141205: discovered bug in Christmas.m3u
#$DEBUG_FILEWATCH_FILENAME="Cosby";										#20141205: discovered bug in Christmas.m3u
#$DEBUG_FILEWATCH_FILENAME="beast.wars.neo.*cut.*off";					#20150925: found bug - songs matching this in /tolerable/ folder were in changer.m3u! 
#$DEBUG_FILEWATCH_FILENAME="Violent.*Femmes.*1982.*Kiss Off";			#201604xx: for bugfixg probability-based playlisting
#$DEBUG_FILEWATCH_FILENAME="Kuru.Kuru";									#20160720: this came back as regression error after weights were added, WTF!
#$DEBUG_FILEWATCH_FILENAME="Bananarama.*Cruel.*Summer";					#2017-2022/02/06 - this had some weiord problem that i think went away














##### External perl packages required by this script:
push(@INC,"c:/perl/site/lib"); $|=1;
use MP3::Tag;         	#<== only called later in program if INI file specifies PROCESS_GENRES=1
use File::Find;

##### Let's keep things strict (conversion from non-strict was a PAIN!!!)
use strict;
use vars qw($DATEINDEX $LONGEST_POSSIBLE_EXECUTION_OF_THIS_SCRIPT_IN_MINUTES $FORWARD_SLASHES 
	$DEBUG_FILEWATCH_FILENAME $SKIP_DATE $nummeta $num_dated_filelists_created $SKIP_FILEFIND
	$genres_encountered $artists_encountered $albums_encountered $songs_encountered 
	$num_dated_filelists_created $DEBUG $line $tmpfile
	$tmpattrib $mode $attrib2use $param $name $lookingForTemp $FOUND $DEBUG_QFF @filelist $sec
	$mp3_file $tmpfilelist $filesfound $FIRST_REPORT $attriblist $valid_extension @ERRORS $mon
	$name2 $num_days_back $num_files_to_check $GENRE_PREFIX $filesfound $dir2lookin $tmpdir $i 
	$NOWYYYY $NOWYYYYMM $NOWYYYYMMDD $NOWYYYYMMDDHH $NOWYYYYMMDDHHSS $NOWMM $NOWDD $NOWMMDD 
	$NOWmin $REQUIRE_INI  $num_written $stat_num_index $stat_num_found $stat_num_dir_e $blocks
	$SKIP_GENRE $min $premsg $NO_FILEWRITE $TRIGGER_FILE $verbose $ATTRIBUTE_LIST $ATTRIBUTE_DB 
	%YYYY_ENCOUNTERED %YYYYMM_ENCOUNTERED %YYYYMMDD_ENCOUNTERED %YYYYMMDDHH_ENCOUNTERED $value
	%YYYYMMDDHHMM_ENCOUNTERED %YYYYMMDDHHMMSS_ENCOUNTERED $GATHER_INFO_ONLY $genre $artist $album 
	$song @regexes $SKIP_SLASH_CONVERSION $program_start_time
	$yyyyvalue $yyyymmvalue $yyyymmddvalue $yyyymmddhhvalue $yyyymmddhhmmvalue $lookingFor 
	$yyyymmddhhmmssvalue $tmpext $temp $tmpdate @tmpkeys @tmpkeys2 $tmp $tmpinterval $tmpname 
	$yyyy $yyyymm $yyyymmdd $yyyymmddhh $yyyymmddhhmm $yyyymmddhhmmss $datefilelist $wday
	$ATTRIB_PREFIX $META_PREFIX $DATE_PREFIX $DATE_RANGE_PREFIX $TODO_FILE $tmpregex $ino
	$DEBUG_ATTRIBWATCH_ATTRIBNAME $DEBUG_CONVERT $DEBUG_SKIPGENRE $DEBUG_META $DEBUG_SKIPDATE
	$DEBUG_DATE_FROM_INDEX $DEBUG_DISPLAY_ALL_ATTRIBUTE_LIST_FILENAMES $DEBUG_TOTALS $NOWHH 
	$ATTRIBUTETOUSE $TOTAL_ATTRIB_CREATED $dir4test $mday $yday $OVERFLOW $size $rdev $gid
	$yyyymmdd_counter $currentgenre4access $IGNORE_BASE_ATTRIBUTE_FILE $hour $year $nlink
	@INPUTFILELIST @INPUTREGEXLIST $uid $atime $mtime $ctime $blksize $mlink $isdst $when
	%FILEKEY_YYYYDATEVALUE %FILEKEY_YYYYMMDATEVALUE %FILEKEY_YYYYMMDDDATEVALUE $FILEDIR
	%FILEKEY_YYYYMMDDHHDATEVALUE %FILEKEY_YYYYMMDDHHMMDATEVALUE $tmp2 $tmpaccess $LOG $dev
	%FILEKEY_YYYYMMDDHHMMSSDATEVALUE $ACCESS_INDEX %FILES_BY_ACCESS %ATTRIBUTES_BY_ACCESS
	@tmpfilelist $datevalue $datemode $tmpout $fileRegex $fileRegexes @attributes $ISBASE
	$DEBUG_MAX_LISTS $SKIP_FILEMATCH_ERRORS %ATTRIBUTES $tmpBeginMM $tmpBeginDD $tmpEndMM 
	$tmpEndDD $DEBUGMMDD $tmpBeginMMDD $tmpEndMMDD $tmptmptmptmp %ATTRIBUTE_WEIGHTS 
	$DEBUG_FILEWATCH_FILENAME $DEBUG_FILEWATCH_META $linenum
	);






### PRE-60G-HARDDRIVE-CRASH NOTES THAT DON'T REALLY APPLY ANYMORE...
######### LATEST BUG: figure out why 'mp3\misc\1980s\ed1ebrickell - circle' is showing up in party.m3u when it seems that it shoudln't
### FUTURE EXPANSION NOTES:
#TODO
# GENRE -- allow genre to be referenced by meta-attribute rules
#   This may work already! Try it!
#   EXAMPLE: hard:+genre-id3-Punk,+genre-id3v1-Metal,+genre-id3v2-Metal (Speedmetal)
#    -- add rule non-music:+id3genre-sound clip
# LINK TO TAG -- like our normal tags but with a location .. #             MAY NOT BE NECESSARY.... 01_:\.\.\\whatever
# LOCATION tag -- to place filelists in specific areas...
#      since it's location BY TAG this goes in the meta attribute file
#      tag:*LIVES IN* <directory>
#      tag:*ALSO LIVES IN* <directory>
#      EX: samhain:*ALSO LIVES IN* <directory>
#      * however, how do we parse directories? Some regex dirmagic?
#      we could have tags isolated within the normal attribute files
#      EX: d:\mp3\misfitssamhaindanzig\samhain\attrib.lst
#          would contain a line kinda like:
#             **filelist only lives here for tag:samhain
#             **filelist also lives here for tag:samhain
#             or abbreviated
#             **only here:samhain
#             **also here:samhain
#       MAY NEED BOTH SOLUTIONS... especially when i want the meta-
#          attribute 'tributes' filelist to be in mp3\tributes
#         NO... cause in mp3\tributes i could just have a
#        "**also here:tributes"
#       THE TRICK IS TO WAIT TIL WE'RE COMPLETE

#### DOCS:
#### This program locates various attrib.lst attribute files that live
#### with various files (in various directories, various collections).
#### It then processes these attribute files in order to be able to assign
#### an infinite number of attirbutes to any files.  Attributes automatically
#### chase file renames because rather than hardcoding filenames we use
#### a minimal regular expression to match the file (usually the track number).
#### For instance, we can say "02::sucks,sucksbad" and any filename
#### with 02 in it will automatically be added to the 'sucks' attribute
#### filelist as well as the 'sucksbad' attribute filelist.
#### The format is <regularexpression>:<attributelist>.  You can use
#### 1 colon or 2 to separate. You will need to use 2 to separate if
#### you want to do something like:   c:\mp3\whatever.mp3::sucks
#### Leave the regularexpression empty to affect all files in that dir and its subdirs.
#### Occasionally, we want attribute lists that reference hardcoded
#### drives and directories, so use 2 colons to separate fileexpression from
#### attribute. Also, you can put a '-' in front of an attribute to REMOVE
#### a file from an attribute it would otherwise fall under.

#### IMPORTANT NOTE: NEVER USE BACKSLASHES FOR DIR SEPARATORS! ONLY SLASHES!

#### Requires: a full perl install, not just a standalone exe.
#### Go to www.activestate.com for this.

#### ** META-ATTRIBUTE FILE **
#### *** THE SAMPLE META-ATTRIBUTE FILE PROBABLY HAS BETTER DOCS. ***
#### The meta-attribute file is a complex second-pass of logic to create complex attributes.
####
#### For example, if you want all covers that are not in mono, you may do something like:
####     non-mono covers:+covers,-mono
#### which basically says "non-mono covers are comprised of all files that are covers,
#### sub subtracting out all files that are mono.  Of course this wont work if there
#### isn't already a rule for covers and mono files.
####
#### If you wanted a group that was ****everyth1ng**** BUT something, like maybe
#### "everyth1ng that isn't for children", it may look something like this:
####     grownup stuff:+everything,-children
#### This program, by default, has an attribute called 'everything' that is every file.
####
#### ** ORDER IS IMPORTANT WITH META-ATTRIBUTES **
#### Perhaps you want to do something like, start with all cartoon files,
#### subtract all mono files, but then add back all tribute files
#### (thus, mono tributes would still exist), this could be accomplished like:
####      stereo cartoonmusic and tributes:+cartoonmusic,-mono,+tributes
#### If the mono tributes weren't to your liking and you didn't want them
#### at all, you would simply do this instead:
####      stereo cartoonmusic and tributes:+cartoonmusic,+tributes,-mono
####
#### GOT GUESTS?
#### If "Mark" hates "Slayer", we could add a base rule akin to:
####    \\Slayer\\:hated by Mark
#### If "Rich" hates "Metallica", we could add a rule akin to:
####    \\Metallica\\:hated by Rich
#### Then we could make a meta rule akin to:
####    hated by guests:+hated by Rich,+hated by Mark
#### Now we can take our standard "preferred" meta rule and customize it
#### for when we have guests over:
####    preferred with guests:+preferred,-hated by guests
#### *** THE SAMPLE META-ATTRIBUTE FILE PROBABLY HAS BETTER EXAMPLES AND/OR DOCS. ***


#### THE DATA STRUCTURE:
#### The main data stricture is %ATTRIBUTES, which is a hash table. 
#### The keys are attributes, such as "party", "love song", "preferred", etc. *THEY ARE ALWAYS LOWERCASE*.
#### The values to each key are *another* hash table (the "inner hash tables").
#### For the inner hash tables, the keys are filenames, such as "c:\mp3\whatever.mp3".
#### For the inner hash tables, the values are generally either:
####  -1 (blacklisted), 0 (previously added but then removed), 1 (added), 2 (force-added/whitelisted)
#### Added means "Yes, this file belongs to this attribute. EX: Yes, this is a party song."
#### Removed means that one rule added it, but later another rule removed it. This can happen.
#### Blacklisted means it has been removed with "--", which means that it wont be added   again, even if a rule says to. (self-overriding)
#### Whitelisted means it has been added   with "++", which means that it wont be removed again, even if a rule says to. (self-overriding)



### some "raw" "documentation":
#ATTRIBFILES.DAT = $ATTRIB_LIST_INDEX = list of all attrib.lst files
#	@attributelists = list of index files that is put to attribfiles.dat
#
#FILES.DAT = $FILE_INDEX = list of all files
#	&writefilesindex writes the actual file to disk
#	&readfilenamesfromfileindex will read the file from disk to memory

#201604: any attrib.lst can use a line containing "!NoWarningsForNextLine!" to suppress warnings for the next line

######################################################################################
######################################################################################
######################################################################################
######################################################################################
######################################################################################
######################################################################################
######################################################################################
######################################################################################

##### CONFIG:											#just started this section in 2015 so it's kinda pointless
my $USE_BACKSLASHES_INSTEAD_OF_SLASHES=1;
my $LONGEST_POSSIBLE_EXECUTION_OF_THIS_SCRIPT_IN_MINUTES="6000";		#Needed to stop fatal errors due to time differences when using "DATE NOW" tags. Unfortunately, now that this has been repurposes to index our photograph collection - THAT collection takes almost 4 days to index. So the original restriction pretty much never happens now.
my $UNIX         = 0; 
my $SKIP_GENRE   = 0;
my $DELIMITER    = "::::";		#internal data structure delimiter

##### MAIN PROGRAM:
my @COLLECTIONS			= (); #("c:/");
my $ATTRIBUTELIST_DIR	= ""; #"c:/My Documents";            #FILELIST DIR. CURRENT CONTENTS WILL BE RECYCLED. NO TRAILING SLASH. MUST EXIST.
my $METAFILELIST_DIR	= ""; #"c:/My Documents"         #METAFILELIST DIR. CURRENT CONTENTS WILL BE RECYCLED. NO TRAILING SLASH. MUST EXIST.
my $DATEFILELIST_DIR	= ""; #"c:/My Documents";    #FILELIST-BY-DATE DIR. CURRENT CONTENTS WILL BE RECYCLED. NO TRAILING SLASH. MUST EXIST.
my $GENREFILELIST_DIR	= ""; #"c:/My Documents";   #FILELIST-BY-GENRE DIR. CURRENT CONTENTS WILL BE RECYCLED. NO TRAILING SLASH. MUST EXIST.
my $ARTISTFILELIST_DIR  = $GENREFILELIST_DIR;
my $ALBUMFILELIST_DIR   = $GENREFILELIST_DIR;
my $SONGFILELIST_DIR    = $GENREFILELIST_DIR;
my $BASE_ATTRIBUTE_FILE	= ""; #"c:/mp3/mp3-base-attributes.lst";          #base attribute file, applied to all collections
my $META_ATTRIBUTE_FILE	= ""; #"c:/mp3/mp3-meta-attributes.lst";          #meta-attribute file, for personal black magic
my @EXTENSIONS			= ""; #("mp3","wav","voc","mod","stm","au","vqf","wma","ogg");
my $ATTRIB_PREFIX		= ""; #"attribute-";
my $META_PREFIX			= ""; #"attribute-";
my $DATE_PREFIX			= ""; #"attribute-date-";
my $DATE_RANGE_PREFIX	= ""; #"attribute-date-range-";
my $GENRE_PREFIX		= ""; #"attribute-genre-";
my $filelistextension	= ""; #"m3u";    #default filelist extension
## Filename for attribute lists is 'attrib.lst'. THIS IS HARDCODED to force compatibility with other users.
my $INI					= "";
my $FILE_INDEX			= "";
my $STATS_INDEX			= "";
my $ACCESS_INDEX		= "";
my $ATTRIB_LIST_INDEX	= "";
my $ATTRIBUTE_DB        = "";
my $GENRE_INDEX			= "";
my $ARTIST_INDEX        = "";
my $ALBUM_INDEX         = "";
my $SONG_INDEX          = "";
my $GENRE_LIST			= "";
my $ARTIST_LIST			= "";
my $ALBUM_LIST			= "";
my $SONG_LIST			= "";
my $DATE_INDEX			= "";
my $COLLECTION_INDEX	= "";
my $INVERSE_INDEX		= "";		#this one is more grep-friendly
my $INVERSE_INDEX_2		= "";		#this one is more database-import friendly
my $numEncountered=0;
my $DATE_INDEX_READ=0;
my $numEncounteredDirs=0;
my $firstpassfilelists=0;
my $SKIP_MONTH_TIMESLICING=0;
my $SKIP_DAYS_AND_HOURS_TIMESLICING=0;
my $NO_GENRE_PROCESSING_WHATSOEVER=0;
my @TODO=();					#textual lines of stuff "todo" encountered when reading attribute lists comments
my @files=();
my %GENRE=();
my %ARTIST=();
my %ALBUM=();
my %SONG=();
my $genres_encountered  = 0;
my $artists_encountered = 0;
my $albums_encountered  = 0;
my $songs_encountered   = 0;
my %ALLFILES=();				#key=filename,value=2 if it's of valid extension that we are indexing, less if not (ie random other files like thumbnails, 0-byte comments, CRAP)
local %ATTRIBUTES=();			#changed from "my" to "local" 20081123 after years if strict adherance to proper paremeter passing, but still having problems with setting new ATTRIBUTES inside of subroutines, especially when trying to make NotLast6Months work
local %ATTRIBUTE_WEIGHTS=();	#key={$filename$delimiter$attribute},value=weight
my %FILES_BY_DATE=();
my @attributelists=();
my %FILES_BY_ACCESS=();			#key=filename,value=access_level ONLY for nondefault access levels
my %INVERSE_ATTRIBUTES=();
my %FILES_BY_DATE_FINAL=();
my %ATTRIBUTES_BY_ACCESS=();
my %DATE_ATTRIBUTES_WRITTEN=();
my %DATE_RANGE_ATTRIBUTES_WRITTEN=();
my %FILEKEY_YYYYDATEVALUE=();
my %FILEKEY_YYYYMMDATEVALUE=();
my %FILEKEY_YYYYMMDDDATEVALUE=();
my %FILEKEY_YYYYMMDDHHDATEVALUE=();
my %FILEKEY_YYYYMMDDHHMMDATEVALUE=();
my %FILEKEY_YYYYMMDDHHMMSSDATEVALUE=();
my $YYYY_ENCOUNTERED=();
my $YYYYMM_ENCOUNTERED=();
my $YYYYMMDD_ENCOUNTERED=();
my $YYYYMMDDHH_ENCOUNTERED=();
#my $YYYYMMDDMMHHMM_ENCOUNTERED=();		#currently unused
#my $YYYYMMDDMMHHMMSS_ENCOUNTERED=();		#currently unused
my $SKIP_DATE=0;
my $SKIP_INVERSE_LIST=0;
my $TOTAL_BYTES_INDEXED=0;
my $SKIP_FILEMATCH_ERRORS=0;
my $SKIP_ERROR_COLLECTION_MISSING=0;
my $TOTAL_BYTES_INDEXED_TEXT=0;
my $TOTAL_BYTES_INDEXED_VIDEO=0;
my $TOTAL_BYTES_INDEXED_IMAGE=0;
my $TOTAL_BYTES_INDEXED_AUDIO=0;
my $TOTAL_FILES_INDEXED_TEXT=0;
my $TOTAL_FILES_INDEXED_VIDEO=0;
my $TOTAL_FILES_INDEXED_IMAGE=0;
my $TOTAL_FILES_INDEXED_AUDIO=0;
my $TOTAL_BYTES_INDEXED_OTHER=0;
my $TOTAL_FILES_INDEXED_OTHER=0;
my $MAX_LISTS=$DEBUG_MAX_LISTS || 0;
my $FORWARD_SLASHES=1;											#doesn't work in windows if this isn't set... no clue what happens in unix
my $CLEANPRE="del /q";
my $CLEANPOST="";
my $MAX_WIDTH=79;					#max number of columns when displaying info. can set environment varabiel COLUMNS to override this (does not enhance functionality, but may look cooler, if you ahve more than 80 columns set an environment variable named 'COLUMNS' to your # of columns for cooler output)
my $tmpaccess="";
my $tmpregex="";
my $tmpattr="";
my $tmpline="";
my $tmp1="";
my $tmp2="";
my $tmp="";
my $tmpdir="";
my $tmpname="";
my $tmpfname="";
my $tmpvalue="";
my $tmpattribute="";
my $tmptmptmptmp="";
my $warnings=1;
my $SKIP_SLASH_CONVERSION=0;
my $program_start_time=time();


# The first value, a number, is how many days for that filelist.
# The second value, a string, is what you will call this filelist.
# For example, you may have "1","Yesterday's Music" for music from the
# past day, or 20,"Last 20 days music" for another example:
my %INTERVALS=(
             #     1, "A - last 1 day",			#1
             #     2, "B - last 2 days",		#2
             #     3, "C - last 3 days",		#3
             #     4, "D - last 4 days",		#4
             #     5, "E - last 5 days",		#5
             #     6, "F - last 6 days",		#6
                   7, "A - last 1 week",		#7
                 2*7, "B - last 2 weeks",		#14
                  30, "C - last 1 month",		#30
                2*30, "D - last 2 months",		#60
                3*30, "E - last 3 months",		#90
                6*30, "F - last 6 months",		#180
                9*30, "G - last 9 months",		#270
                 365, "H - last 1 year",		#365
               2*365, "I - last 2 years",		#730
             # 3*365, "P - last 3 years",		#1095
             # 4*355, "Q - last 4 years",		#1460
               5*365, "J - last 5 years",		#1825
             # 6*365, "S - last 6 years",		#2190	
             # 7*365, "T - last 7 years",		#2555
             # 8*365, "U - last 8 years",		#2920
             # 9*365, "V - last 9 years",		#3285
              10*365, "K - last 10 years",		#3650
			);
                 ###  ^ these letters A-V are meaningless but required, by convention, since other programs read these lists and 
				 ###    make sense of it all, and some of my personal logic has been coded in some of my other personal scripts...
                 ###    The purpose of the letters is that the file listing sorts the alphabetically as it does chronologically 


#any new security levels also have to be added to <photo album viewer> view.pl and be in sync with the database and also be added to &RemapSecurityLevelWordToNumber and the standards-and-pratices file
use constant SECURITY_LEVEL_NOBODY			=> 9999;		#files viewable by nobody, not even us
use constant SECURITY_LEVEL_ADMIN			=> 1000;		#security levels from the database
use constant SECURITY_LEVEL_INTIMATE		=> 900;
use constant SECURITY_LEVEL_FRIEND			=> 666;
use constant SECURITY_LEVEL_FRIEND_CLOSE	=> 777;
use constant SECURITY_LEVEL_FAMILY			=> 500;
use constant SECURITY_LEVEL_STRANGER		=> 250;
use constant SECURITY_LEVEL_DISABLED		=> 10;
use constant SECURITY_LEVEL_HIGHEST			=> SECURITY_LEVEL_NOBODY;	#highest valid security level, including security levels that cause NO ONE to be able to view a file (used to stop index.htmls and such from being viewable)
use constant SECURITY_LEVEL_LOWEST			=> SECURITY_LEVEL_STRANGER;	#not the lowest existing security level, but the lowest *valid* security level. security levels for disabled accounts would not count!
use constant SECURITY_LEVEL_DEFAULT			=> SECURITY_LEVEL_STRANGER;

######################################################################################
######################################################################################
######################################################################################
######################################################################################
######################################################################################

##### MAIN MEAT:

### Initialize:
use open ':std', ':encoding(UTF-8)';				#make STDOUT support unicode
&gettimeinfo;										#201603 - moved from end of initialization to beginning of initialization
&logprint("*** Indexing started at $NOWYYYYMMDDHHSS");
&determine_delete_command;
&determine_max_width;
&initial_command_line_processing;
&read_ini;
&openlog;	#can only be done after read_ini, because it is in the meta-attribute directory and that is determined by INI
&create_collection_index;
&secondpass_command_line_processing;				#because INI can change things
&some_sanity_checks;
#&gettimeinfo;										#was here 2000-2016, but moved earlier


### Gather data:
&find_the_files;	#writes values into @files
#&gettimeinfo;		#old position
if ($SKIP_DATE==1) { &readdatedatafromdateindex("debug_barney"); }		#abandoned testing (2014?) .. can skip_date even be 1 here? probably not. ... BARNEY is a token for debugging that I used :)
else               { &gather_file_dates;                         }		#abandoned testing (2014?)

### Output our genre-specific information, since we have enough info to do that now, and do not need to wait (helps to debug this code faster):
&create_genre_filelists(0);
&write_genre_index;
&write_artist_index;
&write_album_index;
&write_song_index;

### Gather our main set of information, Clio's attribute files:										#$DEBUG_QFF=2;#Turn this on here if you want to test filefinding, but not test filefinding for finding attrib.lsts....
&process_each_attribute_list;

### Delete old data:
DONE:										#label goto'ed by -p option -- which was never written -- so it's never actually used -- since gotos are kinda bad anyway, I don't feel so bad that it's never really used
&delete_old_lists;

### Create playlists:
#&create_genre_filelists(0);					##1\	   #201210: doing this before attrib.lst processing because it doesn't depend on attribute lists
&create_attribute_filelists    (\%ATTRIBUTES);  ##2 \_____ these 4 lines write our filelists
&create_date_filelists         (\%ATTRIBUTES);	##3 /																			#foreach my $key (keys %ATTRIBUTES) { print "\n \%ATTRIBUTES KEY = $key \t VALUE = $ATTRIBUTES{$key}"; }		#print "\n\nMAJOR TESTING (everything):             \n***** \"" . &hashdump(\%{$ATTRIBUTES{"everything"             }}) . "\" *****";	## . &tostr(keys(%{$ATTRIBUTES{"everything"             }}))		#print "\n\nMAJOR TESTING (changerrecent):          \n***** \"" . &hashdump(\%{$ATTRIBUTES{"changerrecent"          }}) . "\" *****";	## . &tostr(keys(%{$ATTRIBUTES{"changerrecent"          }}))		#print "\n\nMAJOR TESTING (changer46mosfolderonly): \n***** \"" . &hashdump(\%{$ATTRIBUTES{"changer46mosfolderonly" }}) . "\" *****";	## . &tostr(keys(%{$ATTRIBUTES{"changer46mosfolderonly" }}))		#print "\n\nMAJOR TESTING (range-F - last 6 months):\n***** \"" . &hashdump(\%{$ATTRIBUTES{"range-F - last 6 months"}}) . "\" *****";	## . &tostr(keys(%{$ATTRIBUTES{"range-F - last 6 months"}}))		#print "\n\nMAJOR TESTING (range-J - last 5 years): \n***** \"" . &hashdump(\%{$ATTRIBUTES{"range-J - last 5 years" }}) . "\" *****";	## . &tostr(keys(%{$ATTRIBUTES{"range-J - last 5 years" }}))
&create_metaattribute_filelists(\%ATTRIBUTES);	##4/																			#print "\n\nMAJOR TESTING (last6mos):               \n***** \"" . &hashdump(\%{$ATTRIBUTES{"last6mos"               }}) . "\" *****";	## . &tostr(keys(%{$ATTRIBUTES{"last6mos" }}))


### Output various indexes:
#OLD:&create_inverse_index(\%INVERSE_ATTRIBUTES);
&create_inverse_index();						##1\
#&write_genre_index;							##2 \_____ these 4 lines write our main indexes					#201210: doing this before attrib.lst processing because it doesn't depend on attribute lists
&create_attribute_index(\%ATTRIBUTES);			##3 /
&create_access_index(\%FILES_BY_ACCESS);		##4/

### Output statistics, trigger file, final report to user:
&create_stat_index;								#statistical index
&create_trigger_file;							#0-byte trigger file - used to be used to trigger a databaser refresh (which deleted the trigger file) (which is how it works) 
&final_report;									#report for user saying what's happening
&closelog;										#close all the log files

######################################################################################
######################################################################################
######################################################################################
######################################################################################
######################################################################################


####################################################################################
sub determine_max_width {
	#ASSUMES global $MAX_WIDTH
	if ($ENV{columns} ne "") { $MAX_WIDTH = $ENV{columns}-1; }
}#endsub determine_max_width
####################################################################################

###################################################################################################
sub determine_delete_command {
	if ($UNIX) {
	    $CLEANPRE = "rm -i";   #I'll keep the -i in, don't want to trick you (the user).
		$CLEANPOST="";
	} else {
		$CLEANPRE = "move /q";
		if    (-d "c:\\recycler") { $CLEANPOST = "c:\\recycler"; }
		elsif (-d "c:\\recycled") { $CLEANPOST = "c:\\recycled"; }
		else  { &death("FATAL ERROR: c:\recycled or c:\recycler must exist.\n"); }
	}
}#endsub determine_delete_command
###################################################################################################

#######################################################################################################################
sub final_report {
	&log("\n*** ".sprintf("%3u",($nummeta+$firstpassfilelists+$num_dated_filelists_created+$genres_encountered
		                         +$artists_encountered+$albums_encountered+$songs_encountered)));
	&log(" total filelists created (normal=$firstpassfilelists,dated=$num_dated_filelists_created," . 
		 "genre=$genres_encountered,artists=$artists_encountered,albums=$albums_encountered,songs=" . 
		 "$songs_encountered,meta=$nummeta).\n");

	
	my $program_end_time = time();
	my $elapsed_seconds  = $program_end_time - $program_start_time;
	my $elapsed_minutes  = $elapsed_seconds / 60;
	my $elapsed_hours    = $elapsed_minutes / 60;
	#DEBUG: &log("program_start_time is $program_start_time\nelapsed_seconds is $elapsed_seconds\nelapsed_minutes is $elapsed_minutes\nelapsed_hours is $elapsed_hours");
	my $elapsed_time_string = sprintf("Elapsed Time: %.1f minutes (%.1f hours)", $elapsed_minutes, $elapsed_hours);
	&log("\n\n" . $elapsed_time_string .  "\n");

}#endsub final_report
#######################################################################################################################

######################################################################################
sub splitdirname {             #splits dir/filename to 2 strings
    my $name = $_[0];          my $dir  = $_[0];
    $name =~ s/^.*[\/\\]//g;   $dir =~ s/[\/\\][^\/\\]*$//;
    return($dir,$name);
	#print "Splitdirname($name)=$dir,$name\n";
}#endsub splitdirname
######################################################################################
###########################################################################################
sub invalid_date_err1 {
	my $datevalue	= $_[0];
	my $list		= $_[1];
	my $linenum		= $_[2];
	my $line		= $_[3];
	my $s = "";
	$s = <<__EOF__;
\n\nFATAL ERROR: Invalid date of \"$datevalue\" used in attribute file.
\tfile: $list
\tLine number $linenum:
\tline: "$line"
Date must be in YYYYMMDD format:

\tEX: :DATE 20011231
\tbut not: :DATE 20013112
\t
\tThe exception is:
\t\t:DATE NOW
\t...which flags the date as being today.
\t(This can be [mis-]used as another way to mark your favorites.)

__EOF__
&death($s);
}#endsub invalid_date_err1
###########################################################################################


######################################################################################
sub isValidExtension {
    #ASSUMES @EXTENSIONS=(list of extensions);
    my $retval=0;

    #if ($DEBUG_FILEFIND) { print "\nDEBUG: *** Extensions are: @EXTENSIONS"; }

    foreach my $t (@EXTENSIONS) {
        #if ($DEBUG_FILEFIND) { print "\nDEBUG: * Checking extension $t"; }
        if ($_[0] =~ /\.$t$/i) { $retval=1; }
    }

    #if ($DEBUG_FILEFIND) { print "\nDEBUG: Extension validity is $retval for file: $_[0]"; }

    return $retval;
}
######################################################################################

######################################################################################
sub linkage {
    #NOT YET SUPPORTED
    return &filefind(@_[0],$_[1]);
}#endsub linkage
######################################################################################

######################################################################################
sub printfilelist { my @f=@_; my $i=1; foreach (@f) { print $i++.":$_\n"; } }
######################################################################################

######################################################################################
sub filefind {
	local $dir2lookin = $_[0];
	local $lookingFor = $_[1];
	local $param      = $_[2];
	local @filelist=();
	local $name="";
	local $lookingForTemp="";
	local $FOUND=0;
	local $valid_extension=0;
	local @regexes=();

	### SIDE-EFFECTS!!! This uses &find which automatically calls &wanted. ###

	#if ($DEBUG_FILEFIND) { print "\nDEBUG: &FILEFIND($_[0],$_[1],$_[2])\nLOOKIN' FOR: \"$lookingFor\"\n\tIN: \"$dir2lookin\""; }

	#OLD:&find($dir2lookin);
	#NEW:&find(wanted=>\&wanted,$dir2lookin);
	#NEWER:
	     &find({wanted=>\&wanted, no_chdir   =>1},$dir2lookin);
	#    &find({wanted=>\&wanted, follow_fast=>1},$dir2lookin);	#TODO try follow_fast instead of chdir:

    #if ($DEBUG_FILEFIND) { print "\nNUMFOUND/ENCOUNTERED: ".@filelist."/$numEncountered/$numEncounteredDirs"; }

    return(@filelist);
}#endsub filefind
######################################################################################
####################################################################################################################################
sub wanted {
	$name = $File::Find::name;
	$name2 = &osslash($name);												#DEBUG: print "Wanted called...name=$name...File::Find::name=$File::Find::name...$_[0]\n";

	if (!-d $name) { $numEncountered++; } else { $numEncounteredDirs++; }
	if (($param->{dots} && (($numEncountered % 500)==0))) { &log("."); }	#$name =~ s/\\/\//g;         #make sure all fwd slashes

	if (&isValidExtension($name2)) { 
		$ALLFILES{$name2}="2"; 
		$valid_extension = 1;
	} else {
		$ALLFILES{$name2}="1";
		$valid_extension = 0;
	}																		#DEBUG: print "\nAllfiles{$name2}=1 now.";
																			#if ($DEBUG_QFF > 5) { if ($name =~ /\.lst/i) { print "[X2X]: ALLFILES{$name2} now = 1\n"; } }
	if (($param->{extensionsonly}) && ($valid_extension==0)) {				#DEBUG: print "\nReturning YU82...".&isValidExtension($name)."...name=$name...";#
		return 0; 
	}#endif

	##### Check to see if the filename has what we are looking for in it:
    $FOUND=0;																#DEBUG: print "\nname=$name, lookingfor=$lookingfor";#
	my @regexes=split(/\|/,"$lookingFor");		
	foreach $lookingForTemp (@regexes) {		
		if ($name =~ /$lookingForTemp/i) { $FOUND=1; }						
		else {
			($tmpdir,$tmpname)=&splitdirname($name);
			if ($tmpname =~ /$lookingForTemp/i) { $FOUND=1; }				#Allows "^" to match beginning of filename instead of whole path
		}
	}

	if ($FOUND) {															#Already did NOT do above, but has seemed to be okay for years: $name =~ s/\\/\//g;    #backslash. make sure all fwd slashes
		push(@filelist,$name2);
	}#endif
}#endsub wanted
####################################################################################################################################




#######################################################################
sub usage {
my $o = $0;
$o =~ s/^.*[\/\\]//g;
my $a = <<__EOF__;
Generate Filelists By Attribute, by Claire Sawyer.

USAGE:
  $o -g -i"c:\\path to ini file\\whatever.ini"
        normal execution using INI file - may take several minutes
        (omit -i to use default values -- deprecated/not recommended)
  $o -q[1234] (stacking allowed, ie -q123 is good) (-i is still required)
        quick execution using INI file
                1=skip filesearch             2=skip id3v1 genre retrieval
                3=skip date stuff             4=skip base attribute list (WHY?)
  $o -r[123] (stacking allowed, ie -r23)
        create index files (in $METAFILELIST_DIR)
            1=file/attrib index only   2=genre index only   3=date index only
            * best done one at a time, in order
  $o -n -- create new attrib list (will not overwrite)

  *** Obscure options:
  $o -c filelist regexlist AttributeName >runonce.bat
        Static filelist to attribute filelist conversion.
        For more help: $o -c with no options.
  $o -t <filelist >newfilelist
        convert full directory filelist into nodir/noextension list
__EOF__
print "\n$a";
exit;
}#endsub usage
#######################################################################
#######################################################################
sub newattributelist {
	&gettimeinfo;
	my $FILE="attrib.lst";
	
	#### If the attribute file already exists, do-nothing:
	if (-e $FILE) { &log("\n\nWARNING: Attribute file $FILE already exists.  Doing nothing.\n"); exit; }
	
	#### AT THIS POINT, we are generating a new attribute file
	
	$yyyymmdd=$NOWYYYYMMDD;
	my $FROMLINE="";
	if ($ENV{"FROM"} ne "") { $FROMLINE=":from " . $ENV{FROM}; }
	
	#### Start writing the new attribute file:
	open(FILE,">$FILE") || &death("couldn't open $FILE\n");
	binmode FILE, ":encoding(UTF-8)";
	print FILE <<__EOF__;
:DATE $yyyymmdd
$FROMLINE

# attribute list generated by makeattrib.bat
#
# FORMAT:  RegEx[|RegEx]:Attribute1,Attribute2,etc (attributes definitely can't have these characters:\\\/:,)
#   EXAMPLE: :acoustic        (flags all files in dir tree as acoustic - value 1)
#   EXAMPLE: :+acoustic       (flags all files in dir tree as acoustic STRONGLY - value 2) (cannot be unset)
#   EXAMPLE: :-acoustic       (flags all files in dir tree as NOT acoustic - value 0)
#   EXAMPLE: :--acoustic      (flags all files in dir tree as NOT acoustic STRONGLY - value -1) (cannot be unset)
#   EXAMPLE: 0[1-5]_:acoustic (flags first 5 files as acoustic, assuming they are prefixed with 01_,02_,03_,04_, or 05_)
# * You can also put more than one RegEx on the right side of the colon:
#   EXAMPLE:fred|barny:flintstones (flags all files with 'fred' OR 'barny' in name as flintstones)
# CAUTION: You must backslash special characters, including: ^().+[]?\\/\$        (you shouldn't really need \/ anyway unless you are referring to items in other directories -- future expansion may support this)
#   EXAMPLE: \\(remix\\):remixes   (sets all files with "(remix)" in title as remixes)
# REGULAR EXPRESSIONS: .=any char, *=0 or more of last char, ?=0 or 1 of last char, +=1 or more of last char, ^=beg of filename or dirname, $=end of filename, []=set of chars (EX:[aeiou]=one vowel or [0-9]=any digit)
# SPECIAL TAGS: DATE to set date for use with date range filelists (file date is used by default)
#   EXAMPLE: :DATE 19991231          makes it dated 12/31/1999 (can use YYYY, YYYYMM, YYYYMMDD, or YYYYMMDDHH)

#   EXAMPLE: :DATE NOW               makes it dated "today" -- forever

__EOF__

	##### Add a set of comments that lists the filenames, just to make life easier
	my @tmpfiles=();
	my $file4print="";
	push(@tmpfiles,&filefind(".",".",{extensionsonly=>1,dots=>0}));
	foreach my $file (@tmpfiles) {
	    $file4print =  $file;
	    $file4print =~ s/^\.//g;
	    $file4print =~ s/^.*[\\\/]//g;
	    print FILE "# $file4print\n";
	}
	
	close(FILE);
	exit;
}#endsub newattributelist
#######################################################################


#################################################################################################################################
sub decrement_date_by_one_day {    #USAGE: ($newyyyymmdd)=&decrement_date_by_one_day($yymmdd);
	#USES last_day_of_month;
	my $date = $_[0];
	my $MONTH_DECREMENTED=0;
	my ($year,$month,$day,$retval)=("","","","");
	
	### FIRST let us parse out our input date:
	$date =~ /(....)(..)(..)/;
	$year  = $1; $month = $2; $day   = $3;
	
	### Decrement day. If day is less than 1, it's really the previous month.
	### If month ends up less than 1, it's really december of the last year.
	### Also, if month decrements, we must set day to last day of month...
	$day--;                         #decrement day
	if ($day  <1) { $month--; $MONTH_DECREMENTED=1; }
	if ($month<1) { $year--; $month=12; }
	if ($MONTH_DECREMENTED) { $day=&last_day_of_month($month,$year); }
	
	$retval=sprintf("%04u%02u%02u",$year,$month,$day);    #Format return value
	return($retval);
}#endsub decrement_date_by_one_day
#################################################################################################################################


#########################################################################################################################
sub last_day_of_month {         #USAGE: ($day)=&last_day_of_month(2,1998);
my ($month)=$_[0];
my ($year) =$_[1];
my ($day)  ="";

#### months with 31 days:
if (($month==1) || ($month== 3) || ($month== 5) || ($month==7)
 || ($month==8) || ($month==10) || ($month==12)) {
        $day=31;
#### months with 30 days:
} elsif (($month==4) || ($month==6) || ($month==9) || ($month==11)) {
        $day=30;
### february is special:
} elsif ($month==2) {
        ## If it's divisible by 4 it's a leapyear...
        if (($year % 4)==0) {
                my $leap=1;
                ## UNLESS divisible by 100
                if (($year % 100)==0) {
                    $leap=0;
                    ## But if it's divisible by 400 it still is,
                    ## Unless it's divisible by 10000...
                    if ((($year % 400)==0) && (($year % 10000)!=0)) {
                        $leap=1;
                    }
                }
                if ($leap) { $day=29; } else { $day=28; }
        } else {
                $day=28;
        }#endif
} else {

        $temp  = "\n\n******* INTERNAL ERROR MONTH_1: month=$month,year=$year *******\n";
        $temp .= "        (THIS SHOULD NEVER HAPPEN)\n\n";
        print $temp;
}#endif

#print "<h1>Last day of month \"$month\" in year \"$year\" is \"$day\"</h1>\n\n";       #

return($day);
}#endsub last_day_of_month
#########################################################################################################################



###########################################################################
sub gather_id3_genres_artists_albums_songs {
    if ($NO_GENRE_PROCESSING_WHATSOEVER) { &log("\n*** NOT Retrieving id3 genre tags.\n"); return; }  #TODO this will cause skipping of artists/bands/songs too
    &log                                           ("\n*** Retrieving id3 genre/artist/album/song tags from $num_files_to_check files.");
    my ($mp3_file1,$mp3_file2,$genrev1,$genrev2,$bestgenre,$artist,$album,$song);
    my $factor = 500;												#hard-coding this isn't as elegant, let's instead calcluate a value:
    $factor = int ($num_files_to_check / 200);						#how many dots to display, set to 100 and each dot is 1% progress
    if ($factor == 0) { $factor=1; }

    foreach my $tmpfile (@files) {
		#print "[PTFG] tmpfile=$tmpfile\n";							#2024/06/02 - had to uncomment this for a weird encoding issue in a Sloppy Jane album [Willow]. Fixed by re-saving metadata of each song in VLCplayer. Made me realize parts of this need a try/catch so that the name is outputted if there is an error, but not otherwise. No need to actually implement that unless this comes up again, though.
        if (($numEncountered++ % $factor)==0) { &log("."); }
        if ($tmpfile !~ /\.mp3$/i) { next; }                        #id3 tags are only for mp3 files! #TODO FLac support would go here
        ($genrev1,$genrev2,$artist,$album,$song) = &get_genre_artist_album_song_for_one_mp3($tmpfile);

		## TODO GOAT MAY NEED TO CHECK IF THESE VALUES EXIST, AND IF THEY DON'T, INITIALIZE TO ZERO
        $ARTIST{$artist}->{$tmpfile}++;
        $ALBUM{$album}->{$tmpfile}++;
        $SONG{$song}->{$tmpfile}++;

        $bestgenre=$genrev2;
        if   (($genrev1 eq "") && ($genrev2 eq "")) { $bestgenre=$genrev1=$genrev2="NEEDS-ID3-TAGGING"  ; }
        elsif ($genrev1 eq "")                      {                     $genrev1="NEEDS-ID3v1-TAGGING"; }
        elsif ($genrev2 eq "")                      { $bestgenre=$genrev1;$genrev2="NEEDS-ID3v2-TAGGING"; }

        ## We make our genres attributable 3 different ways...
        ## id3v1-<id3v1genre>, id3v2-<id3v2genre>, and id3-<genre>.
        ## The 3rd one is the "best" of the two. For example, id3-Metal
        ## flags more files than id3v1-Metal or id3v2-Metal because it
        ## includes files that are only tagged as Metal via v1 or v2 only.

        foreach my $key ("id3-".$bestgenre, "id3v1-".$genrev1, "id3v2-".$genrev2) {
            #DEBUG:
            #print "\n   Setting \%{\$GENRE{$key}}->{$key}=1;";
            #print "\n   Setting \%{\$ATTRIBUTES{\"genre-".$key."\"}}->{$key}=1;\n";
            #%{$GENRE{$key}}->{$tmpfile}=1;
               $GENRE{$key} ->{$tmpfile}=1;
            if ($DEBUG_GENRE_2015) {
				&logonly("\n\%{\$ATTRIBUTES{\"genre-\"." . $key . "}}->{" . $tmpfile . "}=1;" .
				         "\n\%{\$ATTRIBUTES{         "    .$key . "}}->{" . $tmpfile . "}=1;");
            }
           #%{$ATTRIBUTES{"genre-".$key}}->{$tmpfile}=1;    #don't mess with this! (just changed $_ to $tmpfile)		#NOTE this may not work without actually passing %ATTRIB via $aref in the ways shown in other functions here - this was never fully devleoped; just an idea. this line of code probably wont do anything currently.	#20081123 changed GENRE to lowercase since capitals in hash tables have been proved to be trouble and are now a violation of what the documentation says
              $ATTRIBUTES{"genre-".$key} ->{$tmpfile}=1;    #don't mess with this! (just changed $_ to $tmpfile)		#NOTE this may not work without actually passing %ATTRIB via $aref in the ways shown in other functions here - this was never fully devleoped; just an idea. this line of code probably wont do anything currently.	#20081123 changed GENRE to lowercase since capitals in hash tables have been proved to be trouble and are now a violation of what the documentation says
           #%{$ATTRIBUTES{         $key}}->{$tmpfile}=1;    #alias without "genre-" at beginning
              $ATTRIBUTES{         $key} ->{$tmpfile}=1;    #alias without "genre-" at beginning
        }
    }#endforeach
}#endsub gather_id3_genres_artists_albums_songs
###########################################################################


#################################################################################################################################################################
sub get_genre_artist_album_song_for_one_mp3 {
    if ($NO_GENRE_PROCESSING_WHATSOEVER) { return; }
    my $filename = $_[0];

    my $tag;    #pointer
    my ($genrev1,$genrev2)=("","");
    my $id3v2;
    my ($tmpsong, $tmptrack, $tmpartist, $tmpalbum, $tmpcomment, $tmpyear, $tmpgenre)=("","","","","","","");

	#$tag="";                                                   #20230511 patch for increasingly common failures
	eval {														#20230511 patch for increasingly common failures
	    $tag = MP3::Tag->new($filename); 
	};															#20230511 patch for increasingly common failures
	if ($@) {													#20230511 patch for increasingly common failures
		print "\nException: $@ ";								#20230511 patch for increasingly common failures
		#print "\n   ...Setting \$tag to empty"; $tag="";		#20230511 patch for increasingly common failures
	}															#20230511 patch for increasingly common failures

    if (($tag eq "") || (!defined($tag))) {	
		#I don't want to see this error message for mp3s in READY-TO-DELETE folders [20140920] or _PROCESSING/NEW folders [20150809]
		if (($filename !~ /READY-TO-DELETE/i) && ($filename !~ /_PROCESSING/i) && ($filename !~ /[\\\/]NEW[\\\/]/i))
		{									
			&log("\nWARNING: No tag in mp3: $filename");
			return;
		}
    }
	if (defined $tag && length $tag > 0) {		#20140921
	    $tag->get_tags();						#olllllld
	}											#20140921

	### grab genre
    if ($tag->{ID3v2} ne "") {
		$id3v2 = $tag->{ID3v2};
		$genrev2 = $id3v2->get_frame("TCON");  #no clue what TCON is
    }
    if ($tag->{ID3v1} ne "") { 
		$genrev1 = $tag->{ID3v1}->genre; 
	}

	## grab artist / album / song info (everything else is kinda ignored)
    if (($tag->{ID3v2} ne "") || ($tag->{ID3v1} ne "")) { 
		($tmpsong, $tmptrack, $tmpartist, $tmpalbum, $tmpcomment, $tmpyear, $tmpgenre) = $tag->autoinfo();
		#&log("==> GOAT DEBUG ID3 BANDSONGARTIST READ: $tmpsong, $tmptrack, $tmpartist, $tmpalbum, $tmpcomment, $tmpyear, $tmpgenre) = \$tag->autoinfo()\n\t\tfrom $filename;\n");
	}
    return(lc($genrev1),lc($genrev2),ucfirst($tmpartist),ucfirst($tmpalbum),ucfirst($tmpsong));		#keep everything lowercase
}
#################################################################################################################################################################

######################################################################################################################################################
sub create_metaattribute_filelists {   #generate_metaattribute_filelists
    #ASSUMES $META_ATTRIBUTE_FILE should exist;
#    my $aref = $_[0];
#   my %ATTRIB = %$aref;			#DECIDED TO JUST USE %ATTRIBUTES AS A LOCAL INSTEAD ... 20081123
    my $tmpfilename="";
    my $tmpfile2="";
    my $metaattrib="";
    my $oldmode="";
    $nummeta=0; #do NOT my
    my %ATTRIBFILEHASH=();
    my $mode="";
    my $curVal = "";
    my $curValMeta = "";
    my %meta_attribs_generated=();
    my @attribs_now_processing=();
    my $attrib_now_processing=();

	&dump_attribute_weights("create_METAattribute_flielists");


    $meta_attribs_generated{"everything"}=1;
    if ($META_ATTRIBUTE_FILE eq "") {
        &log("WARNING: You have not defined a \$META_ATTRIBUTE_FILE in your INI file or at the top of the $0 source code.\n");
        &log("         This is okay, in theory, but you are missing out on some powerful filelist building abilities!\n\n");
    } elsif (!-e $META_ATTRIBUTE_FILE) { &death("Could not open [3] meta-attribute file $META_ATTRIBUTE_FILE!\nPlease edit the source of $0 to point to a meta-attribute file that actually exists!\n"); }
    &log("\n\n*** Processing meta-attribute file $META_ATTRIBUTE_FILE...");
    open (META,"$META_ATTRIBUTE_FILE") || &death("Could not open [4] meta-attribute file $META_ATTRIBUTE_FILE!!\n");
			binmode META, ":encoding(UTF-8)";
    my $linenum=0;
    while ($line=<META>) {																						#go through each line of the attrib.lst
        chomp $line; $linenum++; next if $line =~ /^#/;															#skip comments; keep track of line number
        next if $line !~ /.:./;																					#need a : with something bef and after..at least



		## NEW MMDD-META CODE INSERTED 20121004 - BEGIN
		if ($line =~ /^MMDD=(..)(..)\-(..)(..)/) {			#MMDD=1001-1031:current holidays:halloween
			($tmpBeginMM,$tmpBeginDD,$tmpEndMM,$tmpEndDD)=($1,$2,$3,$4);								## Split off our values for processing
			if ($DEBUGMMDD) { &log("\n\n* line = $line\n* \$tmpBeginMM,\$tmpBeginDD,\$tmpEndMM,\$tmpEndDD=$tmpBeginMM,$tmpBeginDD,$tmpEndMM,$tmpEndDD\n* NOWMM/DD=$NOWMM,$NOWDD\n"); }
			## Validate the input:
			if (!(($tmpBeginMM >= 01) && ($tmpBeginMM <= 12))) { &death("\n\nFATAL ERROR: tmpBeginMM of $tmpBeginMM is not a valid month number!\nLine = $line\n");	}
			if (!(($tmpBeginDD >= 01) && ($tmpBeginDD <= 31))) { &death("\n\nFATAL ERROR: tmpBeginDD of $tmpBeginDD is not a valid   day number!\nLine = $line\n");	}
			if (!(($tmpEndMM   >= 01) && ($tmpEndMM   <= 12))) { &death("\n\nFATAL ERROR:   tmpEndMM of $tmpEndMM   is not a valid month number!\nLine = $line\n");	}
			if (!(($tmpEndDD   >= 01) && ($tmpEndDD   <= 31))) { &death("\n\nFATAL ERROR:   tmpEndDD of $tmpEndDD   is not a valid   day number!\nLine = $line\n");	}
			$tmpBeginMMDD = $tmpBeginMM . $tmpBeginDD;
			  $tmpEndMMDD =   $tmpEndMM .   $tmpEndDD;
			if ($DEBUGMMDD) { &log("* checking if (\$NOWMMDD($NOWMMDD) >= \$tmpBeginMMDD($tmpBeginMMDD)) && (\$NOWMMDD($NOWMMDD) <= \$tmpEndMMDD($tmpEndMMDD)))\n"); }
			if (($NOWMMDD >= $tmpBeginMMDD) && ($NOWMMDD <= $tmpEndMMDD)) {	#if we have a match that is in today's month/day range
				$line =~ s/^MMDD=(..)(..)\-(..)(..)://i;					#strip off the line and process it like we normall do
			} else { 
				if ($DEBUGMMDD) { &log("* skipping line: $line\n\n"); }
				next;														#otherwise, the date says not to process this line, so go to the next one
			}												
			if ($DEBUGMMDD) { &log("* line is now = $line\n\n"); }
		}
		## NEW MMDD-META CODE INSERTED 20121004 - END



        if ($DEBUG_META>=6) { &log("\n\n\n[META10]\tProcessing line number $linenum".": ".$line); }
        if ($line =~ /::/) { ($metaattrib,$attriblist)=split(/::/,"$line"); }
        else               { ($metaattrib,$attriblist)=split(/:/, "$line"); }

        ##### Add this attribute to our attribute lists to keep track of what attributes exist:
		$metaattrib =~ tr/[A-Z]/[a-z]/;
        if ($metaattrib eq "") { $metaattrib="unknown"; }
        $meta_attribs_generated{$metaattrib}=1;																		if ($DEBUG_META>10) { 	&log("\n========> Setting \$meta_attribs_generated{$metaattrib} to 1..."); }
		#20081123 - wait - this seems like a major major MAJOR bug! doesn't this destroy existing hash tables? FAIL!        $ATTRIBUTES{"$metaattrib"}=1;								#
	
		##### Abandoned security stuff:
        $ATTRIBUTES_BY_ACCESS{"$metaattrib"}=SECURITY_LEVEL_HIGHEST;

		##### Split out [something] and go through it:
        $attriblist =~ tr/[A-Z]/[a-z]/;			
	    my @attribs = split(/,/,"$attriblist");																		
		if ($DEBUG_META) { &log("\n[META20]\tmetaattrib=$metaattrib,tmpattrib=\"$tmpattrib\",\"attriblist\" is \"$attriblist\""); }
		my $newtmpattrib; my $tmpWeight;
		foreach my $tmpattrib (@attribs) {													#go through the list of attributes used to generate this meta-attribute
	        if ($DEBUG_META>=6) { &log("\n[META30]\ttmpattrib=$tmpattrib"); }
            $oldmode=$mode;


			##### DETERMINE WEIGHT OF [META]ATTRIBUTE:
			$newtmpattrib=$tmpattrib;
			if (($tmpattrib =~ /\*/) && ($tmpattrib !~ /caption-/i) && ($tmpattrib !~ /postcaption-/i) && ($tmpattrib !~ /^thing-/i) && ($tmpattrib !~ /^person-/i) && ($tmpattrib !~ /^activity-/i) && ($tmpattrib !~ /^place-/i)) {
				($newtmpattrib,$tmpWeight)=split(/\*/,$tmpattrib); if ($DEBUG_ATTRIBUTE_WEIGHTS) { &log("[[[tmpweight=$tmpWeight]]]"); }
				if (($tmpWeight !~ /^\d*\.?\d*$/) || ($tmpWeight eq "") || ($tmpWeight eq ".")) {  #validate weight
					&log("\n\nERROR W1: WEIGHT of \"$tmpWeight\" is not valid [tmpattrib=$tmpattrib,newtmpattrib=$newtmpattrib,tmpWeight=$tmpWeight]!\n\t LINE=$line"); 
					$newtmpattrib = $tmpattrib; $tmpWeight=1;
				}	
			} else {
				$newtmpattrib = $tmpattrib;
				$tmpWeight=1;	#default weight
			}
			$tmpattrib=$newtmpattrib;

			##### STORE WEIGHT OF ATTRIBUTE, UNLESS NON-1 ATTRIBUTE ALREADY EXISTS: (2017)
			#my %ATTRIBUTE_WEIGHTS=();		#key={$filename$delimiter$attribute},value=weight
			if (($DEBUG_META_ATTRIBUTE_WEIGHTS) && ($tmpWeight != 1)) { &log("\n\n--------[Processing newMETAattrib=$newtmpattrib,tmpWeight=$tmpWeight]"); }
			#f (($tmpWeight==1) && ($ATTRIBUTE_WEIGHTS{       "$tmpfile$DELIMITER$newtmpattrib"} != 1))    #non-meta version
			if (($tmpWeight==1) && ($ATTRIBUTE_WEIGHTS{"META$metaattrib$DELIMITER$newtmpattrib"} != 1)) {  #    meta version
				#don't store the new weight if it's "boring ol' 1", which only ever happens automatically, and should not overwrite a manually set weights	
			} else {
				$ATTRIBUTE_WEIGHTS{"META$metaattrib$DELIMITER$newtmpattrib"}=$tmpWeight;
			}
			if (($DEBUG_META_ATTRIBUTE_WEIGHTS) && ($tmpWeight != 1)) { &log(  "\n         *~*~* [MW]\$ATTRIBUTE_WEIGHTS{META$metaattrib$DELIMITER$newtmpattrib}=\$tmpWeight=".$ATTRIBUTE_WEIGHTS{"META$metaattrib$DELIMITER$newtmpattrib"}.";\n"); }


            if    ($tmpattrib =~ /^\-[^\-]/) { $mode="remove"   ; }
            elsif ($tmpattrib =~ /^\+[^\+]/) { $mode="add"      ; }
            elsif ($tmpattrib =~ /^\+\+/)    { $mode="forceadd" ; }
            elsif ($tmpattrib =~ /^\-\-/)    { $mode="blacklist"; }
            else                             { $mode="add"      ; }
            $tmpattrib =~ s/^[\+\-]*//g;													### remove any leading + or - to get real attrib name and value
			$tmpattrib =~ s/\t/ /g;					$tmpattrib =~ s/:/- /g;					### remove characters that would be invalid filenames
			$tmpattrib =~ s/[\\\/]/ - /g;			$tmpattrib =~ s/\*/x/g;					### remove characters that would be invalid filenames
	        if ($DEBUG_META>=6) { &log("\n[META35]\ttmpattrib=$tmpattrib"); }
            if ($oldmode ne $mode) { $oldmode=$mode; }
            ### now we know this attrib's name (without any leading +/-), we figureout which files belong to it.... First, gather a list of attributes:
            if ($tmpattrib =~ /\*/) {
                $tmpregex = $tmpattrib;
                $tmpregex =~ s/[^\.]\*/.*/g;								                #DEBUG:print "\nMeta RegEx Searching all attributes for \"$tmpregex\"...";#OHOH
                @attribs_now_processing=();
                foreach $tmpattr (%ATTRIBUTES) {											#DEBUG:print "\n\t\t- does $tmpattr contain /$tmpregex/ ???";#OH some of these values its checking are hash tables - freaks me out because I don't evne remember why
					if ($tmpattr =~ /$tmpregex/i) {											#DEBUG:print "\n\tMeta RegEx: pushing $tmpattr into attribs_now_proccesing becasue it has /$tmpregex/ in it . . . ";#OHOH
						push(@attribs_now_processing,$tmpattr);			
						if ($DEBUG_GENRE_2015) { &log("   {{pushing onto \@attribs_now_processing: $tmpattr}}"); };
					}
				}
            } else { @attribs_now_processing = ($tmpattrib); }
            #typically @attribs_now_processing only holds 1 attribute, unless we are using a meta attribute with "*" in it, which is quite rare ... :)
	        if ($DEBUG_META>=6) { &log("\n[META50]\t\@attribs_now_processing is \"@attribs_now_processing\""); }
			#DEBUG:print "\n\RE-TESTING (range-F - last 6 months #2):\n***** \"" . &hashdump(\%{$ATTRIBUTES{"range-F - last 6 months"}}) . "\" *****";	## . &tostr(keys(%{$ATTRIBUTES{"range-F - last 6 months"}}))	#
			#DEBUG:print "\n\RE-TESTING (range-f - last 6 months #2):\n***** \"" . &hashdump(\%{$ATTRIBUTES{"range-f - last 6 months"}}) . "\" *****";	## . &tostr(keys(%{$ATTRIBUTES{"range-F - last 6 months"}}))	#

			### now that we have a list of attributes that create this meta attribute (@attribtes_now_processing), 
			### traverse through each attribute to gather its files:
            foreach $attrib_now_processing (@attribs_now_processing) {
				my $tmpmetaattrib=$attrib_now_processing;									#alias for compatibility with code pasted from the sister/non-meta function this newer function is based on.. just makes life easier!
	            ## now we know attribute's name ($attrib_now_processing), 
				## traverse through all files, assign value depending on whether we are adding/removing:
	            if ($DEBUG_META>=6) { &log("\n[META60]\tNow processing (meta=$metaattrib) attrib \"$attrib_now_processing\",mode=$mode.\n[META] * hashdump attrib{$attrib_now_processing}=" . &hashdump(\%{$ATTRIBUTES{$attrib_now_processing}})); }
	            $curVal=""; $curValMeta="";
	            foreach $tmpfile (keys %{$ATTRIBUTES{$attrib_now_processing}}) {			#traverse all filenames for the attribute we are now processing
	                    ### Get current value/meta value of this filename:
	                   #$curVal     = %{$ATTRIBUTES{"$attrib_now_processing"}}->{"$tmpfile"};
	                    $curVal     =   $ATTRIBUTES{"$attrib_now_processing"} ->{"$tmpfile"};
	                   #$curValMeta = %{$ATTRIBUTES{"$metaattrib"}}->{"$tmpfile"};	
	                    $curValMeta =   $ATTRIBUTES{"$metaattrib"} ->{"$tmpfile"};	
	                    ## DEBUG
	                    #if ($curVal     eq "") { &log("\nWARNING: curval     of $tmpfile for attrib $attrib_now_processing is an empty string!"); }
	                    #if ($curValMeta eq "") { &log("\nWARNING: curvalmeta of $tmpfile for attrib $metaattrib is an empty string!"); $curValMeta=0; }
	                    if (($DEBUG_META>=7)||($tmpfile =~ /$DEBUG_FILEWATCH_FILENAME/i)||($attrib_now_processing =~ /$DEBUG_ATTRIBWATCH_ATTRIBNAME$/i)){
	                        if ((($DEBUG_ATTRIBWATCH_ATTRIBNAME ne "") && ($attrib_now_processing =~ /^$DEBUG_ATTRIBWATCH_ATTRIBNAME$/i))|| ($DEBUG_META>=10)) {
								&log("\n* Line:                 $line");
#								&log("\n* Attrib:               $attrib");	#$attrib doesn't exist; oops!
								&log("\n* Attr now processing:  $attrib_now_processing");
								&log("\n* File:                 $tmpfile");
	                           #&log("\n  ^----- * curVal     = ".%{$ATTRIBUTES{$attrib_now_processing}}->{$tmpfile}.", ");
	                            &log("\n  ^----- * curVal     = ".  $ATTRIBUTES{$attrib_now_processing} ->{$tmpfile}.", ");
	                           #&log("\n  ^----- * curValMeta = ".%{$ATTRIBUTES{$metaattrib           }}->{$tmpfile}."");					 #wtf is this line ?!?!?!     ".";			#attr{metaattrib}->{$tmpfile}\n";
	                            &log("\n  ^----- * curValMeta = ".  $ATTRIBUTES{$metaattrib           } ->{$tmpfile}."");					 #wtf is this line ?!?!?!     ".";			#attr{metaattrib}->{$tmpfile}\n";
	                        }
	                    }


						##### 2015 b.s. - why was i trying to stor eit here? It's already stored from when we read it form the meta file! STORE WEIGHT OF ATTRIBUTE, UNLESS NON-1 ATTRIBUTE ALREADY EXISTS:
						#my %ATTRIBUTE_WEIGHTS=();		#key={$filename$delimiter$attribute},value=weight
	                    #if (($mode eq "add") || ($mode eq "forceadd")) {
						#	if (($DEBUG_ATTRIBUTE_WEIGHTS>1) && ($tmpWeight != 1)) { &log("\n\n--------[Processing metaattrib=$metaattrib,tmpWeight=$tmpWeight]"); }
						#	if (($tmpWeight==1) && ($ATTRIBUTE_WEIGHTS{"$tmpfile$DELIMITER$metaattrib"} != 1)) {
						#		#don't store the new weight if it's "boring ol' 1", which only ever happens automatically, and should not overwrite a manually set weights	
						#	} else {
						#		$ATTRIBUTE_WEIGHTS{"$tmpfile$DELIMITER$metaattrib"}=$tmpWeight;
						#	}
						#	if (($DEBUG_ATTRIBUTE_WEIGHTS>1) && ($tmpWeight != 1)) { &log(  "\n         *!~-*-~!* \$ATTRIBUTE_WEIGHTS{$tmpfile$DELIMITER$newtmpattrib}=\$tmpWeight=".$ATTRIBUTE_WEIGHTS{"$tmpfile$DELIMITER$newtmpattrib"}.";\n"); }
						#}

						##### 2017 redo
						######### CHECK WEIGHT ########
						##### GET WEIGHT:
						$tmpWeight = $ATTRIBUTE_WEIGHTS{"META$DELIMITER$tmpmetaattrib"};			
						if ($DEBUG_ATTRIBUTE_WEIGHTS) { &log("\n\t[MW3][$tmpmetaattrib][\$tmpWeight = \$ATTRIBUTE_WEIGHTS{\"META$DELIMITER$tmpmetaattrib\"}; = " . $ATTRIBUTE_WEIGHTS{"META$DELIMITER$tmpmetaattrib"} . "]"); }
						if ($tmpWeight eq "") { $tmpWeight=1; }											
						if ($DEBUG_ATTRIBUTE_WEIGHTS) { &log("\n\t[MW3][$tmpmetaattrib][\$tmpWeight=$tmpWeight now]"); }


	                    ### We add it, as long as it hasn't been forcefully
	                    ### removed from the attribute already (-1):
	                    if ($mode eq "add") {
	                        #basically, if the current *attribute* for this file is true set to 1), then we know this rule is applying to that
	                        #attribute and that we probably need to add it to the meta attribute we are processing ($metaattrib) ... We cannot 
							# do this if the meta-attribute for the file is already -1 becuase it has already been blacklisted in that case.
	                        #if (($DEBUG_META>=11)||(($tmpfile =~ /$DEBUG_FILEWATCH_FILENAME/i))) 
	                        if ($DEBUG_META>=11) { print "\nExtra debug: if ((curVal=$curVal >= 1) && (curValMeta=$curValMeta > -1)) {let's add it}"; }
	                        if (($curVal >= 1) && ($curValMeta > -1)) {											 	                            if ($DEBUG_META>=7) { if (($DEBUG_ATTRIBWATCH_ATTRIBNAME ne "") && ($DEBUG_ATTRIBWATCH_ATTRIBNAME eq $metaattrib)||($attrib_now_processing =~ /^$DEBUG_ATTRIBWATCH_ATTRIBNAME$/i)) {	                                    print "\nAdd MetaA=$metaattrib (tmp=$attrib_now_processing,mode=$mode,curval($attrib_now_processing)=$curVal,curvalmeta($metaattrib)=$curValMeta): [1Z] $tmpfile...\n"; print "\tBased on[A] line:\n\t$line\n\n"; } }
								if (($DEBUG_META>=10)||($tmpfile =~ /$DEBUG_FILEWATCH_FILENAME/i)) { print "\n[[[[[ \%{\$ATTRIBUTES{\"".$metaattrib."\"}}->{\"".$tmpfile."\"}=1 ]]]]]"; }
	                           #%{$ATTRIBUTES{"$metaattrib"}}->{"$tmpfile"}=1;										                            #if (($DEBUG_META>=7)||(($tmpfile =~ /$DEBUG_FILEWATCH_FILENAME/i)))
	                              $ATTRIBUTES{"$metaattrib"} ->{"$tmpfile"}=1;										                            #if (($DEBUG_META>=7)||(($tmpfile =~ /$DEBUG_FILEWATCH_FILENAME/i)))
	                        }
	                    } elsif ($mode eq "forceadd") {  #aka "whitelist"
	                        #one thing we don't do is forceadd something that has been previously blacklisted from the attribute we are currently generating ($metaattrib). 
							#For EX, fred::--A,++B will whitelist everyth1ng in B to metaattribute 'fred', but that list will not include anything previously blacklisted in 'A'.  
							#To committ this whitelist to memory, we must set the meat-attribute for the file to the value of 2.  We cannot do this if the meta-attribute for the 
							#file is already -1 becuase it has already been blacklisted in that case.
	                        if (($curVal >= 1) && ($curValMeta > -1)) {												                            if (($DEBUG_META>=7)||(($tmpfile=~/$DEBUG_FILEWATCH_FILENAME/i))){ print "\nWhitelist M=$metaattrib (tmp=$attrib_now_processing,mode=$mode,curval=$curVal,curvalmeta=$curValMeta): [2d] $tmpfile...[X]\n\tBased on[B] "; print "attrib_now_processing=$attrib_now_processing,line:\n\t$line\n"; }
								if (($DEBUG_META>=10)||($tmpfile =~ /$DEBUG_FILEWATCH_FILENAME/i)) { &log("\n[[[[[ \%{\$ATTRIBUTES{\"".$metaattrib."\"}}->{\"".$tmpfile."\"}=2 ]]]]]"); }
	                           #%{$ATTRIBUTES{"$metaattrib"}}->{"$tmpfile"}=2;
	                              $ATTRIBUTES{"$metaattrib"} ->{"$tmpfile"}=2;
	                        }
	                    } elsif ($mode eq "blacklist") {
	                        if (($curVal >= 1) && ($curValMeta < 2)) {		#one thing we don't do is blacklist (-1) something that has been previously whitelisted (2)...
								if (($DEBUG_META>=10)|| ($tmpfile =~ /$DEBUG_FILEWATCH_FILENAME/i)) { print "\n[[[[[ \%{\$ATTRIBUTES{\"".$metaattrib."\"}}->{\"".$tmpfile."\"}=-1 ]]]]]"; }
								if (($DEBUG_META>= 7)||(($tmpfile =~ /$DEBUG_FILEWATCH_FILENAME/i))){ 
									&log("\nBlacklist M=$metaattrib (tmp=$attrib_now_processing,mode=$mode,curval=$curVal,curvalmeta=$curValMeta)[blacklist=-1]:\n\t$tmpfile...[X]\n\tBased on[C] attrib_now_processing=$attrib_now_processing,line:\n\t$line\n"); }
	                           #%{$ATTRIBUTES{"$metaattrib"}}->{"$tmpfile"}=-1;															
	                              $ATTRIBUTES{"$metaattrib"} ->{"$tmpfile"}=-1;															
	                        }
	                    } elsif ($mode eq "remove") {	
	                        if (($curVal >= 1) && ($curValMeta < 2)) {		#We remove it, unless it's been force-added (2) to the attribute already
	                           #%{$ATTRIBUTES{"$metaattrib"}}->{"$tmpfile"}=0;										                            
	                              $ATTRIBUTES{"$metaattrib"} ->{"$tmpfile"}=0;										                            
								if (($DEBUG_META>= 7)||($tmpfile =~ /$DEBUG_FILEWATCH_FILENAME/i)) { print "\nRm M=$metaattrib (tmp=$attrib_now_processing,mode=$mode): [-1] $tmpfile...[X]\n\tBased on[D] attrib=$attrib_now_processing,line:\n\t$line\n"; }
								if (($DEBUG_META>=10)||($tmpfile =~ /$DEBUG_FILEWATCH_FILENAME/i)) { print "\n[[[[[ \%{\$ATTRIBUTES{\"".$metaattrib."\"}}->{\"".$tmpfile."\"}=0 ]]]]]"; }
	                        }
	                    } else {
	                        &death("ERROR: Unknown mode of $mode while processing tmpattrib=$attrib_now_processing,metaattrib=$metaattrib,curval=$curVal,curvalmeta=$curValMeta\n");
	                    }#endif
						#f ($DEBUG_META>10) { &log("\n  After processing  $attrib_now_processing for $tmpfile:"); &log("\n  ^----- * curVal     = ".%{$ATTRIBUTES{$attrib_now_processing}}->{$tmpfile}." [$attrib_now_processing] ");							&log("\n  ^----- * curValMeta = ".%{$ATTRIBUTES{$metaattrib           }}->{$tmpfile}." [$metaattrib]\n"); } #wtf is this line ?!?!?!     ".";#attr{metaattrib}->{$tmpfile}\n";
						if ($DEBUG_META>10) { &log("\n  After processing  $attrib_now_processing for $tmpfile:"); &log("\n  ^----- * curVal     = ".  $ATTRIBUTES{$attrib_now_processing} ->{$tmpfile}." [$attrib_now_processing] ");							&log("\n  ^----- * curValMeta = ".  $ATTRIBUTES{$metaattrib           } ->{$tmpfile}." [$metaattrib]\n"); } #wtf is this line ?!?!?!     ".";#attr{metaattrib}->{$tmpfile}\n";
				}#endforeach   file in the member of the set of files               that we are processing
            }#endforeach  attribute in the member of the set of 
        }#endforeach      attribute in the member of the set of attributes          that we need to process for this line
    }#endwhile
    close(META);
    &log("\n*** Done processing meta-attribute file.");
    ##############################################



	##############################################
    &log("\n*** Writing meta attribute lists...     ");
    my @tmpkeys     = ();
    my $tmpattrname = "";
	my $num_files   =  0;
	my $num_written =  0;
	my $before;
	my $after;
	my $roll;
    foreach my $tmpmetaattrib (sort keys %meta_attribs_generated) {
		if ($DEBUG_GENRE_2015){ &logprint("\n\n\n\n\n-----[tmpmetaattrib=$tmpmetaattrib]-----"); }				
		if ($ATTRIBUTES{"$tmpmetaattrib"} eq "") { next; }					
		print ".";										

		if (($DEBUG_META)||(0)) { &logprint("\n * Writing $tmpmetaattrib filelist!!!"); } 	#DEBUG
		
		## Prepare filename & filecounts:
		$tmpattrname = "$META_PREFIX$tmpmetaattrib";
		$tmpfilename = $METAFILELIST_DIR . "/" . $tmpattrname . "." . $filelistextension;
		$num_files   = 0;
		$num_written = 0;
		
		%ATTRIBFILEHASH = %{$ATTRIBUTES{"$tmpmetaattrib"}};										# pull out the hashtable for this attribute
		@tmpkeys       = sort keys %ATTRIBFILEHASH;													# do the subparts in alphabetical order
		$num_files     = 0;																			# count if it has files or not
		my $filesfound = 0;
		my $timestoprint;
		my $tmpWeight;
		foreach $tmpfile (@tmpkeys) { if ($ATTRIBFILEHASH{"$tmpfile"} >= 1) { $num_files++; } }	# count if it has files or not	
		if (($num_files > 0)) {																				
			#$tmpfilename = &clean_name_for_filenames($tmpfilename);	this was giving us filenames like "--mp3-listrs" maybe need to use that backslash flag to suppress slash conversion but no that would fuck up tags with slahes in them so don't do that
			open (METALIST, ">$tmpfilename") || &death("could not open [50] $tmpfilename!!\nPerhaps your \$METAFILELIST_DIR of $METAFILELIST_DIR does not exist... Look carefully at the filename and make sure the directory exists.\n");			#DEBUG: print METALIST "#[TEST]\n";
			binmode METALIST, ":encoding(UTF-8)";
			foreach $tmpfile (@tmpkeys) {		#EX: go through each song in the current meta-tag									

				if ($tmpfile =~ /$DEBUG_FILEWATCH_FILENAME/i) { &logprint("\n\t[*** [$tmpmetaattrib]\t\$ATTRIBFILEHASH{\"$tmpfile\"}=$ATTRIBFILEHASH{$tmpfile} ***]     "); }
				if (($DEBUG_GENRE_2015)||(($DEBUG_FILEWATCH_META>0)&&(($tmpfile=~/$DEBUG_FILEWATCH_FILENAME/i)))){ &logprint("\n     *** VALUE of M=$tmpmetaattrib is $ATTRIBFILEHASH{$tmpfile} for f=$tmpfile"); }				#if ($DEBUG_META>=5){print "*** Inserting [1S9S3S3] \"$tmpfile\" into meta-category $tmpmetaattrib...\n";}#DEBUG: print "\nTMPFILE=". $ATTRIBFILEHASH{"$tmpfile"}."=$tmpfile";

				if ($ATTRIBFILEHASH{"$tmpfile"} >= 1) {		
					
					######### CHECK WEIGHT ########
					##### GET WEIGHT:
					$tmpWeight = $ATTRIBUTE_WEIGHTS{"$tmpfile$DELIMITER$tmpmetaattrib"};			
					if ($DEBUG_ATTRIBUTE_WEIGHTS) { &log("\n\t[TW2][$tmpmetaattrib][\$tmpWeight = \$ATTRIBUTE_WEIGHTS{\"$tmpfile$DELIMITER$tmpmetaattrib\"}; = " . $ATTRIBUTE_WEIGHTS{"$tmpfile$DELIMITER$tmpmetaattrib"} . "]"); }
					if ($tmpWeight eq "") { $tmpWeight=1; }											
					if ($DEBUG_ATTRIBUTE_WEIGHTS) { &log("\n\t[TW2][$tmpmetaattrib][\$tmpWeight=$tmpWeight now]"); }

					##### MASSAGE FILENAME & KEEP TRACK OF TOTAL FILES:
					$filesfound++;				
					#if ($USE_BACKSLASHES_INSTEAD_OF_SLASHES) { $tmpfile =~ s/\//\\/g; } else { $tmpfile =~ s/\\/\//g; }

					##### IF TMPWEIGHT>1, ACT ON IT, BUT IF IT'S <1, DO NOT ROLL, WE ALREADY ROLLED AND SAVED THAT VALUE:
					$timestoprint=1;										#default value in case we miss cases
					if ($tmpWeight > 1) {
						$timestoprint = $tmpWeight;
						if ($tmpWeight =~ /\./) {			#5.9 would mean timestoprint is 5 + roll against 0.9
							($before,$after)=split(/\./,$tmpWeight);
							$timestoprint=$before; $roll = rand(1); if ($roll <= ".$after") { $timestoprint++; } 
						}
					} 
					elsif ($tmpWeight ==  0) { $timestoprint=0; }		#don't add if weight is 0	
					elsif ($tmpWeight eq "") { $timestoprint=1; }		#no weight assigned, so just go with the default behavior, before we added weighting
					elsif ($tmpWeight <=  1) { $timestoprint=1; }		#we already rolled in this case, and the roll result already determined whether this would be here
					if (($DEBUG_ATTRIBUTE_WEIGHTS) && ($tmpWeight != 1)) { &log("\t[tmpWeight=$tmpWeight,roll=$roll]\n\t[**timestoprint**=$timestoprint for tmpfile=$tmpfile]\n"); }

					##### PRINT TO PLAYLIST CORRECT NUMBER OF TIMES (& KEEP TRACK):
					if ($timestoprint == 0) {
						#FROM NONMETA: %{$ATTRIBUTES{$currentattrib}}->{$tmpfile}=0;				#remove from internal data structure so meta-attributes don't pick this file up as being part of this attribute anymore -- a use case that was making it so removing something from an attribute a certain percentage of the time would remove it from meta-attributes comprised of that attribute 0% of the time. Really, if a file is removed from an attribute based on probability, it also should not appear in a meta-attribute that is comprised of that attribute (unless explicitly added by a side effect of some other unrelated directive, of course)
						#FROM NONMETA: delete %{$ATTRIBUTES{$currentattrib}}->{$tmpfile};			#DEBUG: &logprint("\n----------------------------------------------\%{\$ATTRIBUTES{$currentattrib}}->{".$tmpfile."}=0=(sanity)".%{$ATTRIBUTES{$currentattrib}}->{$tmpfile}.";--------------------------------------");#
						#FOR META: JUST DO NOTHING. DON'T PRINT IT.
					} else {
						for ($i=1; $i<=$timestoprint; $i++) {
							$num_written++; print METALIST $tmpfile . "\n"; if ($DEBUG_ATTRIBUTE_WEIGHTS) { &log("[printing because \$i=$i]"); }
						}#endfor
					}#endif
				}#endif 
				
			}#endforeach
			close(METALIST);
		}#endif
		
        &logprint("\n\t" . sprintf("%5u",$num_files) . "\t" . sprintf("%5u",$num_written) . "\t" . $tmpmetaattrib);

        $nummeta++;
    }#endforeach
    &log("\n*** Done writing $nummeta meta-attribute lists...");
    #######################





    #&log("\n*** Processing inverse meta-attributes...\n");
	#&log("\n*** Processing access levels [meta]...\n");
	 &log("\n*** Processing access levels [meta]...");

    foreach my $tmpmetaattrib (keys %meta_attribs_generated) {
		#### The inverse attributes for this meta attribute, which may have the same name as a previous attribute, must be reset:
		#$INVERSE_ATTRIBUTES{$tmpmetaattrib}=();
        #DEBUG:print "\n * Processing inverse for $tmpmetaattrib ...\n";#
		#print ".";
		
		if ($tmpmetaattrib eq "everything") { next; }		#speedup optimization by removing processing 'everything' . . .

		print "\r" . " " x $MAX_WIDTH . "\r$tmpmetaattrib";

		##### Retrieve files related to this meta-attribute......BUT BEWARE!!  There may be none!!
		if ($tmpmetaattrib ne "") {															
			#&logonly("> $tmpmetaattrib ... \n>> $ATTRIB{$tmpmetaattrib} ...\n");
			if ($ATTRIBUTES{"$tmpmetaattrib"} eq "") { 
				&logonly("\n       WARNING: Meta-attribute with 0 files found: \"$tmpmetaattrib\""); 
				@tmpkeys = ();	#this can happen below too
			} else {
				%ATTRIBFILEHASH = %{$ATTRIBUTES{"$tmpmetaattrib"}};		#OHOH ! ! ! ! ! (what??)
				@tmpkeys = keys %ATTRIBFILEHASH;
			}
		} else {
			@tmpkeys = ();  #this can happen above too
		}																											#DEBUG:print "\t* There are " . @tmpkeys . " files related to $tmpmetaattrib . . . ";#OH

		##### Process each file related to this meta-attribute, check some things about it:
		foreach $tmpfile (@tmpkeys) {
			if ($ATTRIBFILEHASH{"$tmpfile"} >= 1) {																	#DEBUG:print "\n[X1]TMPFILE=$tmpfile\n";#
				if ($ATTRIBUTES_BY_ACCESS{"$tmpmetaattrib"} > SECURITY_LEVEL_LOWEST) {	# Keep track of access level for this attribute
					if (!defined $FILES_BY_ACCESS{$tmpfile}) {
						$ATTRIBUTES_BY_ACCESS{"$tmpmetaattrib"} = SECURITY_LEVEL_DEFAULT;							#DEBUG:print "\n=> Lowering access level for attribute $tmpmetaattrib to DEFAULT level of ".SECURITY_LEVEL_DEFAULT."!";		#
					} elsif ($FILES_BY_ACCESS{"$tmpfile"} < $ATTRIBUTES_BY_ACCESS{"$tmpmetaattrib"}) {
						$ATTRIBUTES_BY_ACCESS{"$tmpmetaattrib"} = $FILES_BY_ACCESS{"$tmpfile"};						#DEBUG:print "\n=> Lowering access level for attribute $tmpmetaattrib to $FILES_BY_ACCESS{$tmpfile}!";		#
					}
				}
			}
		}
		close(METALIST);
		$nummeta++;
    }#endforeach


    ###### Report what happened (1):
    print "\r" . " " x $MAX_WIDTH . "\r";    ##print "\n*** Done processing inverse meta-attributes...";


    ###### Report what happened (2):
    &log("\n" . $FIRST_REPORT . "\n*** ".sprintf("%4u",$nummeta)." different meta-filelists were created in $METAFILELIST_DIR.\n");
}#endsub create_metaattribute_filelists
######################################################################################################################################################

###########################################################################
sub trimdirofffilelist {
    if ($ARGV[1] ne "") {
        my $errmsg  = "\nFATAL ERROR: You gave an argument other than \"-t\".\n\nThe -t option takes no direct arguments; it works with STDIN and STDOUT.\n\nYou must use < to redirect STDIN from your filelist,\n";;
           $errmsg .= "and > to redirect STDOUT to your output to an output file.";
           $errmsg .= "\n\nEXAMPLE: $0 -t <oldlist.m3u >newlist.m3u\n\nI purposely made it difficult to prevent overwriting files.\n\nFor more help, $0 -?.\n";
        &death($errmsg);
    }
    my $tmpext;
    while ($line=<STDIN>) {
        $line = &filenametoregex($line);
        print $line;
    }
}#endsub trimdirofffilelist
###########################################################################

###########################################################################
sub filenametoregex {
	# PURPOSE:	convert a filename to a smaller ('weaker') regular 
	#			expression that still matches the said file . . . . 

    my $s = $_[0];

    ##### Erase the directory:
    #$s =~ s/^.*\\//g;#win-style
    #$s =~ s/^.*\///g;#nix-syle
    $s =~ s/^.*[\/\\]//g;#all-styles

	#### Erase the extension, if it's one of our supported extensions:
    foreach $tmpext (@EXTENSIONS) { $s =~ s/\.$tmpext$//; }

	#### Convert () to \(\), etc:
    $s = &regexquote($s);
    return($s);
}#endif filenametoregex
###########################################################################


###########################################################################
sub osslash {
    my $s = $_[0];
    if ($UNIX==1)	{ $s =~ s/\\/\//g; }
    else     		{ $s =~ s/\//\\/g; }
    return($s);
}#endsub fixslash
###########################################################################

###########################################################################
sub convertextendedhelp {
my $o = $0;
$o =~ s/^.*[\/\\]//g;
my $a = <<__EOF__;

CONVERTING STATIC FILELISTS INTO ATTRIBUTE FILES -- EXTENDED HELP.

PRESS ENTER to scroll through each page or CTRL-C/BREAK to stop now.

__EOF__
print "\n$a";
my $bah = <STDIN>;
$a = <<__EOF__;

USAGE: $o -c a.m3u a.txt AttributeName >a.bat

GIVEN: AttributeName is the attribute you want to assign to all the mp3s in
       the filelist (party, sucky, good, long, boring, metal, etc)
GIVEN: a.m3u filelist; lines like "c:\\mp3\\Misfits\\Earth AD\\05_Green Hell.mp3"
GIVEN: a.txt copy of filelist, with each line reduced to the minimal matching

       keystrokes for just the filename. "Green Hell" or "05_".  (This allows
       us flexibility in changing the name of the mp3 later, as long as it
       matches the minimal matching keystroke!  This is the same as the part
       before the colon in any attribute list (attrib.lst).  NOTE THAT A.TXT
       MUST BE IN SYNC WITH A.M3U.  That is, line X from a.m3u should refer to
       the same mp3 as line X from a.txt.  Here is another example:

                .M3U line: c:\\mp3\\undead\\dawn\\01_evening of desire.mp3
                A.TXT line possibility #1: 01_
                A.TXT line possibility #2: evening
                A.TXT line possibility #3: desire
                A.TXT line possibility #4: evening.*desire
                This would let us rename the file a bit, and as long
                as it matches the minimal matching keystrokes regex,
                the attribute would continue to be applied to the new
                filename without us having to do anything.
__EOF__
print "\n$a";
$bah = <STDIN>;
$a = <<__EOF__;

Finally, at the command line you should use the > character to redirect
the output to a script file with the extension BAT.

Review this script.  Make sure it isn't doing something you don't want!
If the script is fine, RUN IT ONCE AND ONLY ONCE.

If used properly, ConvertMode will actually convert one filelist of mp3s
into many separate attribute files for each mp3.

__EOF__
print "\n$a";
$bah = <STDIN>;
$a = <<__EOF__;

For example, if we have a filelist (a.m3u):
        c:\\mp3\\70s\\queen\\another one bites the dust.mp3
        c:\\mp3\\80s\\madonna\\like a virgin.mp3
        c:\\mp3\\90s\\divinyls\\i touch myself.mp3

And we have made our minimal matching keystroke regex list (a.txt):
        another.*dust
        like.*virgin
        touch.*myself

And the attribute we've selected is 'party',

...Then the generated script will actually go into c:\\mp3\\70s\\queen,
and add the line:
        another.*dust:party
to attrib.lst (it will create it if it doesn't exist).  It will then
go into c:\\mp3\\80s\\madonna and add the line:
        like.*virgin:party
to attrib.lst, and finish up by going into c:\\mp3\\90s\\divinyls and
add the line:
        touch.*myself:party

__EOF__
print "\n$a";

$bah = <STDIN>;
$a = <<__EOF__;

The idea is that this method, while a bit manual in its approach,
will allow us to import filelists made manually, or by other programs,

into our own classification system.  Perhaps you manually made a filelist
before using this program, and would like to convert the data that is the
filelist into separate attribute files.  THIS WOULD BE PAINFUL TO DO
MANUALLY.


__EOF__
print "\n$a";


$bah = <STDIN>;
$a = <<__EOF__;

Most filelists have directories in them, and this would make reducing
each filename to the minimal matching keystroke regex a bit annoying
and cumbersome and repetitive.  So I added another option that takes
an existing filelist and removes the directories from each line, removes
the mp3 extension from the end of the line, and does a few other regex
blackmagic tricks to make the ride a bit less bumpy:


        $o -t <a.m3u >a.txt

(After doing this, edit a.txt and reduce each name to the minimal
matching regex.  In 99% of cases, the track number followed by an
underscore is sufficient.  EX: "02_" matches "02_name.mp3".)

When done, simply
        $o -c a.m3u a.txt AttributeName >runme.bat
...then review runme.bat and run it if satisfied.

__EOF__
print "\n$a";

exit;
}#endsub convertextendedhelp
###########################################################################

###########################################################################
sub convert_checkoptions {
my $error=$_[0];
#ASSUMES @ERRORS (to push errors onto)

#0=-c 1=a.m3u, 2=a.txt, 3=attrib, 4=shouldn't exist

##### First check if any options are missing, then check if we have too many options:

for (my $i=1; $i<=3; $i++) { if ($ARGV[$i] eq "") { $error=1; push(@ERRORS,"Argument ".($i+1)." cannot be blank!"); return($error); } }
if ($ARGV[4] ne "") { $error=1; push(@ERRORS,"Too many arguments! $ARGV[4] should not be there.\nPerhaps you need a > before your output script name.") }

##### Then check if any of the files mentioned exist or not:
if (!-e $ARGV[1]) { $error=1; push(@ERRORS,"Input filelist $ARGV[1] does not exist!"); }
if (!-e $ARGV[2]) {
    $error=1; my $errmsg = "Input regexlist $ARGV[2] does not exist!\nPerhaps you need to use the -t option to convert\n$ARGV[1] to $ARGV[2] without the directories, then manually\nreduce each name to a minimal matching regex.";
    $errmsg .= "\nRefer to the help on trimming directories\nand why you may want to do this.";
    push(@ERRORS,$errmsg);
}
if ($DEBUG_CONVERT>=2) { print "[ZZ] \$error is currently ".$error.". \@ERRORS has ".@ERRORS." error messages queued.\n"; }
return($error);
}#endsub convert_checkoptions
###########################################################################

###########################################################################
sub convertshowerrors {
    my @ERRORS = @{$_[0]};
    my $numerrors = @ERRORS;
    my $currenterror = 0;
    if ($DEBUG_CONVERT>=2) { print "numerrors is $numerrors\n"; }
    foreach my $err (@ERRORS) {
      $currenterror++;
      if ($currenterror == 1) { print "\n"; } #lead with 1 blank line
      $err =~ s/\n/\n       $1/g;
      &log("ERROR: $err\n\n");

      if ($currenterror<$numerrors) { print "Hit [ENTER] for error #".($currenterror+1)." of ".$numerrors.".\n"; my $bah=<STDIN>; }
    }
}#endsub convertshowerrors
###########################################################################

###########################################################################
sub convert_checkfiles {
my $error = $_[0];
#ASSUMES @ERRORS (to push errors onto)
#ASSUMES local @INPUTFILELIST=();
#ASSUMES local @INPUTREGEXLIST=();
#ASSUMES local $ATTRIBUTETOUSE="";


open(MP3,  $ARGV[1]) || &death("could not open [6] $ARGV[1]");
open(REGEX,$ARGV[2]) || &death("could not open [7] $ARGV[2]");
		binmode MP3,   ":encoding(UTF-8)";
		binmode REGEX, ":encoding(UTF-8)";

$ATTRIBUTETOUSE=$ARGV[3];

@INPUTFILELIST=<MP3>;
@INPUTREGEXLIST=<REGEX>;

if (@INPUTFILELIST != @INPUTREGEXLIST) {
    push(@ERRORS,"$ARGV[1] and $ARGV[2] must have the same number of lines!\n$ARGV[1] has ".@INPUTFILELIST." lines, but $ARGV[2] has ".@INPUTREGEXLIST." lines!");
    return(1);
}

my $mp3=""; my $regex=""; my $lineforprinting=""; my $tmperr="";
for (my $line=0; $line<@INPUTFILELIST; $line++) {
  $mp3   = @INPUTFILELIST [$line];

  $regex = @INPUTREGEXLIST[$line];
  chomp $mp3;
  chomp $regex;

  if ($mp3 !~ /$regex/i) {
    $lineforprinting = $line + 1;
    $tmperr  = "Line $lineforprinting of $ARGV[2], which is:\n      $regex\ndoes not regex-match line $lineforprinting of $ARGV[1], which is:\n      $mp3\nTry reducing the regex to a shorter value,\n";
    $tmperr .= "like just the tracknumber (followed by underscore),\nor the most unique word in the filename.";
    push(@ERRORS,$tmperr);
  }
}

if ($DEBUG_CONVERT>=2) { print "There are ".@INPUTFILELIST." lines in $ARGV[1].\n"; print "There are ".@INPUTREGEXLIST." lines in $ARGV[2].\n"; print "[YY] \$error is currently ".$error.". \@ERRORS has ".@ERRORS." error messages queued.\n"; }
&scriptcomment(@INPUTFILELIST." lines in $ARGV[1] and $ARGV[2].");

##### Sanitycheck in case we pushed an error on @ERROR but forgot to set $error to 1:
if (@ERRORS > 0) { $error=1; }
return($error);
}#endsub convert_checkfiles
###########################################################################

###########################################################################

sub convert_checkstuff {
    my $error=0;
    ##### Check for errors in commandline options, and errors in the actual files:
    $error=&convert_checkoptions($error); &convertprocesserrors($error);
    $error=&convert_checkfiles  ($error); &convertprocesserrors($error);
}
###########################################################################

###########################################################################
sub convertprocesserrors {
    my $error = $_[0];
    if ($error==1) { &convertshowerrors(\@ERRORS); &convertextendedhelp; exit; }
}
###########################################################################


####################################################################################
sub delete_old_lists {
	print "\n\n\n\n\n\n*** Recycling old filelists...\n";
	if ($UNIX) {
		my $delete = $CLEANPRE;   #I'll keep the -i in, don't want to trick you.
		system("$delete $ATTRIBUTELIST_DIR/*." . $filelistextension);
		system("$delete  $METAFILELIST_DIR/*." . $filelistextension);	
		system("$delete  $DATEFILELIST_DIR/*." . $filelistextension);
		if ($NO_GENRE_PROCESSING_WHATSOEVER != 1) { system("$delete $GENREFILELIST_DIR/*." . $filelistextension); }
		#TODO wiping the bands/artists/songs files has not been covered yet
	} else {
		#TODO: change this to simply us the &osslash function
		my $ATTRIBUTELIST_DIR_W_BACKSLASH = $ATTRIBUTELIST_DIR;
		my  $METAFILELIST_DIR_W_BACKSLASH =  $METAFILELIST_DIR;
		my  $DATEFILELIST_DIR_W_BACKSLASH =  $DATEFILELIST_DIR;

		#Not dealing with bands/artists/songs as we're just piggybacking off the genre framework

		my $GENREFILELIST_DIR_W_BACKSLASH = $GENREFILELIST_DIR;
		   $ATTRIBUTELIST_DIR_W_BACKSLASH =~ s/\//\\/g;
		    $METAFILELIST_DIR_W_BACKSLASH =~ s/\//\\/g;
		    $DATEFILELIST_DIR_W_BACKSLASH =~ s/\//\\/g;
		   $GENREFILELIST_DIR_W_BACKSLASH =~ s/\//\\/g;
		#^^^ just terrible what bill gates has forced us to do with our lives...
		my $move=$CLEANPRE;
		system("$move \"$ATTRIBUTELIST_DIR_W_BACKSLASH\\*."."$filelistextension\" $CLEANPOST");
		system("$move  \"$METAFILELIST_DIR_W_BACKSLASH\\*."."$filelistextension\" $CLEANPOST");
		system("$move  \"$DATEFILELIST_DIR_W_BACKSLASH\\*."."$filelistextension\" $CLEANPOST");
		if ($NO_GENRE_PROCESSING_WHATSOEVER != 1) { system("$move $GENREFILELIST_DIR_W_BACKSLASH\\*."."$filelistextension $CLEANPOST"); }
	}#endif
	print "\n\n\n\n\n";
}#endsub delete_old_lists
####################################################################################

######################################################################################################################################################
sub scriptcomment {			#i think this might only be used by an obscure command-line option
    my $s = $_[0];
    my $comment;
    if ($UNIX) { $comment = ";;;;;"; }
    else       { $comment = ":::::"; }
    if ($s !~ /\n$/) { $s.="\n"; }
    print "$comment $s";
}
######################################################################################################################################################
###########################################################################
sub convertgetinfo {
    my $file    = $_[0];
    my $dir     = $file;    #returned with no trailing slash
    my $drive   = $file;    #returned with no trailing colon
    my $mp3only = $file;    #returned with extension

    $dir     =~ s/^(.*[\/\\])([^\/\\]*)$/$1/;
    $mp3only =~ s/^(.*[\/\\])([^\/\\]*)$/$2/;
    #&scriptcomment("      dir[1] is $dir");

	#OHOH before i was manually setting the slashes, then i used fix slash, 
	#then fixslash's meaning changed, i might need to set up the manual way again

	$dir=&osslash($dir);
    if (!$UNIX) {
        if ($drive =~ /^([A-Z]):/i) {
            $drive =~ s/^([A-Z]):.*$/$1/i;
            $dir   =~ s/^[A-Z]:(.*)$/$1/i;
        }
    }
    #&scriptcomment("drive:dir[2] is $drive".":"."$dir");
    $dir =~ s/[\\\/]$//;#don't trail
    #&scriptcomment("drive:dir[3] is $drive".":"."$dir");
    #$dir     = &regexquote($dir);
    #&scriptcomment("drive:dir[4] is $drive".":"."$dir");
    #$mp3only = &regexquote($mp3only);
    $drive =~ tr/[a-z]/[A-Z]/;
    $dir   =~ tr/[A-Z]/[a-z]/;
    #&scriptcomment("returning drive/dir/mp3only of $drive/$dir/$mp3only");
    return($drive,$dir,$mp3only);
}#endsub convertgetinfo
###########################################################################




############################################################################################
sub findfilesonly {
		my @tmpfiles=();
        foreach my $currentCollection (@COLLECTIONS) {
            print "\n*** Finding files in ".$currentCollection.".";
            push(@tmpfiles,&filefind($currentCollection,".",{extensionsonly=>1,dots=>1}));
        }
		foreach my $tmpfile (@tmpfiles) {
			if ($USE_BACKSLASHES_INSTEAD_OF_SLASHES) { $tmpfile =~ s/\//\\/g; }
			else                                     { $tmpfile =~ s/\\/\//g; }
			push(@files,$tmpfile);
		}
}
############################################################################################
###########################################################################
sub writefilesindex {
	&log("\n*** Writing file index $FILE_INDEX ...");
	my $tmpfilename = $FILE_INDEX;
	open (FILEINDEX, ">$tmpfilename") || &death("could not open [8] $tmpfilename!!\nPerhaps the directory does not exist... Look carefully at the filename and make sure the directory exists too.\n");
	binmode FILEINDEX, ":encoding(UTF-8)";
	foreach my $file (@files) { print FILEINDEX $file . "\n"; }
	close(FILEINDEX);
}#endsub writefilesindex
###########################################################################
###########################################################################
sub readfilenamesfromfileindex {
	my $tmpfilename = $FILE_INDEX;
	my $line="";
	open (FILEINDEX, "$tmpfilename") || &death("could not open [10] \"$tmpfilename\"!!\nPerhaps the directory it is in does not exist... Look carefully at the filename and make sure the directory exists too.\n");
			binmode FILEINDEX, ":encoding(UTF-8)";
	&log("\n*** Reading filenames from\t\t$FILE_INDEX ...");
	while ($line=<FILEINDEX>) {
	        chomp $line;
	        push(@files,$line);
	        $numEncountered++;
	        $ALLFILES{$line}=1;
	}#endwhile
	close(FILEINDEX);
}#endsub readfilenamesfromfileindex
###########################################################################
###########################################################################
sub readattribnamesfromfileindex {
	my $tmpfilename = $ATTRIB_LIST_INDEX;   #which lives in $ATTRIBUTELIST_DIR
	my $line="";
	open (FILEINDEX, "$tmpfilename") || &death("could not open [11] $tmpfilename!!\nPerhaps the directory does not exist... Look carefully at the filename and make sure the directory exists too.\n");
			binmode FILEINDEX, ":encoding(UTF-8)";
	&log("\n*** Reading attribute file list from\t$ATTRIB_LIST_INDEX ...");
	while ($line=<FILEINDEX>) {
			chomp $line;
			push(@attributelists,$line);
			$numEncountered++;
			$ALLFILES{$line}=1;
	}#endwhile
	close(FILEINDEX);
}#endsub readattribnamesfromfileindex
###########################################################################
###########################################################################
sub find_all_files_and_lists {
        &findfilesonly;
        &writefilesindex;
        &findattriblists;
        &writeattriblists;
}#endfusb find_all_files_and_lists
###########################################################################

##################################################################################################################
sub write_genre_list {
	if ($NO_GENRE_PROCESSING_WHATSOEVER) { return; }
	my @genres_encountered = sort keys %GENRE;
	my $num_genres_encountered = @genres_encountered;
	&log("\n*** Writing list of genres encountered ($num_genres_encountered total) to $GENRE_LIST...");
	 my $tmpfilename = $GENRE_LIST;
	open (GENRELIST, ">$tmpfilename") || &death("could not open [12A] $tmpfilename!!\nPerhaps the directory does not exist... Look carefully at the filename and make sure the directory exists too.\n");
	binmode GENRELIST, ":encoding(UTF-8)";
	foreach my $genre (@genres_encountered) { print GENRELIST $genre . "\n"; }
	close(GENRELIST);
}#endsub write_genre_list
##################################################################################################################


##################################################################################################################
sub write_artist_list {
	#TODO: idea write another artist list in descending order of how frequent that artist is represented
	#if ($NO_GENRE_PROCESSING_WHATSOEVER) { return; }
	my @artists_encountered = sort keys %ARTIST;
	my $num_artists_encountered = @artists_encountered;
	&log("\n*** Writing list of artists encountered ($num_artists_encountered total) to $ARTIST_LIST...");
	my $tmpfilename = $ARTIST_LIST;
	open (LIST, ">$tmpfilename") || &death("could not open [12B] $tmpfilename!!\nPerhaps the directory does not exist... Look carefully at the filename and make sure the directory exists too.\n");
	binmode LIST, ":encoding(UTF-8)";
	foreach my $tmp (@artists_encountered) { print LIST $tmp . "\n"; }
	close(LIST);
}#endsub write_artist_list
##################################################################################################################

##################################################################################################################################################
sub write_album_list {
	#if ($NO_GENRE_PROCESSING_WHATSOEVER) { return; }
	my @albums_encountered = sort keys %ALBUM;
	my $num_encountered = @albums_encountered;
	&log("\n*** Writing list of albums encountered ($num_encountered total) to $ALBUM_LIST...");
	my $tmpfilename = $ALBUM_LIST;
	open (LIST, ">$tmpfilename") || &death("could not open [12C] $tmpfilename!!\nPerhaps the directory does not exist... Look carefully at the filename and make sure the directory exists too.\n");
	binmode LIST, ":encoding(UTF-8)";
	foreach my $tmp (@albums_encountered) { print LIST $tmp . "\n"; }
	close(LIST);
}#endsub write_album_list
##################################################################################################################################################

##################################################################################################################################################
sub write_song_list {
	#if ($NO_GENRE_PROCESSING_WHATSOEVER) { return; }
	my @songs_encountered = sort keys %SONG;
	my $num_encountered = @songs_encountered;
	&log("\n*** Writing list of songs encountered ($num_encountered total) to $SONG_LIST...");
	my $tmpfilename = $SONG_LIST;
	open (LIST, ">$tmpfilename") || &death("could not open [12D] $tmpfilename!!\nPerhaps the directory does not exist... Look carefully at the filename and make sure the directory exists too.\n");
	binmode LIST, ":encoding(UTF-8)";
	foreach my $tmp (@songs_encountered) { print LIST $tmp . "\n"; }
	close(LIST);
}#endsub write_song_list
##################################################################################################################################################




######################################################################################################################################################
sub readgenredatafromgenreindex {
	if ($NO_GENRE_PROCESSING_WHATSOEVER) { return; }
	my ($tmpgenre,$tmpfilename,$tmpline)="";
	my $tmpfilename = $GENRE_INDEX;
	&log("\n*** Reading id3v1 genre index from\t$GENRE_INDEX ...");
	open (GENREINDEX, "$tmpfilename") || &death("could not open [14] $tmpfilename!!\nPerhaps the directory does not exist... Look carefully at the filename and make sure the directory exists too.\n");
			 binmode GENREINDEX, ":encoding(UTF-8)";
	while ($tmpline=<GENREINDEX>) {
			chomp $tmpline;
			($tmpgenre, $tmpfilename) = split(/::::/,$tmpline);

			#{$ATTRIBUTES{"genre-".$tmpgenre}}->{$tmpfilename}=1;								#GENRE changed from capital to lowercase 20081123 because we have now added documentation stating the key to ATTRIBUTES must be lowercase, as capitals have proven to be an annoying problem
			  $ATTRIBUTES{"genre-".$tmpgenre} ->{$tmpfilename}=1;								#GENRE changed from capital to lowercase 20081123 because we have now added documentation stating the key to ATTRIBUTES must be lowercase, as capitals have proven to be an annoying problem
			#{$GENRE{$tmpgenre}}->{$tmpfilename}=1;
			  $GENRE{$tmpgenre} ->{$tmpfilename}=1;
	}#endwhile
	close(GENREINDEX);
}#endsub readgenredatafromgenreindex
######################################################################################################################################################

###########################################################################
sub readdatedatafromdateindex {
	if ($DATE_INDEX_READ) { return; }
	my $index_token = $_[0];
	my $tmpfilename = $DATE_INDEX;
	my ($tmpdate)="";
	local $linenum=0;
	local $when = "reading date data from $DATEINDEX";
	$tmpfilename =~ s/[\/]/\\/g;
	my $openfail=0;
	open (DATEINDEX, "$tmpfilename") || ($openfail=1);
			binmode DATEINDEX, ":encoding(UTF-8)";
	if ($openfail==1) {
		&log("\n\nFATAL ERROR: Could not open date index of \"$tmpfilename\"!! [code:7UX$index_token]\nPerhaps the directory does not exist... Look carefully at the filename and make sure the directory exists too.\n");
		return;
	}
	&log("\n*** Reading date info from\t$DATE_INDEX ... THIS CODE IS NOT VERY TESTED!!! GOOD LUCK!! IT SHOULD WORK IN AN APPROXIMATE FASHION BUT IT IS NOT RECOMMENDED TO ALWAYS USE THIS OPTION...");
	while ($line=<DATEINDEX>) {
		$linenum++;
		chomp $line;
		($tmpdate, $tmpfilename) = split(/::::/,$line);
		&checkvaliddate($tmpdate,"in attribute list $tmpfilename, line number $linenum, tmpfile=$tmpfilename");

		#### OHOH untested . . . 
		#{$ATTRIBUTES{"DATE-".$tmpdate}}->{$tmpfilename}=1;				#capital letters in ATTRIBUTES keys are forbidden in the documentation -- but this one may hardcoded for a reason. Let's leave it in.. for now.(20081123)
		  $ATTRIBUTES{"DATE-".$tmpdate} ->{$tmpfilename}=1;				#capital letters in ATTRIBUTES keys are forbidden in the documentation -- but this one may hardcoded for a reason. Let's leave it in.. for now.(20081123)
		if (length($tmpdate)>=8) {
			$tmpdate =~ /^(....)(..)(..)/;
			$yyyy=$1;
			$yyyymm="$1$2";
			$yyyymmdd="$1$2$3";
			#testing:
			$yyyymmddhh="$1$2$300";
			$yyyymmddhhmm="$1$2$30000";
			$yyyymmddhhmmss="$1$2$3000000";
		} 
		if (length($tmpdate)==12) {	#yyyyMMddHHmm
			$tmpdate =~ /^(....)(..)(..)(..)(..)/;
			$yyyymmddhh="$yyyymmdd$4";
			$yyyymmddhhmm="$yyyymmddhh$5";
		#next 2 lines no longer necessary:
		#} else {
		#	&death("\n\nFATAL ERROR 9K2E: tmpdate is \"$tmpdate\"!\n\n");
		}
		$FILEKEY_YYYYMMDDHHMMSSDATEVALUE{$tmpfilename}=$yyyymmddhhmmss;
		$FILEKEY_YYYYMMDDHHMMDATEVALUE{$tmpfilename}=$yyyymmddhhmm;
		$FILEKEY_YYYYMMDDHHDATEVALUE{$tmpfilename}=$yyyymmddhh;
		$FILEKEY_YYYYMMDDDATEVALUE{$tmpfilename}=$yyyymmdd;
		$FILEKEY_YYYYMMDATEVALUE{$tmpfilename}=$yyyymm;
		$FILEKEY_YYYYDATEVALUE{$tmpfilename}=$yyyy;
	}#endwhile
	close (DATEINDEX);
	$DATE_INDEX_READ=1;
}#endsub readdatedatafromdateindex
###########################################################################


###########################################################################
sub create_genre_filelists {
	local $GATHER_INFO_ONLY = $_[0];           #set to 1 to NOT write the filelists out, specifically because we now do this elsewhere
	local ($mp3_file,$genre)=("","");
	local $num_files_to_check = @files;
	my @tmpfilelist;
	
	
	if ($NO_GENRE_PROCESSING_WHATSOEVER) { return; }
	if ($DEBUG_SKIPGENRE>=1) { return; }
	if (!$SKIP_GENRE) { &gather_id3_genres_artists_albums_songs; }
	if ($GATHER_INFO_ONLY) { return; }
	
	$genres_encountered=0;
	my $currentgenre="";
	my $currentgenre4access="";
	my $tmpfile2="";
	&log("\n");

	
	#DEBUG: foreach $currentgenre (sort keys %GENRE) { print "\n *** key is $currentgenre .."; }
	
	foreach $currentgenre (sort keys %GENRE) {
	    #DEBUG: print "Doing current genre $currentgenre\n";	
		if ($DEBUG_GENRE_2015>1) { print "\n[CGP][doing current genre $currentgenre"; }

		if (($currentgenre eq "") || ($currentgenre eq "\n")) { next; }
	
	    $currentgenre4access = $currentgenre;
	    $currentgenre4access =~ s/\//--/;
	    $currentgenre4access =~ s/:/- /;
	    $currentgenre4access =~ s/\t/ /;
	
	
	    $filesfound=0;
#	    $tmpfilelist = &clean_name_for_filenames("$GENREFILELIST_DIR/$GENRE_PREFIX$currentgenre4access".".".$filelistextension);	#BUG! slashes in directories got converted to --
	    $tmpfilelist = "$GENREFILELIST_DIR/" .          &clean_name_for_filenames($currentgenre4access).".".$filelistextension ;
	    open (LIST,">$tmpfilelist")
	       || &log("\n\n&*** CONCERNING ERROR: Could not create genre filelist \"$tmpfilelist\"!!!!\n" .
	               "Perhaps you need to redefine \$GENREFILELIST_DIR at the top of the source code...Look carefully at the filename and make sure any directories needed already exist.\n\n");
		binmode LIST, ":encoding(UTF-8)";

	    @tmpfilelist = sort keys %{$GENRE{$currentgenre}};
	
	    foreach (@tmpfilelist) {
			if ($DEBUG_GENRE_2015>1) { print "\n[CGP][\@tmpfilelist][\$_=" . $_ . "]}"; }
	        #f (%{$GENRE{$currentgenre}}->{$_} >= 1) {		#why >=1? because it might be 1(in) or 2(whitelist/permanent-in)
	        if (  $GENRE{$currentgenre} ->{$_} >= 1) {		#why >=1? because it might be 1(in) or 2(whitelist/permanent-in)
	        #if (1) {										#bad idea: tried in 20160108 to fix the stupid genre meta not working issue, which has since been fixed
				print LIST $_ . "\n"; $filesfound++;
				#%{$ATTRIBUTES{"genre-".$currentgenre}}->{$_}=1;				#add internal "genre-Metal" type representation for current file, so we can do meta-magic with genres
				   $ATTRIBUTES{"genre-".$currentgenre} ->{$_}=1;				#add internal "genre-Metal" type representation for current file, so we can do meta-magic with genres
				#f ($DEBUG_GENRE_2015>1) { print "[\%{\$ATTRIBUTES{\"genre-\"\.\$currentgenre}}->{\$_}=" . %{$ATTRIBUTES{"genre-".$currentgenre}}->{$_} . "]"; }
				if ($DEBUG_GENRE_2015>1) { print "[\%{\$ATTRIBUTES{\"genre-\"\.\$currentgenre}}->{\$_}=" .   $ATTRIBUTES{"genre-".$currentgenre} ->{$_} . "]"; }
				#MOVED to below: &pushhashofarrays(\%INVERSE_ATTRIBUTES,$tmpfile2,"genre-".$currentgenre4access);#
	        }
	    }
	    close(LIST);
	    $genres_encountered++;
	    &logonly("\t" . sprintf("%5u",$filesfound) . "\tGENRE: $currentgenre\n");
	}

#	#attempted optimization -- just to move the pushhash line from above....
#	foreach $currentgenre (sort keys %GENRE) {
#	    $currentgenre4access = $currentgenre;
#	    $currentgenre4access =~ s/\//--/;
#	    $currentgenre4access =~ s/:/- /;	
#	    if (($currentgenre eq "") || ($currentgenre eq "\n")) { next; }
#	    @tmpfilelist = sort keys %{$GENRE{$currentgenre}};
#	    foreach (@tmpfilelist) {
#	        if (%{$GENRE{$currentgenre}}->{$_} >= 1) {
#				&pushhashofarrays(\%INVERSE_ATTRIBUTES,$_,"genre-".$currentgenre4access);#
#	        }
#
#	}
#OH

	
	my $tmpREPORT = "*** ".sprintf("%4u",$genres_encountered)." different genrefilelists were created in $GENREFILELIST_DIR.";
	&log($tmpREPORT);
	$FIRST_REPORT .= $tmpREPORT;
}#endsub create_genre_filelists
###########################################################################


#############################################################################################################################
sub create_date_filelists {     #pass this a "1" as a parameter to not actually write the date lists to disk
#    my %ATTRIB = %{$_[0]};

	#FAIL: #$ATTRIB{"test or something"}=1;			#fuck scope. "local" kicks ass!
	#WIN:  #$ATTRIBUTES{"test or something"}=1;

	my $SUPPRESS_FILEWRITE=$_[1];		#never used; abandoned from some earlier point apparently (discovered this status 20081123)

	#DEBUG: print "\nDEBUG_SKIPDATE is $DEBUG_SKIPDATE\nSKIP_DATE is $SKIP_DATE\nDONOTACTUALLYWRITETHELISTS is $_[0]\n";
	if ($DEBUG_SKIPDATE>=1) { return; }
	#if ($SKIP_DATE) { &readdatedatafromdateindex("bambam"); } #bambam is a token for debugging
	#else            { &gather_file_dates;                   }

	&write_date_filelists($SUPPRESS_FILEWRITE);#,\%ATTRIB);
	&write_file_dates_index;
}#endsub create_date_filelists
#############################################################################################################################
#####################################################################################
sub write_date_filelists {
	my $NO_FILEWRITE = $_[0];   #pass a 1 to prevent writing of files
#    my $aref = $_[1];
#    my %ATTRIB = %{$aref};
	my $value="";

	##### Write the two kinds of date lists we create:
	#DEBUGTprint "\n\naref(1) is $aref\n\n";#
	my $num_dated_filelists_created  = &write_date_range_filelists   ($NO_FILEWRITE);#,$aref);
	   $num_dated_filelists_created += &write_date_specific_filelists($NO_FILEWRITE);
	
	##### Let user know how many we created:
	my $tmpREPORT .= "\n*** ".sprintf("%4u",$num_dated_filelists_created)." different date-filelists were created in $DATEFILELIST_DIR.";
	$FIRST_REPORT .= $tmpREPORT;
	&log($tmpREPORT);
}#endsub write_date_filelists
###########################################################################
###############################################################################################
sub write_date_range_filelists {
	my $NO_FILEWRITE = $_[0];			#unused, but left in due to past development
#    my $aref = $_[1];
	#DEBUG:	print "\n\naref(2) is $aref\n";#
#    my %ATTRIB = %{$aref};				#moved on to just using local %ATTRIBUTES instead  20081123
	my $verbose=0;						#
	my $tmpinfo="";
	my $factor = int (@files / 18);		# Determine rate of progress meter
	if ($factor == 0) { $factor=1; }
	my $j=0;

	##### Get the intervals we will be processing with:
	my @TMPINTERVALS=sort {$a<=>$b} keys %INTERVALS;
	&log("\n\n*** [B] Processing file date information into ".@TMPINTERVALS." date ranges (phase 1) (factor=$factor)...");
	
	##### NEW: Does every file, even ones not date tagged:
	foreach my $file (@files) {
		##### Display progress meter:
		$j++; if (($j % $factor)==0) { print "."; }

		##### Fetch date from attribute, or if no attribute, from file:
		$value = &get_date_value_from_attribute_or_date($file);

		#### DEBUG:	#it's a problem if we're not getting a value for $value
		if (($verbose>1) || ($DEBUG_DATE_FROM_INDEX)) { print qq[\nValue is $value]; print qq[\nPushing into \@{\$FILES_BY_DATE{] . $value . qq[}} the file "$file"...]; }

		##### Now that we know the date,store it:
		#DEBUG: print "push(\@{\$FILES_BY_DATE{".$value."}},".$file.");\n";
		push(@{$FILES_BY_DATE{$value}},$file);
	}#endif
	
	##### Get current date in YYYYMMDD format for timestamp:
	($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst)=localtime(time);
	$year+=1900; $mon+=1; local $yyyymmdd=sprintf("%04u%02u%02u",$year,$mon,$mday);
	
	##### We have to keep track of how many days we've gone back:
	local $yyyymmdd_counter=$yyyymmdd;
	local $num_days_back=0;
	local $OVERFLOW=36500;  #How far back before we give up. I would say 100 years is about as long as possible, though if medical advancements are made in the field of longevity this may have to be increased :)
	local ($tmpdate,$tmpfile,$tmpinterval,$i)=("","","","");

	if ($verbose) { print "\nCURRENT DATE INTERVALS: @TMPINTERVALS .. Length:".@TMPINTERVALS."\n"; }

	##### OHOH this whole section could use a rewrite, unfortunately.	 (Later: Why?)

	##### Now that we have stored all these dates, start going in backwards order
	##### so we can keep track of $num_days_back and correctly process all of our
	##### "last 1 day", "last 1 week", "last 1 month"-type date range filelists:
	my $num_intervals = @TMPINTERVALS;
	&log("\n*** [C] Processing file date information into ".$num_intervals." date ranges (phase 2) (factor=$factor)...\n");
	my $k=0;
	foreach $tmpdate (reverse sort keys %FILES_BY_DATE) {
		if ($tmpdate eq "") {
			if ($verbose) { print "\nNext'ing because tmpdate=\"$tmpdate\"..."; }
			next;		#KLUDGE!
		}#endif

		if ($verbose>3) { print "\nProcessing tmpdate=\"$tmpdate\"..."; }

		#OLD: while ($yyyymmdd_counter !~ /^$tmpdate/) 
		#NEW:
		while ($tmpdate !~ /^$yyyymmdd_counter/)  {
			$k++;																							#DEBUG: if ($verbose>5) { print "\n[1v1] while $yyyymmdd_counter !~ /^$tmpdate/"; }
			print "\rSeeking $yyyymmdd_counter: $tmpdate...        ";										#Display progress info
			$yyyymmdd_counter = &decrement_date_by_one_day($yyyymmdd_counter);								#Go back another day
			$num_days_back++;																				#DEBUG: if ($verbose>5) { print "*dec to \"$yyyymmdd_counter\" ($num_days_back d back) SEEKING:\"$tmpdate\"\n"; }
			if ($num_days_back > $OVERFLOW) { last; }														#this is really an error that seems to be harmless. at first I used to die() here...
		}#endwhile
		print "\r" . " " x $MAX_WIDTH . "\r";

	    	## At this point, we've found our next target date.	    	For each interval found in our list of intervals (ie 7d, 14d, 30d),
	    	## if we've gone back less, add it.  If we've gone back more, actually remove that interval from the list of intervals we'll be checking,
	    	## that way it will get progressively faster!
	
		#DEBUG: &log("\n*** [q] Processing file date information into ".$num_intervals." date ranges (phase X)...");
		##### So first, cleanse out any intervals we no longer need to check:
		for ($i=$num_intervals-1; $i>=0; $i--) {               #for each interval check the file
			if (($TMPINTERVALS[$i] > 0) && ($TMPINTERVALS[$i] < $num_days_back)) {
				if ($verbose) { print "\nDeleting ".$TMPINTERVALS[$i]." (i=$i)(name=$INTERVALS{$i}) from TMPINTERVALS since it's less than $num_days_back days back\n"; }
				delete($TMPINTERVALS[$i]);
			}#endif
		}#endfor

		##### Then something that is too complicated for me to remember (!):
		foreach $tmpfile (@{$FILES_BY_DATE{$tmpdate}}) {
			foreach $tmpinterval (@TMPINTERVALS) {
				if ($tmpinterval > 0) {
					if ($verbose>4) { print "\n** processing tmpinterval $tmpinterval"; }
					push(@{$FILES_BY_DATE_FINAL{$tmpinterval}},$tmpfile);			
				}#endif
			}#endforeach
		}#endforeach
	}#endforeach
	if ($NO_FILEWRITE) { return; }
	
	##### Now let's write out our files:
	&log("*** [D] Processing file date information into ".$num_intervals." date ranges (phase 3)...\n");
	my $tmpfile2="";
	my $datefilelist="";
	my $datefilename="";
	my $tmpattrname="";
	$num_dated_filelists_created=0;
	@tmpkeys = sort {$a<=>$b} keys %FILES_BY_DATE_FINAL;
	foreach my $tmpkey (@tmpkeys) {
		$tmpattrname  = $DATE_RANGE_PREFIX . $INTERVALS{$tmpkey};
		$datefilename = $tmpattrname;
		$datefilelist = $DATEFILELIST_DIR."/".$datefilename.".".$filelistextension;

		$tmpinfo = "$tmpattrname...";
		print $tmpinfo;

		if (!defined $ATTRIBUTES_BY_ACCESS{$INTERVALS{$tmpkey}}) { 
			$ATTRIBUTES_BY_ACCESS{$INTERVALS{$tmpkey}} = SECURITY_LEVEL_DEFAULT;
		}

		open(DPL,">$datefilelist")||&death("could not open [2] $datefilelist! CODE X43\n");
		binmode DPL, ":encoding(UTF-8)";
		foreach my $tmpf ( sort @{$FILES_BY_DATE_FINAL{$tmpkey}} ) { 
			##### File security issues
			if ($ATTRIBUTES_BY_ACCESS{$INTERVALS{$tmpkey}} > SECURITY_LEVEL_LOWEST) {
				if (!defined $FILES_BY_ACCESS{$tmpf}) {
					$ATTRIBUTES_BY_ACCESS{$INTERVALS{$tmpkey}} = SECURITY_LEVEL_DEFAULT;
				} elsif ($FILES_BY_ACCESS{$tmpf} < $ATTRIBUTES_BY_ACCESS{$INTERVALS{$tmpkey}}) {
					$ATTRIBUTES_BY_ACCESS{$INTERVALS{$tmpkey}} = $FILES_BY_ACCESS{$tmpf};

				}#endif
			}#endif


	        $datefilename =~ tr/[A-Z]/[a-z]/;

			#DEBUG:	print "\n\%{\$ATTRIB{\"".$datefilename."\"}}->{\"".$tmpf."\"}=1;\n";#
			#$ATTRIB{TEST}=1;
			#$ATTRIBUTES{TEST}=1;
#			%{$ATTRIB{"$datefilename"}}->{"$tmpf"}=1;										#20081123 NotLast6Months.m3u not working fix			#
			#%{$ATTRIBUTES{"$datefilename"}}->{"$tmpf"}=1;									#20081123 NotLast6Months.m3u not working fix			#
			   $ATTRIBUTES{"$datefilename"} ->{"$tmpf"}=1;									#20081123 NotLast6Months.m3u not working fix			#
			#DEBUG:print "\n[DPL]writing to $datefilename this: $tmpf\n";
			#if ($USE_BACKSLASHES_INSTEAD_OF_SLASHES) { $tmpf =~ s/\//\\/g; }
			print DPL "$tmpf\n"; 
		}#endforeach
		close(DPL);
		$num_dated_filelists_created++;
		#OHOH should we do a zero byte check here too?

		##### Keep track of the fact that this filename was written:
		$DATE_RANGE_ATTRIBUTES_WRITTEN{$tmpattrname}=1;	

		#DEBUG: print "\nSetting date_range_attributes_written for $tmpattrname to 1...\n";	#OHOH

		print "\r" . " " x $MAX_WIDTH . "\r";
	}#endforeach


#OHOH
#	# optimization -- 2nd pass
#	&log("*** Processing file date information [Z] into ".$num_intervals." date ranges (inverse)...\n");
#	foreach my $tmpkey (@tmpkeys) {
#		#print ".";
#		print "\r" . " " x $MAX_WIDTH . "\r$INTERVALS{$tmpkey}" . "...";
#		$tmpattrname  = $DATE_RANGE_PREFIX . $INTERVALS{$tmpkey};
#
#		foreach my $tmpf ( @{$FILES_BY_DATE_FINAL{$tmpkey}} ) { 
#			&pushhashofarrays(\%INVERSE_ATTRIBUTES,$tmpf,$tmpattrname);#
#		}
#		print "\b";
#	}#end
#	print "\r" . " " x $MAX_WIDTH . "\r";
	

	return($num_dated_filelists_created);
}#endsub write_date_range_filelists
###############################################################################################

#########################################################################################
sub write_date_specific_filelists {
	my $NO_FILEWRITE = $_[0];
	my $num_filelists_created=0;

	if ($NO_FILEWRITE) { return(0); }

	$num_filelists_created += &write_date_specific_filelists_with(\%FILEKEY_YYYYDATEVALUE,      \%YYYY_ENCOUNTERED,      	"years");
	if ($SKIP_MONTH_TIMESLICING) {
		&log("\n\n	* Skipping month/day/hour timeslicing\n");
	} else {
		$num_filelists_created += &write_date_specific_filelists_with(\%FILEKEY_YYYYMMDATEVALUE,    \%YYYYMM_ENCOUNTERED,    	"months");
		if ($SKIP_DAYS_AND_HOURS_TIMESLICING) {
			&log("\n\n* Skipping day/hour timeslicing\n");
		} else {
			$num_filelists_created += &write_date_specific_filelists_with(\%FILEKEY_YYYYMMDDDATEVALUE,  \%YYYYMMDD_ENCOUNTERED,  	"days");
			$num_filelists_created += &write_date_specific_filelists_with(\%FILEKEY_YYYYMMDDHHDATEVALUE,\%YYYYMMDDHH_ENCOUNTERED,	"hours");
			## I am only supporting to the hour-level, sorry
			#$num_filelists_created += &write_date_specific_filelists_with(\%FILEKEY_YYYYMMDDHHMMDATEVALUE,  \%YYYYMMDDHHMM_ENCOUNTERED,	"minutes");
			#$num_filelists_created += &write_date_specific_filelists_with(\%FILEKEY_YYYYMMDDHHMMSSDATEVALUE,\%YYYYMMDDHHNMSS_ENCOUNTERED,"seconds");
		}
	}
	return $num_filelists_created;
}#endsub write_date_specific_filelists
#########################################################################################

#############################################################################################
sub write_date_specific_filelists_with {
	my %FILEKEYDATEVALUE = %{$_[0]};
	my %KEYS_ENCOUNTERED = %{$_[1]};
	my $intervalname	   = $_[2];
	my @keys   = keys %KEYS_ENCOUNTERED;
	my @keys2  = keys %FILEKEYDATEVALUE;
	my $count  = @keys;
	my $count2 = @keys2;
	##my $verbose=0;	#
	my $tmpfile2="";
	my $tmpattrname="";
	my $tmpsize="";
	my $num_dated_filelists_created=0;

	## first pass, filewrite:
	@tmpkeys = sort {$a<=>$b} @keys;
	@tmpkeys2 = sort keys %FILEKEYDATEVALUE;	#moved from inside of loop below to speed up

	##### Determine progress meter rate:	
	my $factor = 10;
	my $i=0;
	#$factor = int(($count*$count2) / 10);	#$factor=int($numEncountered / $count);	#$factor=int((@tmpkeys * @tmpkeys2) / 10);
	$factor=int(@tmpkeys / 10);
	if ($factor == 0) { $factor=1; };

	##### Display progress header:
	&log("\n*** [A] Processing file date information into $count different ");	#different years,different months,different days,different hours,different minutes,different seconds
	#print sprintf("%6s",$intervalname);	#before using \b progress stuff
	print $intervalname;
	print " (factor=$factor).";

	foreach my $tmpkey (@tmpkeys) {	
		if ($tmpkey eq "") { next; }
		#DEBUG:print "\n\nProcessing date range of $tmpkey"; #OHOH
		#$i=0;
		if (($i++ % $factor)==0) { print "."; }	#moved from below, commented out prev line

		$tmpattrname  = "$DATE_PREFIX$tmpkey";
		$datefilelist = $DATEFILELIST_DIR."/".$tmpattrname."."."$filelistextension";
		#MOVED TO OUTSIDE OF LOOP TO SPEED UP: @tmpkeys2 = sort keys %FILEKEYDATEVALUE;
		if (@tmpkeys2 > 0) {
			open(DPL,">$datefilelist")||&death("\ncould not open [2] \"$datefilelist!\" CODE X44A\n");
			binmode DPL, ":encoding(UTF-8)";
			foreach my $tmpf (@tmpkeys2) {
				#if (($i++ % $factor)==0) { print "."; }	#moved to above
				##if ($verbose>1) { print "\n\tKEYDATEVALUE=$FILEKEYDATEVALUE{$tmpf}..file=$tmpf"; }
				if ($FILEKEYDATEVALUE{$tmpf} == $tmpkey) {
					##if ($verbose>1) { print "\t...MATCH!"; }
					print DPL $tmpf . "\n";
				     #moved to below: if (!$SKIP_INVERSE_LIST) { &pushhashofarrays(\%INVERSE_ATTRIBUTES,$tmpfile2,$tmpattrname); }
				##} else {
				##	if ($verbose>1) { print "\t...NO match!"; }
				}
			}
			close(DPL);

			##### If we just made a zero byte file, kill it:
			$tmpsize=&GetFileSize($datefilelist);
			#DEBUG:print "\nSize for $datefilelist=$tmpsize";#OH
			if ($tmpsize==0) { 
				$tmp="$CLEANPRE " . &osslash($datefilelist) . " $CLEANPOST";
				#DEBUG:print "\nabout to $tmp";#OH
				system("$tmp");
			} else {
				$DATE_ATTRIBUTES_WRITTEN{$tmpkey}="1";
				#DEBUG: print "\nSetting date_attributes_written for $tmpattrname to 1...";	#
			}#
		}#endif
		$num_dated_filelists_created++;
	}#endforeach	


	## second pass: access attribute (this loop used to process inverse attributes too...)
	$i=0;
	foreach my $tmpkey (@tmpkeys) {	
		if ($tmpkey eq "") { next; }
		if (($i++ % $factor)==0) { print "."; }	#moved from below, commented out prev line
		$tmpattrname  = "$DATE_PREFIX$tmpkey";
		foreach my $tmpf (keys %FILEKEYDATEVALUE) {			#OHOH remove sort to gspeed up
			if ($FILEKEYDATEVALUE{$tmpf} == $tmpkey) {
				##if ($verbose>1) { print "\t...MATCH!"; }
				##OHOH if (!$SKIP_INVERSE_LIST) { &pushhashofarrays(\%INVERSE_ATTRIBUTES,$tmpf,$tmpattrname); }
				#OHOHOH ..... Security stuff
				if (($ATTRIBUTES_BY_ACCESS{$tmpkey} > SECURITY_LEVEL_LOWEST) || (!defined $ATTRIBUTES_BY_ACCESS{$tmpkey})) {
					if (!defined $FILES_BY_ACCESS{$tmpf}) {
						$ATTRIBUTES_BY_ACCESS{$tmpkey} = SECURITY_LEVEL_DEFAULT;
					} elsif ($FILES_BY_ACCESS{$tmpf} < $ATTRIBUTES_BY_ACCESS{$tmpkey}) {
						$ATTRIBUTES_BY_ACCESS{$tmpkey} = $FILES_BY_ACCESS{$tmpf};
					}#endif
				}#endif
			}#endif
		}#endforeach 
	}#endforeach

	return($num_dated_filelists_created);
}#endsub write_date_specific_filelists_with
#############################################################################################



###########################################################################
sub gather_file_dates {
	my $numtodo  = @files;
	my $factor   = int ($numtodo / 27);
	my $i        = 0;
	my $verbose  = 0;		#
	my $yyyymmddhhmmss = "";
	my $yyyymmddhhmm = "";
	my $yyyymmddhh = "";
	my $yyyymmdd = "";
	local $when = "";
	my $yyyymm = "";
	my $yyyy = "";
	if ($SKIP_DATE) { return; }		#OHOHOH

	&log("\n*** Gathering file date information from ".$numtodo." files.");
	if ($factor == 0) { $factor=1; }
	foreach my $tmpfile (@files) {
		##### Display pretty dots:
		$i++; if (($i % $factor)==0) { print "."; }

		##### Get file date ($mtime is number of seconds since epoch):
		($dev,$ino,$mode,$nlink,$uid,$gid,$rdev,$size,$atime,$mtime,$ctime,
			$blksize,$blocks) = stat($tmpfile);
		##### Convert date into YYYYMMDDHHSS format:
		($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst)=localtime($mtime);
		$year+=1900; $mon+=1;
		$yyyymmddhhmmss=sprintf("%04u%02u%02u%02u%02u",$year,$mon,$mday,$hour,$min,$sec);
		$yyyymmddhhmm=sprintf("%04u%02u%02u%02u%02u",$year,$mon,$mday,$hour,$min);
		$yyyymmddhh=sprintf("%04u%02u%02u%02u",$year,$mon,$mday,$hour);
		$yyyymmdd=sprintf("%04u%02u%02u",$year,$mon,$mday);
		$yyyymm=sprintf("%04u%02u",$year,$mon);
		$yyyy=sprintf("%04u",$year);

		##### Check the date for validity:
		#OH: not validating to-the-second leve (only minute) because seconds are not going to be fully supported until I feel like it, if ever
		$when = "when gathering file dates from operating system";
		&checkvaliddate($yyyymmddhhmm,"$when, file number $i, tmpfile=$tmpfile");

		##### Put date into a simple file/date hash:
		if ($verbose) { 
			print "\n\tFILEKEY_YYYYMMDDHHMMSSDATEVALUE{$tmpfile}=$yyyymmddhhmmss";
			print "\n\tFILEKEY_YYYYMMDDHHMMDATEVALUE{$tmpfile}=$yyyymmddhhmm";
			print "\n\tFILEKEY_YYYYMMDDHHDATEVALUE{$tmpfile}=$yyyymmddhh";
			print "\n\tFILEKEY_YYYYMMDDDATEVALUE{$tmpfile}=$yyyymmdd";
			print "\n\tFILEKEY_YYYYMMDATEVALUE{$tmpfile}=$yyyymm";
			print "\n\tFILEKEY_YYYYDATEVALUE{$tmpfile}=$yyyy";
		}
		$FILEKEY_YYYYMMDDHHMMSSDATEVALUE{$tmpfile}=$yyyymmddhhmmss;
		$FILEKEY_YYYYMMDDHHMMDATEVALUE{$tmpfile}=$yyyymmddhhmm;
		$FILEKEY_YYYYMMDDHHDATEVALUE{$tmpfile}=$yyyymmddhh;
		$FILEKEY_YYYYMMDDDATEVALUE{$tmpfile}=$yyyymmdd;

		$FILEKEY_YYYYMMDATEVALUE{$tmpfile}=$yyyymm;
		$FILEKEY_YYYYDATEVALUE{$tmpfile}=$yyyy;

		$YYYY_ENCOUNTERED{$yyyy}++;
		$YYYYMM_ENCOUNTERED{$yyyymm}++;
		$YYYYMMDD_ENCOUNTERED{$yyyymmdd}++;
		$YYYYMMDDHH_ENCOUNTERED{$yyyymmddhh}++;
		$YYYYMMDDHHMM_ENCOUNTERED{$yyyymmddhhmm}++;
		$YYYYMMDDHHMMSS_ENCOUNTERED{$yyyymmddhhmmss}++;
	}#endforeach file
}#endsub gather_file_dates
###########################################################################

###########################################################################
sub write_file_dates_index {
	if ($SKIP_DATE) {
		&log("\n*** NOT Writing date index to $DATE_INDEX because we read it from there ...");
		return;
	}
	&log("\n*** Writing date index to $DATE_INDEX ...");
	my $tmpfilename = $DATE_INDEX;
	my $tmpvalue = "";
	
	##OLD: foreach my $tmpf ( sort @{$FILES_BY_DATE_FINAL{$tmpkey}} ) { print DATEINDEX $t pkey . "::::" . &osslash($tmpf) . "\n"; }
	
	open (DATELIST, ">$tmpfilename") || &death("could not open [16] $tmpfilename!!\nPerhaps the directory does not exist... Look carefully at the filename and make sure the directory exists too.\n");
	binmode DATELIST, ":encoding(UTF-8)";

	#OH!
	#the variable here should be the max-time-detail we go to
	#that is, if we only were doing up to years, it would be %FILEKEY_YYYY
	#if we were going up to seconds, it would be %FILEKEY_YYYYMMDDHHSS

	foreach my $key (sort keys %FILEKEY_YYYYMMDDHHDATEVALUE) { 
		$tmpvalue = &get_date_value_from_attribute_or_date($key);
		#print DATELIST &osslash($tmpvalue) . "::::" . $key . "\n"; 
		print DATELIST $tmpvalue . "::::" . $key . "\n"; 
	}#endforeach
	close(DATELIST);
}#endsub write_file_dates_index

###########################################################################

########################################################################################################################################
sub write_genre_index {
	if ($NO_GENRE_PROCESSING_WHATSOEVER) { return; }
	&log("\n*** Writing index of id3 genres to $GENRE_INDEX ...");
	my $tmpfilename = $GENRE_INDEX;
	my @tmpfilelist=();
	open (GENREINDEX, ">$tmpfilename") || &death("could not open [13A] tmpfilename=\"$tmpfilename\"!!\nPerhaps the directory does not exist... Look carefully at the filename and make sure the directory exists too.\n");
	binmode GENREINDEX, ":encoding(UTF-8)";
	foreach my $currentgenre (sort keys %GENRE) {
		if ($currentgenre eq "") { next; }
		$currentgenre4access = $currentgenre;
		$currentgenre4access =~ s/\//--/;
		$currentgenre4access =~ s/:/- /;

		#DEBUG: print "\n[X1X1X] currentgenre = $currentgenre / 4access = $currentgenre4access";

		@tmpfilelist = sort keys %{$GENRE{$currentgenre}};
		foreach my $tmpfile (@tmpfilelist) {

			#f ((%{$ATTRIBUTES{"genre-".$currentgenre}}->{$tmpfile} >= 1) || (%{$GENRE{$currentgenre}}->{$tmpfile} >= 1)) {
			if ((  $ATTRIBUTES{"genre-".$currentgenre} ->{$tmpfile} >= 1) || (  $GENRE{$currentgenre} ->{$tmpfile} >= 1)) {
				#f ($tmpfile ne "") { print GENREINDEX $currentgenre . "::::" . &osslash($tmpfile) . "\n"; }
				if ($tmpfile ne "") { print GENREINDEX $currentgenre . "::::" .          $tmpfile  . "\n"; }
			}
		}
	}
	close(GENREINDEX);
	&write_genre_list;
}#endsub write_genre_index
########################################################################################################################################


########################################################################################################################################
sub write_artist_index {
	#if ($NO_GENRE_PROCESSING_WHATSOEVER) { return; }
	&log("\n*** Writing index of artists to $ARTIST_LIST ...");
	my $tmpfilename = $ARTIST_LIST;
	open (INDEX, ">$tmpfilename") || &death("could not open [13B] (tmpfilename=$tmpfilename)!!\nPerhaps the directory does not exist... Look carefully at the filename and make sure the directory exists too.\n");
	binmode INDEX, ":encoding(UTF-8)";
		my $current4access="";
		foreach my $current (sort keys %ARTIST) {
			if ($current eq "") { next; }
			$current4access = $current;
			$current4access =~ s/\//--/;
			$current4access =~ s/:/- /;
			#DEBUG: print "\n[XAS1ASXAS1X] current = $current / 4access = $current4access";
			print INDEX "$current\n";
		}
	close(INDEX);
	&write_artist_list();
}
########################################################################################################################################
########################################################################################################################################
sub write_album_index {
	#if ($NO_GENRE_PROCESSING_WHATSOEVER) { return; }
	&log("\n*** Writing index of albums to $ALBUM_LIST ...");
	my $tmpfilename = $ALBUM_LIST;
	open (INDEX, ">$tmpfilename") || &death("could not open [13C] $tmpfilename!!\nPerhaps the directory does not exist... Look carefully at the filename and make sure the directory exists too.\n");
	binmode INDEX, ":encoding(UTF-8)";
		my $current4access="";
		foreach my $current (sort keys %ALBUM) {
			if ($current eq "") { next; }
			$current4access = $current;
			$current4access =~ s/\//--/;
			$current4access =~ s/:/- /;
			#DEBUG: print "\n[X2AA2X] current = $current / 4access = $current4access";
			print INDEX "$current\n";
		}
	close(INDEX);
	&write_album_list();
}
########################################################################################################################################
########################################################################################################################################
sub write_song_index {
	#if ($NO_GENRE_PROCESSING_WHATSOEVER) { return; }
	&log("\n*** Writing index of songs to $SONG_LIST ...");
	my $tmpfilename = $SONG_LIST;
	open (INDEX, ">$tmpfilename") || &death("could not open [13D] $tmpfilename!!\nPerhaps the directory does not exist... Look carefully at the filename and make sure the directory exists too.\n");
	binmode INDEX, ":encoding(UTF-8)";
		my $current4access="";
		foreach my $current (sort keys %SONG) {
			if ($current eq "") { next; }
			$current4access = $current;
			$current4access =~ s/\//--/;
			$current4access =~ s/:/- /;
			#DEBUG: print "\n[X2SASX] current = $current / 4access = $current4access";
			print INDEX "$current\n";
		}
	close(INDEX);
	&write_song_list();
}
########################################################################################################################################




##########################################################################################################################################
sub initial_command_line_processing {  #command line processing   #command-line processing
  &log("\n*** Processing command line options...");
  if (@ARGV==0) { &usage; &death("[DEATH1]"); }
  foreach my $tmparg (@ARGV) {
    #DEBUG: #print "\n* Processing argument: $tmparg";
    #DEBUG: #print "\nif ($tmparg =~ /^-i/i) ";
    if ($tmparg =~ /^-i/i) {
        #DEBUG: print "\nWe have a match! -i!";
        $INI = $tmparg; $INI =~ s/^-i//i;
        if (-e $INI) { print "\n* Using INI file: $INI"; }
        else         { &death("\n* Could not find specified INI file: $INI\n"); }
    } else {
        #DEBUG: print "\nNo match on \"$tmparg\"!";
    }
  }
}#endsub initial_command_line_processing
##########################################################################################################################################

##########################################################################
sub secondpass_command_line_processing {
  if (($ARGV[0] =~ /\?/) || ($ARGV[0] eq "-h") || ($ARGV[0] eq "")) {
      &usage; exit;
  } elsif ($ARGV[0] =~ /^-t$/i) {     #trim directories & extensions off filelist
      &trimdirofffilelist; exit;
  } elsif ($ARGV[0] =~ /^-c$/i) {     #convert manual list into separate attribute files in the appropriate directories
      &convertstaticlisttobatfile; exit;
  } elsif ($ARGV[0] =~ /^-n$/i) {     #create new attribute list
      &newattributelist; exit;
  } elsif ($ARGV[0] =~ /^-r/i) {      #creates DAT (and GenreLST) files in metaattrib dir
      &require_ini;
      my $DO_ALL = 0;
      if  ($ARGV[0] =~ /^-r$/)     { $DO_ALL=1; }
      if  ($ARGV[0] =~ /^-r[0-9]/) { $DO_ALL=0; }
      if (($ARGV[0] =~ /1/) || ($DO_ALL)) { &find_all_files_and_lists; }
      else { &readfilenamesfromfileindex; }
      if (($ARGV[0] =~ /2/) || ($DO_ALL) || (!-e $GENRE_INDEX)) { &create_genre_filelists(1); &write_genre_index; &write_artist_index; &write_album_index; &write_song_index; }
      else { &readgenredatafromgenreindex; }
      if (($ARGV[0] =~ /3/) || ($DO_ALL) || (!-e $DATE_INDEX))  { 
		  &gather_file_dates; &write_file_dates_index; 
	  } else { 
	      &readdatedatafromdateindex("fred");	#fred is for debugging
	  }
	  #ohohoh maybe this should be a GOTO? that goes to after indexing... / 20081123,yrs later: Wouldn't I just need to return to do that??
      exit;
  } elsif ($ARGV[0] =~ /^-p$/i) {
      &dashp_option;				#this option was never finished
      goto DONE;
  } elsif ($ARGV[0] =~ /^-q/i) {
      &require_ini;
      if ($ARGV[0] =~ /^-q$/i) { &death("Incorrect usage -- -q option must be followed by 1 or more numbers.\nRun $0 with no options to display usage help.\n"); }
      if ($ARGV[0] =~ /1/) { $SKIP_FILEFIND=1; }
      if ($ARGV[0] =~ /2/) { $SKIP_GENRE=1; }
      if ($ARGV[0] =~ /3/) { $SKIP_DATE=1; }
      if ($ARGV[0] =~ /4/) { $IGNORE_BASE_ATTRIBUTE_FILE=1; }
      #if ($ARGV[0] =~ /5/) { }
  } elsif ($ARGV[0] !~ /^-g$/) {
      ##### At this point, if they haven't specified -g they don't know what they
      ##### are doing.  So we tell them their options.
      &usage;
  }
}#endsub secondpass_command_line_processing
##########################################################################

#############################################################################
sub require_ini {
#ASSUMES $INI is set to the ini filename, if any
if (($INI eq "") || (!-e $INI)) { &death("\n\nFATAL ERROR: an INI file is required."); }
}#endsub require_ini
#############################################################################

##########################################################################################
sub some_sanity_checks {
	my $tmpfiledir;
	##### DOUBLE-CHECK EXISTENCE OF COLLECTION DIRS:
	if (!$SKIP_ERROR_COLLECTION_MISSING) { 
		foreach $FILEDIR (@COLLECTIONS) {
			$tmpfiledir = &osslash($FILEDIR);
			if (!-d "$tmpfiledir") { &death("The folder $FILEDIR specified in your collections list does not\nexist. Please check the definition of this variable in the script.  It should be set to all the directories that you would like to scan.\n"); }
		}#endfor
	}#endif
	if (!-d "$ATTRIBUTELIST_DIR") { &death("The folder $ATTRIBUTELIST_DIR specified at the top of the source code does no nexist. Please re-set this variable.\nexample: my \$ATTRIBUTELIST_DIR=\"c:/mp3/filelists\";\n"); }
	if (!-d  "$METAFILELIST_DIR") { &death("The folder  $METAFILELIST_DIR specified at the top of the source code does not exist. Please re-set this variable.\nexample: my \$METAFILELIST_DIR=\"c:/mp3/filelists\";\n"); }
}#endsub some_sanity_checks
##########################################################################################

################################################
sub remove_leading_and_trailing_spaces {
  my $s = $_[0];
  $s =~ s/^\s+//g;
  $s =~ s/\s+$//g;

  return($s);

}#endsub remove_leading_and_trailing_spaces
################################################

###################################################################################
sub find_the_files {
	my $tmptype="";
	my $tmpsize="";


	if ($SKIP_FILEFIND==1) {
			&log("\n*** QUICKMODE: Skipping finding of files...\t(skip_filefind=1)");
	        &readfilenamesfromfileindex;
	        &readattribnamesfromfileindex;
	        &readgenredatafromgenreindex;
	        #&readdatedatafromdateindex("wilma");		#wilma is for debugging
	} else {
	        &find_all_files_and_lists;
	}#endif
	
	##### Building list of all files:
	&log("\n*** Building internal list of files...");
	foreach my $tmpfile (@files) {
	    if (($DEBUG_META>15)||($DEBUG_EVERYTHING)) { print "\n** DEBUG: Setting \%{\$ATTRIBUTES{everything}}->{$tmpfile}=1;"; }
	    #%{$ATTRIBUTES{everything}}->{$tmpfile}=1;
	       $ATTRIBUTES{everything} ->{$tmpfile}=1;
		$tmpsize = &GetFileSize($tmpfile); 	
		$tmptype = &TypeOfFile($tmpfile);

		$TOTAL_BYTES_INDEXED += $tmpsize;
		if ($tmptype eq "audio") {
			$TOTAL_BYTES_INDEXED_AUDIO+=$tmpsize;
			$TOTAL_FILES_INDEXED_AUDIO++;
		} elsif ($tmptype eq "image") {
			$TOTAL_BYTES_INDEXED_IMAGE+=$tmpsize;
			$TOTAL_FILES_INDEXED_IMAGE++;
		} elsif ($tmptype eq "video") {
			$TOTAL_BYTES_INDEXED_VIDEO+=$tmpsize;
			$TOTAL_FILES_INDEXED_VIDEO++;
		} elsif ($tmptype eq "text") { 
			$TOTAL_BYTES_INDEXED_TEXT+=$tmpsize;
			$TOTAL_FILES_INDEXED_TEXT++;
		} else {
			$TOTAL_BYTES_INDEXED_OTHER+=$tmpsize;
			$TOTAL_FILES_INDEXED_OTHER++;
		}
	}#endforeach


	my @tmpkeys = keys %{$ATTRIBUTES{everything}};
	my $numFound = @tmpkeys;
	&log("\n*** Attributable/Total Files Found: $numFound/$numEncountered in $numEncounteredDirs dirs");
	$stat_num_index=$numFound;
	$stat_num_found=$numEncountered;
	$stat_num_dir_e=$numEncounteredDirs;

	##### Display all attribute lists if debug flag is turned on:
	if ($DEBUG_DISPLAY_ALL_ATTRIBUTE_LIST_FILENAMES>0) { my $iiii=0; foreach my $filename (@attributelists) { $iiii++; print $iiii . ": " . $filename . "\n"; } }
}#endsub find_the_files
###################################################################################

########################################################################################################################################################
sub read_ini {
	# ASSUMES $INI is the filename of an existing INI file
	my $line   = "";
	my $option = "";
	my $value  = "";
	local $linenum=0;
	
	if ($INI eq "") {
	    if ($REQUIRE_INI) { &death("\n\nFATAL ERROR: INI file required!"); }
	    else              { return; }
	}
	

	# 1) reset values from default [just in case]
	@COLLECTIONS = ();	
	@EXTENSIONS  = ();
	
	# 2) open & read values from INI file:
	open(INI,"$INI") || &death("\nFATAL ERROR: Could not open INI file $INI !\n");
				binmode INI, ":encoding(UTF-8)";
	my $oldvalue;
	while($line=<INI>) {
	    ##### Get line, skip if necessary or sanity check it:
	    $linenum++;
	    if (($line =~ /^#/) || ($line !~ /=/)) { next; }      #skip comments & lines without a "="
	
	    ##### Preprocess line:
	    chomp $line;
	    ($option,$value)=split(/=/,"$line");
	    $option = &remove_leading_and_trailing_spaces($option);														if ($option eq "") { &death("\n\n*** FATAL ERROR: No option given for value \"$value\"  in INI file $INI on line $linenum!\n"); }
	    $value  = &remove_leading_and_trailing_spaces($value );														if ($value  eq "") { &death("\n\n*** FATAL ERROR: No value given for option \"$option\" in INI file $INI on line $linenum!\n"); }
	    if ($value =~ /\$ENV/) {									#evaluate any environment variables
			my $oldvalue=$value; 
			$value = eval $value;				#sheer brilliance!
			&log("\n[DEBUG-ENVVAR: evaluated & modified value of \"$oldvalue\" is \"$value\"]");
		}        																									if ($value eq "") { &death("\n\n*** FATAL ERROR: Value given for option \"$option\" in INI file $INI on line $linenum is invalid.  Perhaps it is an environment variable that does not exist! Value = \"$value\" line=\"$line\""); }
		if ($USE_BACKSLASHES_INSTEAD_OF_SLASHES) { $value =~ s/\//\\/g; }
		else                                     { $value =~ s/\\/\//g; }

	
	    if ($option =~ /^COLLECTION$/i) {
			if (!$SKIP_ERROR_COLLECTION_MISSING) { &checkdir($value,"Collection"); }
	        &logprint("\n* Adding collection: $value");
	        push(@COLLECTIONS,$value);
	    } elsif ($option =~ /^POTENTIAL_COLLECTION$/i) {
			#Same as COLLECTION but without insisting the folder exists
			&logprint("\n* ");
			if (-d $value) {
				push(@COLLECTIONS,$value);
			} else {
				&logprint("NOT ");
			}
			&logprint("Adding potential collection: $value");
	    } elsif ($option =~ /^UNIX$/i) {
	        &checkboolean($value,"UNIX");

	        if ($value) { &log("\n* Operating system: UNIX"   ); }
	        else        { &log("\n* Operating system: Windows"); }

	        $UNIX=$value;
	    } elsif ($option =~ /^PROCESS_GENRES$/i) {
	        &checkboolean($value,"Genre processing");
	        if ($value) { 
	            &log("\n* Genre processing: On");  
	            $NO_GENRE_PROCESSING_WHATSOEVER=0; 
	            use MP3::Tag;					#we wont need this package unless Genre Processing is on
	        } else { 
	            &log("\n* Genre processing: Off"); 
	            $NO_GENRE_PROCESSING_WHATSOEVER=1; 
	        }#endif
	    } 
		elsif ($option =~ /^EXTENSION$/i                         ) { &log("\n* Adding extension: $value");   push(@EXTENSIONS,$value);	    } 
		elsif ($option =~ /^ATTRIBUTELIST_DIR$/i                 ) { $ATTRIBUTELIST_DIR                  = $value; &checkdir ($value,"Attribute filelist"     ); &log("\n* Attribute filelists will be written in:\t$ATTRIBUTELIST_DIR");	        } 
		elsif ($option =~ /^METAFILELIST_DIR$/i                  ) { $METAFILELIST_DIR                   = $value; &checkdir ($value,"Meta-attribute filelist"); &log("\n* Meta-attribute filelists will be written in:\t$METAFILELIST_DIR");       } 
		elsif ($option =~ /^DATEFILELIST_DIR$/i                  ) { $DATEFILELIST_DIR                   = $value; &checkdir ($value,"Dated filelist"         ); &log("\n* Dated filelists will be written in:\t\t$DATEFILELIST_DIR");	            } 
		elsif ($option =~ /^GENREFILELIST_DIR$/i                 ) { $GENREFILELIST_DIR                  = $value; &checkdir ($value,"Genre filelist"         ); &log("\n* Genre filelists will be written in:\t\t$GENREFILELIST_DIR");	            } 
		#TODO never bothered to define any configurability for artist/album/song indexes, they just followed the GENRE index values
		elsif ($option =~ /^BASE_ATTRIBUTE_FILE$/i               ) { $BASE_ATTRIBUTE_FILE                = $value; &checkfile($value,"Base attribute"         ); &log("\n* Using base attribute file:\t\t\t$BASE_ATTRIBUTE_FILE");	                } 
		elsif ($option =~ /^META_ATTRIBUTE_FILE$/i               ) { $META_ATTRIBUTE_FILE                = $value; &checkfile($value,"Meta attribute"         ); &log("\n* Using meta attribute file:\t\t\t$META_ATTRIBUTE_FILE");	                } 
		elsif ($option =~ /^PREFIX_ATTRIB_FILELISTS$/i           ) { $ATTRIB_PREFIX                      = $value;                                               &log("\n* Prefixing  attribute filelist filenames with \"$ATTRIB_PREFIX\"");       } 
		elsif ($option =~ /^PREFIX_META_FILELISTS$/i             ) { $META_PREFIX                        = $value;                                               &log("\n* Prefixing    meta    filelist filenames with \"$META_PREFIX\"");	        } 
		elsif ($option =~ /^PREFIX_DATE_FILELISTS$/i             ) { $DATE_PREFIX                        = $value;                                               &log("\n* Prefixing    dated   filelist filenames with:\t\"$DATE_PREFIX\"");       } 
		elsif ($option =~ /^PREFIX_DATE_RANGE_FILELISTS$/i       ) { $DATE_RANGE_PREFIX                  = $value;                                               &log("\n* Prefixing date range filelist filenames with:\t\"$DATE_RANGE_PREFIX\"");	} 
		elsif ($option =~ /^PREFIX_GENRE_FILELISTS$/i            ) { $GENRE_PREFIX                       = $value;                                               &log("\n* Prefixing    genre   filelist filenames with \"$GENRE_PREFIX\"");	    } 
		elsif ($option =~ /^SKIP_MONTH_TIMESLICING$/i            ) { $SKIP_MONTH_TIMESLICING             = $value;                                               &log("\n* Setting 'skip months, days, and hours timeslicing' to:\t$value");	    } 
		elsif ($option =~ /^SKIP_DAYS_AND_HOURS_TIMESLICING$/i   ) { $SKIP_DAYS_AND_HOURS_TIMESLICING    = $value;                                               &log("\n* Setting 'skip days and hours timeslicing' to:\t\t\t$value");	            } 
		elsif ($option =~ /^FILELIST_EXTENSION$/i                ) { $filelistextension                  = $value;                                               &log("\n* Setting filelist extension to: $value");	                                } 
		elsif ($option =~ /^USE_BACKSLASHES_INSTEAD_OF_SLASHES$/i) { $USE_BACKSLASHES_INSTEAD_OF_SLASHES = 1;                                                    &log("\n* Using backslashes in filelists instead of slashes."); 	                } 
		elsif ($option =~ /^SKIP_ERROR_COLLECTION_MISSING$/i)      { $SKIP_ERROR_COLLECTION_MISSING      = $value;                                               &log("\n* Skipping 'collection missing' errors.");                                 } 		
		elsif ($option =~ /^SKIP_INVERSE_LIST$/i                 ) { $SKIP_INVERSE_LIST                  = $value;                                               &log("\n* Inverse attribute list will "); 	        if (!$value) { &log("NOT "); }   &log("be created."         ); } 
		elsif ($option =~ /^SKIP_FILEMATCH_ERRORS$/i             ) { $SKIP_FILEMATCH_ERRORS              = $value;                                               &log("\n* Attributes not matching files will "); 	if (!$value) { &log("NOT "); }   &log("be logged as errors."); }
	    #}elsif ($option =~ /^$/i) {
	    else { &death("\n\n*** FATAL ERROR: Unknown option of \"$option\" with value of \"$value\" encountered in INI file $INI line $linenum!\n"); }
	
	}
	close(INI);
	
	##### These values are based indirectly on the INI (due to metafilelist_dir):
	$FILE_INDEX        	= &osslash($METAFILELIST_DIR . "/FILES.DAT"      ); #no reason to ever change this unless you already have a        files.dat you want in that directory for some odd reason
	$ATTRIB_LIST_INDEX 	= &osslash($METAFILELIST_DIR . "/ATTRIBFILES.DAT"); #no reason to ever change this unless you already have an attribfiles.dat you want in that directory for some odd reason
	$ATTRIBUTE_LIST 	= &osslash($METAFILELIST_DIR . "/ATTRIBUTES.LST" );	#no reason to ever change this unless you already have an  attributes.lst you want in that directory for some odd reason
	$ATTRIBUTE_DB 		= &osslash($METAFILELIST_DIR . "/ATTRIBUTES.DAT" );	#no reason to ever change this unless you already have an  attributes.dat you want in that directory for some odd reason
	$GENRE_INDEX       	= &osslash($METAFILELIST_DIR . "/GENRES.DAT"     ); #no reason to ever change this unless you already have a       genres.dat you want in that directory for some odd reason
	$GENRE_LIST        	= &osslash($METAFILELIST_DIR . "/GENRES.LST"     ); #no reason to ever change this unless you already have a       genres.lst you want in that directory for some odd reason
	$ARTIST_LIST        = &osslash($METAFILELIST_DIR . "/ARTISTS.LST"    ); #no reason to ever change this unless you already have a      artists.lst you want in that directory for some odd reason
	$ALBUM_LIST         = &osslash($METAFILELIST_DIR . "/ALBUMS.LST"     ); #no reason to ever change this unless you already have a       albums.lst you want in that directory for some odd reason
	$SONG_LIST          = &osslash($METAFILELIST_DIR . "/SONGS.LST"      ); #no reason to ever change this unless you already have a        songs.lst you want in that directory for some odd reason
	$DATE_INDEX        	= &osslash($METAFILELIST_DIR . "/DATES.DAT"      ); #no reason to ever change this unless you already have a        dates.lst you want in that directory for some odd reason
	$STATS_INDEX       	= &osslash($METAFILELIST_DIR . "/STATS.DAT"      );	#no reason to ever change this unless you already have a        stats.dat you want in that directory for some odd reason
	$INVERSE_INDEX     	= &osslash($METAFILELIST_DIR . "/INVERSE.DAT"    ); #no reason to ever change this unless you already have an     inverse.dat you want in that directory for some odd reason
	$INVERSE_INDEX_2   	= &osslash($METAFILELIST_DIR . "/INVERSE2.DAT"   );	#no reason to ever change this unless you already have an    inverse2.dat you want in that directory for some odd reason
	$TRIGGER_FILE		= &osslash($METAFILELIST_DIR . "/TRIGGER.TRG"    );	#no reason to ever change this unless you already have a      trigger.trg you want in that directory for some odd reason
	$TODO_FILE			= &osslash($METAFILELIST_DIR . "/TODO.DAT"       );	#no reason to ever change this unless you already have a         todo.dat you want in that directory for some odd reason
	$ACCESS_INDEX		= &osslash($METAFILELIST_DIR . "/ACCESS.DAT"     );	#no reason to ever change this unless you already have an      access.dat you want in that directory for some odd reason
	$COLLECTION_INDEX	= &osslash($METAFILELIST_DIR . "/COLLECTIONS.DAT");	#no reason to ever change this unless you already have a  collectoins.dat you want in that directory for some odd reason
	$LOG                = &osslash($METAFILELIST_DIR . "/INDEXER.LOG"    );	#no reason to ever change this unless you already have a      indexer.log you want in that directory for some odd reason
	
	
	&log("\n* Using file_index file "           . "of:\t\t"   . "$FILE_INDEX"       );
	&log("\n* Using attrib_file_index file "    . "of:\t"     . "$ATTRIB_LIST_INDEX");
	&log("\n* Using date_file_index file "      . "of:\t"     . "$DATE_INDEX"       );
	if (!$SKIP_INVERSE_LIST) { 
		&log("\n* Using inverse attribute index file of:"     . "$INVERSE_INDEX_2"  ); 
	}
	&log("\n* Using stat index "                . "of:\t\t\t" . "$STATS_INDEX"      );
	&log("\n* Using attribute index "           . "of:\t\t"   . "$ATTRIBUTE_LIST"   );
	&log("\n* Using trigger file "              . "of:\t\t"   . "$TRIGGER_FILE"     );
	&log("\n* Using todo file "                 . "of:\t\t\t" . "$TODO_FILE"        );
	&log("\n* Using access index file "         . "of:\t\t"   . "$ACCESS_INDEX"     );
	&log("\n* Using collections index file "    . "of:\t"     . "$COLLECTION_INDEX" );
	if (!$NO_GENRE_PROCESSING_WHATSOEVER) {
	    &log("\n* Using genre_file_index file " . "of:\t"     . "$GENRE_INDEX"      );
	    &log("\n* Using genre_list file "       . "of:\t\t"   . "$GENRE_LIST"       );
		#TODO mention in logging: our ARTISTS/ALBUMS/SONGS index
	}#endif
}#endsub read_ini
########################################################################################################################################################
###########################################################################
sub dashp_option {			#TODO: never completed
    my $al = $ARGV[1];
    if (-e $al) {
        print "This doesn't work right yet... I never finished this part... don't do this.\n";
        print "Processing the 1 list: $al ... \nThis is for testing purposes only and\nmay not generate the filelists you really want.\n";
        &process_attributelist($al,0,1,1);
    } else { &death("cannot find attribute list $al\n"); }
    print "Done Processing The One List.\n";
}#endsub dashp_option
###########################################################################
#########################################################################################################################################
sub checkdir {
    my $value   = $_[0];
    my $dirtype = $_[1];
    if (!-e $value) { &death("\n\n*** FATAL ERROR: ".$dirtype." directory of \"$value\" does not exist in INI file $INI" . "!"); }
    if (!-d $value) { &death("\n\n*** FATAL ERROR: ".$dirtype." directory of \"$value\" seems to actually be a file, not a directory, in INI file $INI" . "!"); }
}#endsub checkdir
#########################################################################################################################################
#########################################################################################################################################
sub checkfile {
    my $value    = $_[0];
    my $filetype = $_[1];
    if (!-e $value) { &death("\n\n*** FATAL ERROR: ".$filetype." file of \"$value\" does not exist in INI file $INI" . "!"); }
    if ( -d $value) { &death("\n\n*** FATAL ERROR: ".$filetype." file of \"$value\" seems to actually be a directory, not a file, in INI file $INI" . "!"); }
}#endsub checkfile
#########################################################################################################################################

#########################################################################################################################################
sub checkboolean {
    my $value = $_[0];
    my $type  = $_[1];
    if (($value == 1) || ($value == 0)) { return; }
    &death("\n\n*** FATAL ERROR: ".$type." value of \"$value\" needs to be a 0 or 1 in INI file $INI" . "!");
}#endsub checkfile
#########################################################################################################################################
###########################################################################
sub gettimeinfo {

	#### Get current date in YYYYMMDD format for timestampe:
	($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst)=localtime(time); $year+=1900; $mon+=1;
	$NOWYYYYMMDDHHSS = sprintf("%04u%02u%02u%02u%02u",$year,$mon,$mday,$hour,$min);
	$NOWYYYYMMDD     = sprintf("%04u%02u%02u"        ,$year,$mon,$mday);
	$NOWYYYY         = sprintf("%04u"                ,$year);
	$NOWMM           = sprintf("%02u"                ,$mon);
	$NOWDD           = sprintf("%02u"                ,$mday);
	$NOWMMDD         = "$NOWMM$NOWDD";
	$NOWHH           = $hour;
	$NOWmin          = $min;
	if ($DEBUG_NOW) { print "\n* NOW is: YYYYMMDDHHSS=$NOWYYYYMMDDHHSS,YYYYMMDD=$NOWYYYYMMDD,YYYY=$NOWYYYY,MM=$NOWMM,DD=$NOWDD,HH=$NOWHH,min=$NOWmin\n"; }
}#endsub gettimeinfo
###########################################################################


###########################################################################################################################################
sub checkvaliddate {
	### This sub is a prime candidate to be migrated to the Clio::Date library!
	### Though the future-checking should be an option.. ie {allowfuture=>0}
	### Also maybe a check for allowable lengths. . .

	my $date  = $_[0];
	#ASSUMES $when exists and $linenum exists -- see calls to this function to realize why
	my $when2 = $_[1];		#only used for debugging
	my $DEBUG = 0;			#

	my $verbose=0;
	if ($verbose || $DEBUG) { print "\n* Checking $date for validity.\n"; }
	my ($yyyy,$mm,$dd,$hour,$min) = ("","","","","");

	if ($DEBUG) {	print "[S1] prescrub date is \"$date\"\n"; }
	$date =~ s/ish$//ig;						#a date like "1989ish" must be considered simply "1989" for these purposes. no "ish"-isms!
	$date =~ s/([0-9][0-9][0-9][0-9])s$/$1/ig;	#a date like "1990s" must be considered simply "1990" for these purposes. no "s"-isms!
	$date =~ s/ *\(spring\)//ig;				#seasons are often appended to a date, and interfere with the validation process
	$date =~ s/ *\(pring\)//ig;					#why does this happen?
	$date =~ s/ *\(summer\)//ig;				#seasons are often appended to a date, and interfere with the validation process
	$date =~ s/ *\(ummer\)//ig;					#why does this happen?
	$date =~ s/ *\(fall\)//ig;					#seasons are often appended to a date, and interfere with the validation process
	$date =~ s/ *\(autumn\)//ig;				#seasons are often appended to a date, and interfere with the validation process
	$date =~ s/ *\(early\)//ig;					#often appended to a date, and interfere with the validation process
	$date =~ s/ *\(mid\)//ig;					#often appended to a date, and interfere with the validation process
	$date =~ s/ *\(late\)//ig;					#often appended to a date, and interfere with the validation process
	if ($DEBUG) {	print "[S2] postscrub date is \"$date\"\n"; }

	##### CHECK THAT DATE LENGTH IS A VALID LENGTH:
	my $length=length($date);
	if (($length != 8) && ($length != 12) && ($length != 4) && ($length != 3) && ($length != 5) && ($length != 6) && ($length != 10)) { &death("\n\nFATAL TAG ERROR: [1]invalid date length of $length $when\nThe date given is \"$date\", and this is not the right length\nValid lengths are 8 for YYYYMMDD-style dates and 12 for YYYYMMDDHHSS-style dates\nYour tag's length was $length\n"); }

	##### UNFORTUNATELY WE MUST ALLOW SOME WEIRD LENGTHS, FOR THINGS TAGGED IN THE DISTANT PAST OR FUTURE:
	if ($length == 3) {			#we will allow 3-year dates due to musuems and tagging things during historical dates. 
		if ($date !~ /^[1-9][0-9]{2}$/) { &death("FATAL TAG ERROR: [6] Invalid 3-digit date."); 	}
		return 1;
	}
	if ($length == 5) {			#we will allow 3-year dates due to musuems and tagging things during historical dates. 
		if ($date !~ /^[1-9][0-9]{4}$/) { &death("FATAL TAG ERROR: [6] Invalid 5-digit date."); 	}
		return 1;
	}

	##### BUT 99.99% OF DATES WILL FALL IN THE 1900s OR 2000s:
	if ($length >= 4) {			#if it has a year, validate it
		$date =~ /^(....)/;		
		($yyyy)=$1;
		##### Validate year:
		my $premsg = "\n\nFATAL TAG ERROR: [2] invalid year of $yyyy in date \"$date\" $when (line=$linenum)";
		if ($yyyy < 0) { &death("$premsg ... This program only works after Christ. Get back in your time machine and go back to the future."); }
		###### I changed my mind - after 15yrs of using this script I have found I really do want to future-date things sometimes: 
		#if ($yyyy > $NOWYYYY) { &death("$premsg ... Files cannot be dated in the future!  Current year is $NOWYYYY.  Do not tag files with a year greater than this!"); }
	}
	#5 digit dates like "1980s" just get truncated and treated like 1980.
	#5 digit dates like "40000" (Yes, some things are future dated, like the Hello Kitty year 40,000 picture) are also valid:
	#it's either that, or make it 1985 (to be in the *center* of the 1980s), but that requires extra programming
	if ($length >= 6) {			#if it has a month, validate it
		$date =~ /^(....)(..)/;		
		($yyyy,$mm)=($1,$2);
		##### Validate month:
		$premsg = "\n\nFATAL TAG ERROR: [3] invalid month of $mm in date \"$date\" $when (line=$linenum)";
		if  ($mm <   1) { &death("$premsg .. Months must be positive!"); }
		if  ($mm >= 13) { &death("$premsg... \nMonths must be in the range of 00-12!\n"); }
		if (($mm > $NOWMM) && ($yyyy >= $NOWYYYY)) { &death("$premsg ... Files cannot be dated in the future!  Current date is $NOWYYYYMMDD.  Do not tag files after this date!"); }
	}
	if ($length >= 8) {			#if it has a day, validate it
		if ($date !~ /^[0-9][0-9][0-9][0-9][01][0-9][0-3][0-9]/) {
			&death("\n\nFATAL TAG ERROR: [4] invalid date of $date does not fit YYYYMMDD format $when (line=$linenum)\nPerhaps you have an invalid month or day value.\n"); 
		}
		$date =~ /^(....)(..)(..)/;		
		($yyyy,$mm,$dd)=($1,$2,$3);

		##### Validate day:
		my $last_day_of_month=&last_day_of_month($mm,$yyyy);		
		$premsg = "\n\nFATAL TAG ERROR: [5] invalid day of $dd in date \"$date\" $when (line=$linenum) (when=$when) (when2=$when2)";
		if ($dd < 1) { &death("$premsg .. Days must be positive!"); }
		if (($dd > $NOWDD) && ($yyyy >= $NOWYYYY) && ($mm >= $NOWMM)) { &death("$premsg ... Files cannot be dated in the future!  Current date is $NOWYYYYMMDD.  Do not tag files after this date!\n"); }
		if ($dd > $last_day_of_month)  { &death("$premsg...\nThe last day of month $mm in year $yyyy is $last_day_of_month.\nSince this date does not exist in our calendar system, this tag is invalid!\n"); }
	}
	if ($length >= 10) {			#if it has an hour, validate it
		$date =~ /^........(..)/;		
		$hour=$1;
		##### Validate hour:
		$premsg = "\n\nFATAL TAG ERROR: [6] invalid hour of $hour in date \"$date\" $when (line=$linenum)";
		if ($hour < 0) { &death("$premsg... \nHours must be non-negative!\n"); }
		if ($hour >= 24) { &death("$premsg... \nHours must be in the range of 00-23!\n"); }
		if ($verbose>1) {
			if ($hour > $NOWHH) { print "\nHour greater $when (line=$linenum)"; }
			if ($dd >= $NOWDD) { print "\nDD greater $when (line=$linenum)"; }
			if ($yyyy>=$NOWYYYY) { print "\nYYYY greater $when (line=$linenum)"; } else { print "\nYYYY less! $yyyy"; }
			if ($mm>=$NOWMM) { print "\nmm greater $when (line=$linenum)"; }
		}#endif DEBUG

		if (($hour > $NOWHH) && ($dd >= $NOWDD) && ($yyyy >= $NOWYYYY) && ($mm >= $NOWMM)) { 
			&death("$premsg ... \nFiles cannot be dated in the future!\nCurrent date & time is $NOWYYYYMMDDHHSS.\nDo not tag files with a date/time that occurrs after this date!\n"); 
		}
	}
	if ($length >= 12) {			#if it has a minute, validate it
		if ($date !~ /^[0-9][0-9][0-9][0-9][01][0-9][0-3][0-9][0-2][0-9][0-5][0-9]/) {
			&death("\n\nFATAL TAG ERROR: [7] invalid date of $date does not fit YYYYMMDDHHSS format (error is probably in the HHSS part) $when (line=$linenum)\n"); 
		}
		$date =~ /^(....)(..)(..)(..)(..)/;
		($hour,$min)=($4,$5);
		if ($verbose>1) { print "\nhour=$hour,nowhh=$NOWHH,when=$when (line=$linenum)"; }

		##### Validate minute:
		$premsg = "\n\nFATAL TAG ERROR: [8] invalid minute of $min in date \"$date\" $when (line=$linenum)";
		if ($min < 0) { &death("$premsg .. Minutes must be non-negative!"); }
		# i had to put the NOWmin+$LONGEST... $NOWmin because there would sometimes be errors if a DATE NOW tag was used due to stuff taking longer than a minute to execute...
		if (($min > ($NOWmin+$LONGEST_POSSIBLE_EXECUTION_OF_THIS_SCRIPT_IN_MINUTES)) && ($hour >= $NOWHH) && ($dd >= $NOWDD) && ($yyyy >= $NOWYYYY) && ($mm >= $NOWMM)) { 
			&death("$premsg ... \nFiles cannot be dated in the future!\nCurrent date & time is $NOWYYYYMMDDHHSS.\nDo not tag files with a date/time that occurrs after this date!\n"); 
		}
	}
}#endsub checkvaliddate
###########################################################################################################################################


########################################################
sub round {
	my($number) = shift;
	return int($number + .5 * ($number <=> 0));
}#endif
########################################################

########################################################################
#USAGE: &pushhashofarrays(\%HASH,"filename","attribute");
sub pushhashofarrays {
	if ($SKIP_INVERSE_LIST) { return; }


	#kludge to insure attribute prefix is before ALL attributes:
	if ($value !~ /^$ATTRIB_PREFIX/) { $value =~ $ATTRIB_PREFIX . $value; }

	my $hashref = $_[0];
	my $key	= $_[1];
	my $value   = $_[2];
	my %hash 	= %$hashref;
	#my $verbose	= 0;			#

	if (!defined($hashref->{$key})) { 
		$hashref->{$key}=(); 
		if ($verbose) { print "key $key Not defined.\n"; }
	}# else {
	#	if ($verbose) { print "key $key Defined.\n"; }
	#}

	my $arrayref = \@{$hashref->{$key}};

	#if ($verbose) {
	#	print "Arrayref is ".$arrayref ."... \n";
	#	print "Pushing value of $value into key $key ...\n";
	#}#endif

	push(@$arrayref,$value);	
}#endsubpushhash
########################################################################


###############################################################################################################
sub NiceFileSize {
	#USAGE: print &NiceFileSize($bytes);

	my $rate    = $_[0];
	my $options = $_[1];
	my $lprecision = $options->{lprecision};
	my $nice_size;
	if ($lprecision eq "") {$lprecision = 8;}
	if ($rate >= (1024*1024*1024*1024*1024)) {
		--$lprecision;
		$nice_size = sprintf ("%${lprecision}.1fP", ($rate/(1024*1024*1024*1024*1024)));       #petabyte
	} elsif ($rate >= (1024*1024*1024*1024)) {
		--$lprecision;
		$nice_size = sprintf ("%${lprecision}.1fT", ($rate/(1024*1024*1024*1024)));            #terabyte
	} elsif ($rate >= (1024*1024*1024)) {
		--$lprecision;
		$nice_size = sprintf ("%${lprecision}.1fG", ($rate/(1024*1024*1024)));                 #gigabyte
	} elsif ($rate >= (1024*1024)) {
		--$lprecision;
		$nice_size = sprintf ("%${lprecision}.1fM", ($rate/(1024*1024)));                      #megabyte
	} elsif ($rate >= 1024) {
		--$lprecision;
		$nice_size = sprintf ("%${lprecision}.1fK", ($rate/1024));                             #terabyte
	} else {
		$nice_size = sprintf ("%${lprecision}.1f", $rate );                                    #byte
	}#endif
	if ($DEBUG_TOTALS >= 3) { print "short_number($rate)=\"$nice_size\"...<BR>\n"; }
	if ($nice_size =~ /\s+0\.0$/) { $nice_size=sprintf("%${lprecision}s","0"); }
	if ($options->{notrailingzeroes}) { $nice_size =~ s/\.0+//; }
	return ($nice_size);
}#endsub short_number
###############################################################################################################
########################################################################################
sub GetFileSize {
      #($mtime is number of seconds since epoch)
      my ($dev,$ino,$mode,$nlink,$uid,$gid,$rdev,$size,$atime,$mtime,$ctime,

            $blksize,$blocks) = stat($_[0]);
	return($size);
}#endsub GetFileSize
########################################################################################


#########################################################################################################################
sub dienumdaysbackoverflow {
my $a = <<__EOF__;
ERROR: Went too many days back in subroutine create_date_filelists.

       This may happen if you dated a file a date that is in the future.
       Is \"$tmpdate\" a date in the future?  If so, bad tagging.
       You didn't get it tomorrow.  Tomorrow hasn't happened yet.
       It's probably a typo.

       (went back $num_days_back days before quitting)
__EOF__
&death($a);
}#endsub dienumdaysbackoverflow
#########################################################################################################################


############################################################
sub create_stat_index {
	#these values are synced with &get_index_data in the photo album view.pl
	my $tmpfilename=$STATS_INDEX;
	&log("\n*** Creating stat      index $STATS_INDEX...");
	open (STATS, ">$tmpfilename") || &death("could not open [26] inverse index of \"$tmpfilename\"!!\nPerhaps the directory does not exist... Look carefully at the filename and make sure the directory exists too.\n");
	binmode STATS, ":encoding(UTF-8)";
	print STATS "# Statistics generated on $NOWYYYYMMDDHHSS\n\n";
	print STATS "TOTAL_FILES_ENCOUNTERED=$stat_num_found\n";
	print STATS "TOTAL_FILES_INDEXED=$stat_num_index\n";
	print STATS "TOTAL_DIRS_ENCOUNTERED=$stat_num_dir_e\n";
	print STATS "TOTAL_BYTES_INDEXED=$TOTAL_BYTES_INDEXED\n\n";

	print STATS "TOTAL_BYTES_AUDIO=$TOTAL_BYTES_INDEXED_AUDIO\n";
	print STATS "TOTAL_FILES_AUDIO=$TOTAL_FILES_INDEXED_AUDIO\n\n";

	print STATS "TOTAL_FILES_VIDEO=$TOTAL_FILES_INDEXED_VIDEO\n";
	print STATS "TOTAL_BYTES_VIDEO=$TOTAL_BYTES_INDEXED_VIDEO\n\n";

	print STATS "TOTAL_FILES_IMAGE=$TOTAL_FILES_INDEXED_IMAGE\n";
	print STATS "TOTAL_BYTES_IMAGE=$TOTAL_BYTES_INDEXED_IMAGE\n\n";

	print STATS "TOTAL_FILES_TEXT=$TOTAL_FILES_INDEXED_TEXT\n";
	print STATS "TOTAL_BYTES_TEXT=$TOTAL_BYTES_INDEXED_TEXT\n\n";

	print STATS "TOTAL_FILES_OTHER=$TOTAL_FILES_INDEXED_OTHER\n";
	print STATS "TOTAL_BYTES_OTHER=$TOTAL_BYTES_INDEXED_OTHER\n\n";

	close(STATS);

	##### Also do todo file:
	&log("\n*** Creating TODO list in    $TODO_FILE...");

	open (TODO, ">$TODO_FILE") || &death("could not open [26.B] todo file of $TODO_FILE");
	binmode TODO, ":encoding(UTF-8)";
	foreach my $todo (@TODO) { print TODO &osslash($todo); }
	close(TODO);
}#endsub create_stat_index
############################################################
#########################################################################
sub TypeOfFile {
	#copied from Clio::File... may need to be periodically updated
	#USAGE: $type = &TypeOfFile($filename); 

	#RETURNS: "audio", "video", "image", "text"

	my $file = $_[0];
	my $extension = &GetExtension($file);

	if ($extension eq "jpg") { return "image"; }
	if ($extension eq "avi") { return "video"; }

	if ($extension eq "gif") { return "image"; }
	if ($extension eq "bmp") { return "image"; }

	if ($extension eq "mp3") { return "audio"; }

	if ($extension eq "wav") { return "audio"; }
	if ($extension eq "qt")  { return "video"; }

	if ($extension =~ /^mpe?g$/i) { return "video"; }
	if ($extension eq "jpeg")    { return "image"; }

	if ($extension eq "doc") { return "text"; }
	if ($extension =~ /html?/) { return "text"; }
	if ($extension =~ /txt/) { return "text"; }
	if ($extension =~ /mht/) { return "text"; }

	return "unknown";
}#endsub TypeOfFile
#########################################################################
####################################################################
sub GetExtension {
	#copied from Clio::File
	#USAGE:	$extension = &GetExtension($fullfilename);	#returns "AVI" for example
	my $fullfilename = $_[0];
	my $returnvalue = $fullfilename;
	$returnvalue =~ s/^.*\.([^\.]+)$/$1/;
	$returnvalue =~ tr/[A-Z]/[a-z]/;
	return $returnvalue;
}#endsub GetExtension

####################################################################

########################################################################
sub create_trigger_file {
	open(TRIGGER,">$TRIGGER_FILE") || &death("ERROR: Could not open trigger file $TRIGGER_FILE... This is not mission critical but may hurt the situation if something (ie a database) is supposed to react to this file's existence...");
	print TRIGGER "\n\n# This file is a trigger.  It serves no other purpose than to exist as a flag that the filelists have been generated ...\n\n";
	close(TRIGGER);
}#endsub create_trigger_file
########################################################################

#What is the purpose of this trigger?
#To trigger the import these values into a database of course!
#However, using bcp.exe is better because you don't have to be constantly checking for this trigger file.
#The following stored procedure checks for the trigger file
#(you have to edit to include the path, notice the "d:\www\lists\trigger.trg" below)
#If it exists, it imports the data into the server named 'FIRE' (my computer's name),
#using the DTS called "Import Media Album Attributes".  This is a DTS that I set up
#to import the data into a table caleld "Media_Attributes" in the database called
#"FireWWW".  You can import the DTS file that I saved to disk and with very little
#modification, get it working.  Then create this stored procedure (make sure to
#edit the @triggerfilename).  Then set up a job to run the stored procedure
#every minute...  There is 0 cpu hit if the trigger file does not exist.
#If it does exist, the data is imported, and the trigger file deleted.
#This causes the database to automatically be updated within 1 minute of
#this program's completetion!   However, it's much better to simply not
#use the trigger file and learn to use bcp.exe to import it yourself into SQL
#Server anyway!

#CREATE PROCEDURE trigger_media_attributes_import  AS
#
#declare @exists int 
#declare @triggerfilename varchar(128)
#declare @dts varchar(128)
#declare @command varchar(256)
#
#set @triggerfilename = 'd:\www\lists\trigger.trg'
#set @dts = '"Import Media Album Attributes"'
#
#exec master..xp_fileexist @triggerfilename,@exists output
#
#if @exists = 1
#begin
#	print 'File ' +  @triggerfilename + ' Exists! ... Starting DTS'
#	set @command = 'dtsrun -S FIRE -N ' + @dts + ' -E'
#	exec master..xp_cmdshell @command	
#	print 'Deleting trigger file ' + @triggerfilename
#	set @command = 'del ' + @triggerfilename
#	exec master..xp_cmdshell @command	
#

#end
#else
#begin
#	print 'File ' + @triggerfilename + ' DOES NOT EXIST!  Not importing . . . .'
#end
#GO

######################################################################## 

###########################################################################
sub findattriblists {
    #ASSUMES @attributelists=();
    foreach my $currentCollection (@COLLECTIONS) {
        &log("\n*** Finding attribute lists in $currentCollection ... ");
        push(@attributelists,&quickfilefind($currentCollection,"attrib.lst\$")); #the \$ at end removes files named attrib.lst~~ and such
        &log(@attributelists . " found");
    }
}#endsub findattriblists
###########################################################################
###########################################################################
sub writeattriblists {
	my $tmpfilename = $ATTRIB_LIST_INDEX;
	open (ATTRIBINDEX, ">$tmpfilename") || &death("could not open [9] $tmpfilename!!\nPerhaps the directory does not exist... Look carefully at the filename and make sure the directory exists too.\n");
	binmode ATTRIBINDEX, ":encoding(UTF-8)";
	$i = 0;
	&log("\n*** Writing attribute file index $ATTRIB_LIST_INDEX ... ");
	foreach my $file (@attributelists) { print ATTRIBINDEX $file . "\n"; $i++; }
	print "($i lists written to file) ";
close(ATTRIBINDEX);
}#endsub writeattriblists
###########################################################################

	
########################################################################################################
sub get_date_value_from_attribute_or_date {
	my $file=$_[0];	

	##### Get the attribute DATE tag value, if any:
	#y $value = %{$ATTRIBUTES{DATE}}->{$file};
	my $value =   $ATTRIBUTES{DATE} ->{$file};
	
	##### If no date was tagged, use the file's creation date, gathered earlier:
	if ($value eq "") { $value = $FILEKEY_YYYYMMDDHHDATEVALUE{$file}; }


	### SPECIAL DATA NOTE: currently, these are using the FILEKEY_YYYYMMDDHH variable,
	###		because our max precision is to the hour. but if later we want to extend
	###		that to the minute or second, we need to change this variable to match
	###		that precision, ie $FILEKEY_YYYYMMDDHHMMDATEVALUE 
	###					  or $FILEKEY_YYYYMMDDHHMMSSDATEVALUE


	return($value);
}#endsub get_date_value_from_attribute_or_date
########################################################################################################

############################################################################
sub create_attribute_index {
	my %HASH		= %{$_[0]};			#our %ATTRIBUTES has
	my $tmpfilename	= $ATTRIBUTE_LIST;
	my $tmp			= "";
	my @lines		= ();
	#ASSUMES $ATTRIBUTE_LIST is defined
	#ASSUMES %ATTRIBUTES hash

	&log("\n*** Creating attribute list $ATTRIBUTE_LIST...");
	foreach my $tmpkey (sort keys %HASH) {		#the sort takes time, but makes a prettier file that could theoretically be binary searched
		if ($tmpkey =~ /^DATE$/) {			#date is special, as it really links into another whole tree of attributes
			my @keys=();

			##### First we must process the specific date attributes (YYYY,YYYYMM,YYYYMMDD,YYYYMMDDHH[,YYYYMMDDHHMM,YYYYMMDDHHMMSS])
			@keys=keys %DATE_ATTRIBUTES_WRITTEN;
			foreach my $datekey (@keys) { 
				$tmp = "$DATE_PREFIX$datekey";
				if ($tmp =~ /^$ATTRIB_PREFIX/) { $tmp =~ s/^$ATTRIB_PREFIX//; }
				#$tmpaccess = $ATTRIBUTES_BY_ACCESS{$datekey} || SECURITY_LEVEL_DEFAULT;#push(@lines,"$tmp|$tmpaccess\n");					#let's stop doing the security level printout
				push(@lines,"$tmp\n");								
			}#endforeach
		
			##### Then we must process the date-RANGE attributes: (basically the same block of code as above, perhaps i shoudl just push all the keys into one array)
			@keys = sort keys %DATE_RANGE_ATTRIBUTES_WRITTEN;	#short enough to sort
			foreach my $datekey (@keys) { 
				#print INDEX "$DATE_RANGE_PREFIX$INTERVALS{$datekey}\n"; 	#print INDEX "$DATE_RANGE_PREFIX$datekey\n";			#$tmp="$DATE_RANGE_PREFIX" . "$INTERVALS{$datekey}"; 
				$tmp = $datekey;
				if ($tmp =~ /^$ATTRIB_PREFIX/) { $tmp =~ s/^$ATTRIB_PREFIX//; }
				#$tmpaccess = $ATTRIBUTES_BY_ACCESS{$datekey} || SECURITY_LEVEL_DEFAULT; #push(@lines,"$tmp|$tmpaccess\n");					#let's stop doing the security level printout
				push(@lines,"$tmp\n"); 
			}#endforeach
		} else {
			if (%{$ATTRIBUTES{$tmpkey}} ne "") {
				$tmp = keys %{$ATTRIBUTES{$tmpkey}};
			} else {
				$tmp = 0;
			}
			#DEBUG: print "\n NUM KEYS for $tmpkey is $tmp ....";
			if ($tmp > 0) {	#this keeps attributes with 0 files that match them from showing up in our attribute index
				#$tmpaccess = $ATTRIBUTES_BY_ACCESS{$tmpkey} || SECURITY_LEVEL_DEFAULT;#push(@lines,"$tmpkey|$tmpaccess\n");				#let's stop doing the security level printout
				$tmpaccess = $ATTRIBUTES_BY_ACCESS{$tmpkey} || SECURITY_LEVEL_DEFAULT;
				push(@lines,"$tmpkey\n");
			}
		}#endif
	}#endforeach

	##### Now that we have determined our attributes, spit it out in a sorted fashion:
	open (INDEX, ">$tmpfilename")  || &death("could not open [27] attribute index of \"$tmpfilename\"!!\nPerhaps the directory does not exist... Look carefully at the filename and make sure the directory exists too.\n");
	binmode INDEX, ":encoding(UTF-8)";
		foreach my $line (sort @lines) { print INDEX $line; }
	close(INDEX);



	##### 2016: Decided a more full database of all our conclusions in one place might make sense to have:

	&log("\n*** Creating attribute database $ATTRIBUTE_DB...");
	open (INDEX, ">$ATTRIBUTE_DB") || &death("could not open [28] attribute db of \"$ATTRIBUTE_DB\"!!\nPerhaps the directory does not exist... Look carefully at the filename and make sure the directory exists too.\n");
	binmode INDEX, ":encoding(UTF-8)";
		#### More readable:
		#foreach $tmpfile (@files) {
		#		print INDEX "$tmpfile\n";
		#		foreach $tmpattribute (keys %ATTRIBUTES) {
		#			print INDEX "    $tmpattribute\n";
		#			foreach $tmpfilename (keys %{$ATTRIBUTES{$tmpattribute}}) { print INDEX "        $tmpfilename\n"; }
		#		}
		#}
		#### More parseable:
		foreach $tmpattribute (keys %ATTRIBUTES) {							#print INDEX "$tmpattribute\n";
			foreach $tmpfilename (keys %{$ATTRIBUTES{$tmpattribute}}) {		#print INDEX "    $tmpfilename\n";
				#tmpvalue=%{$ATTRIBUTES{$tmpattribute}}->{$tmpfilename};
				$tmpvalue=  $ATTRIBUTES{$tmpattribute} ->{$tmpfilename};
				print INDEX "$tmpattribute:$tmpfilename:$tmpvalue\n";
			}
		}
	close(INDEX);


}#endsub create_attribute_index
############################################################################

################################################################################
sub RemapSecurityLevelWordToNumber {
	if    ($_[0] =~ /^friend$/i)   		{ return SECURITY_LEVEL_FRIEND   	; }
	if    ($_[0] =~ /^closefriend$/i)	{ return SECURITY_LEVEL_FRIEND_CLOSE; }
	elsif ($_[0] =~ /^family$/i)   		{ return SECURITY_LEVEL_FAMILY   	; }
	elsif ($_[0] =~ /^familyonly$/i)	{ return SECURITY_LEVEL_FAMILY   	; }
	elsif ($_[0] =~ /^admin$/i)    		{ return SECURITY_LEVEL_ADMIN    	; }
	elsif ($_[0] =~ /^intimate$/i) 		{ return SECURITY_LEVEL_INTIMATE 	; }
	elsif ($_[0] =~ /^public$/i)   		{ return SECURITY_LEVEL_STRANGER 	; }
	elsif ($_[0] =~ /^private$/i) 		{ return SECURITY_LEVEL_NOBODY		; }
	elsif ($_[0] =~ /^temp-private$/i) 	{ return SECURITY_LEVEL_STRANGER	; }		#temp-private is really only for flickr use!
	elsif ($_[0] =~ /^nobody$/i) 		{ return SECURITY_LEVEL_NOBODY		; }
	else  { &death("Unknown security level of $_[0] encountered!"); }
}#endsub RemapSecurityLevelWordToNumber
################################################################################


########################################################################################################################################################
sub create_access_index {
	my %HASH			= %{$_[0]};			#the access levels hash %FILES_BY_ACCESS
	my $tmpfilename	= $ACCESS_INDEX;
	my $tmp			= "";
	my @lines			= ();
	#ASSUMES $ACCESS_INDEX is defined
	#ASSUMES const SECURITY_LEVEL_DEFAULT
	&log("\n*** Creating access    index $tmpfilename...");

	foreach my $tmpkey (keys %ALLFILES) {									#foreach file encountered
		if ($ALLFILES{$tmpkey} >= 2) {										#if it's of a valid extension
			#DEBUG:		#print "\nChecking access for $tmpfile...";
			if (defined $HASH{$tmpkey}) {									#and an access level is defined 
				push(@lines,"$tmpkey|$HASH{$tmpkey}\n");					#then take write down that access level
			} else {		
				push(@lines,"$tmpkey|" . SECURITY_LEVEL_DEFAULT . "\n");	#take down the default access level
			}#endif
		}#endif
	}#endforeach

	##### Now that we have determined our attributes, spit it out in a sorted fashion:
	open (INDEX, ">$tmpfilename")  || &death("could not open [29] access index of \"$tmpfilename\"!!\nPerhaps the directory does not exist... Look carefully at the filename and make sure the directory exists too.\n");
	binmode INDEX, ":encoding(UTF-8)";
	foreach my $line (sort @lines) { print INDEX $line; }
	close(INDEX);
}#endsub create_access_index
########################################################################################################################################################



##########################################################################################
sub create_inverse_index_OLD {
	if ($SKIP_INVERSE_LIST) { return; }
	my $hashref	 = $_[0];						#\%INVERSE_ATTRIBUTES
	my %HASH	 = %$hashref;
	my $verbose	 = 0;		#
	my @tmparray = ();


	my $tmpfilename  = $INVERSE_INDEX;
	my $tmpfilename2 = $INVERSE_INDEX_2;
	my $linenum=0;
	my %printed=();

	#OHOHOH: I'm going to try not generating inverseindex1 just to see if that helps speed it up a bit...

	&log("\n*** Creating inverse attribute index...");
	#: open (INVERSEINDEX, ">$tmpfilename")  || &death("could not open [25] inverse index \#1 of \"$tmpfilename\"!!\nPerhaps the directory does not exist... Look carefully at the filename and make sure the directory exists too.\n");
	open (INVERSEINDEX2,">$tmpfilename2") || &death("could not open [29] inverse index \#2 of \"$tmpfilename2\"!!\nPerhaps the directory does not exist... Look carefully at the filename and make sure the directory exists too.\n");
	binmode INVERSEINDEX2, ":encoding(UTF-8)";
	foreach my $tmpkey (sort keys %HASH) {		#the sort takes time, but makes a prettier file that could theoretically be binary searched
		#if ($verbose) { print "Processing key=$tmpkey,tmparray=".\@tmparray.":\n"; }
		#: print INVERSEINDEX $tmpkey . "|";

		@tmparray=@{$HASH{$tmpkey}};
		%printed=();
		foreach my $member (@tmparray) {		# remove sorting for speedup!
			$linenum++;
			if ($printed{$member}==1) { next; }
			if ($member =~ /^$ATTRIB_PREFIX/) { $member =~ s/^$ATTRIB_PREFIX//; }
			###if (($verbose) ||(1)) { print "\t=> (tmpkey=$tmpkey) value=$member\n"; }
			#: print INVERSEINDEX $member . ":";
			print INVERSEINDEX2 "$tmpkey|$member\n";
			$printed{$member}=1;
		}#endforeach
		#: print INVERSEINDEX "\n";
	}#endforeach
	#: close(INVERSEINDEX);
	close(INVERSEINDEX2);
}#endsub create_inverse_index_OLD
##########################################################################################

######################################################################################################
sub GetContentsOfDirectory {				#from Clio::File
	#USAGE:	($filesArrayRef,$subdirsArrayRef) = &GetContentsOfDirectory($dir,{extensions=>\@extensions});
	my $dirname 	= $_[0];
	my $options 	= $_[1];
	my @extensions	= ();
	if (defined($options->{extensions})) { @extensions = @{$options->{extensions}}; }
	my @files 	= ();
	my @subdirs	= ();
	my $entity	= "";
	my $tmp		= "";
	my $tmp2		= "";


	#DEBUG:print &tabledump("extensions",\@extensions);#


	opendir(DIR, $dirname) or &death("FATAL ERROR: can't open directory \"$dirname\": $!");
	while (defined($entity = readdir(DIR))) { 
		next if ($entity =~ /^\.{1,2}/);
		$tmp = "$dirname/$entity";
		#DEBUG:print "tmp is $tmp<BR>";	#
		if  (-f $tmp) { 
			if (@extensions > 0) {
				$tmp2 = &GetExtension($tmp);
				foreach my $tmpext (@extensions) {
					#DEBUG:print "Checking $tmp2 for $tmpext . . . ";#
					if ($tmp2 =~ /^$tmpext$/i) { push(@files,$tmp); last; }
				}
			} else {
				push(@files,$tmp); 
			}#endif
		}
		elsif (-d $tmp) { push(@subdirs,$tmp); }
		else {
			&log("WARNING: unknown entity of $tmp in dir $dirname...\n");
		}#endeif
	}#endwhile
	closedir(DIR);
	return \@files, \@subdirs;
}#endsub GetContentsOfDirectory
######################################################################################################


##################################################################################################################################################################
sub process_each_attribute_list {
	local $linenum="";
	local $fileRegex="";
	local $fileRegexes="";
	local $attriblist="";
	local @tmpfilelist="";
	local @regexes=();
	local $yyyyvalue;
	local $yyyymmvalue;
	local $yyyymmddvalue;
	local $yyyymmddhhvalue;
	local $verbose=0;		
	local @attributes=();
	local $value;
	local $datevalue;
	local $datemode;
	local $tmpout="";

	##### Process each attribute list to learn attributes:
	&log("\n\n*** Processing ".@attributelists." attribute lists...\n");					#processing attribute lists,processing x attribute lists
	if (($DEBUG>=5)||($DEBUG_LIST_ALL_ATTRIBUTE_LISTS_BEING_PROCESSED)) { foreach my $a (@attributelists) { &log("\t[LIST=$a]\n"); } }
	my $list=0;

	my $total=@attributelists;

	foreach my $a (sort @attributelists) { 
		$list++; 
		#print "."; 
		if (($list > $MAX_LISTS) && ($MAX_LISTS > 0)) { return; }
		&process_attributelist($a,0,$list,$total); 
	}
	&dump_attribute_weights("process_each_attribute_list BEFORE base attribute file");
		if (!$IGNORE_BASE_ATTRIBUTE_FILE) { &process_attributelist($BASE_ATTRIBUTE_FILE,1,1,1);                       }
		else                              { &log("\n*** Ignoring base attribute list $BASE_ATTRIBUTE_FILE"."...\n");  }
	&dump_attribute_weights("process_each_attribute_list after base attribute file");
}#endsub process_each_attribute_list
##################################################################################################################################################################


##################################################################################################################
sub dump_attribute_weights {
	my $trace=$_[0];
	##### debug stuff:
	if ($DEBUG_ATTRIBUTE_WEIGHTS > 1) {
		&log("\n");
		my $tmpval;
		foreach my $key (sort keys %ATTRIBUTE_WEIGHTS) {
			$tmpval=$ATTRIBUTE_WEIGHTS{$key};
			if ($tmpval != 1) {
				&log("[$trace][ATTRIBUTE_WEIGHTS NON-1-VALUES DUMP: VALUE=".$tmpval.",\tKEY=$key]\n");
			}
		}
	}
}
##################################################################################################################


######################################################################################
sub create_attribute_filelists {            #1stpass
	#USAGE: &create_attribute_filelists(\%ATTRIBUTES);			
#    my $aref = $_[0];
#    my %ATTRIB = %{$aref};
#    my @attriblist = sort keys %ATTRIB;
    my @attriblist = sort keys %ATTRIBUTES;
    my $tmpfile = "";
    my $tmpfile2= "";
    my $filesfound = 0;
    my $tmpfilelist = "";
    my @tmpfilelist = ();
	my $linesprinted;
	my $tmpWeight;
	my $timestoprint;	
	my $roll;
	my $tmpval;
	my ($before,$after);
	my $currentattribClean="";
	my $tmpfilelistclean="";
    if ($filelistextension eq "") { $filelistextension="m3u"; }

	&dump_attribute_weights("create_attribute_flielists");

	##### Let them know what's going to happen:
    &log("\n*** Writing attribute filelists...\n");
    &log("\n\tFiles\tLines\tAttribute");
    &log("\n\t=====\t=====\t=========");

    $firstpassfilelists = @attriblist;
    my $num_lists_created=0;
	if ((0)||($DEBUG_META)) { &log("\n*********POTENTIAL DEBUG: \@attriblist is: [".join("] [",@attriblist)."] ****************\n"); }	#DEBUG #
	my $logstring="";
    foreach my $currentattrib (@attriblist) {
        if ($DEBUG_META>5) { &log("\n****** Looping through \$currentattrib=\"$currentattrib\"..."); }
        #next if $currentattrib eq "everything";		#I used to think this was a good idea. Really, it doesn't matter unlesss meta generation fails for some reason.
        next if $currentattrib =~ /^DATE[\s\-]/i;		#Date attributes are handled separately
        next if $currentattrib =~ /^DATE$/i;			#Date attributes are handled separately
        next if $currentattrib =~ /^GENRE-/i;			#Genre attributes are handled separately
        next if $currentattrib =~ /^postcaption-/i;     #caption attributes are for uploading/image-index only
        next if $currentattrib =~ /^caption-/i;			#caption attributes are for uploading/image-index only

		#clean it out, including any slashes
		$SKIP_SLASH_CONVERSION=0; $currentattribClean = &clean_name_for_filenames($currentattrib); $SKIP_SLASH_CONVERSION=0;

        if ($DEBUG_META>5) { &log("Proceeding!"); }
        $num_lists_created++;
        $tmpfilelist = "$ATTRIBUTELIST_DIR/$ATTRIB_PREFIX" . $currentattribClean . "." . $filelistextension;
		$tmpfilelist =~ s/[\r\n\t]//g;					#last minute fixes
		#BAD IDEA!!!!  $tmpfilelist =~ s/:/-/g;			#can't happen, but just in case
        @tmpfilelist = sort keys %{$ATTRIBUTES{$currentattrib}};
        $filesfound=0;        
		$linesprinted=0;
		if (@tmpfilelist > 0) {
			$SKIP_SLASH_CONVERSION=1;										#we need slashes because we've put them in this filename!
			$tmpfilelistclean = &clean_name_for_filenames($tmpfilelist);
			$SKIP_SLASH_CONVERSION=0;
			open (LIST,">$tmpfilelistclean")
			  || &death("\n\nFATAL ERROR 2G1: could not create filelist \"$tmpfilelist\"\n" .
					 "Perhaps you need to redefine \$ATTRIBUTELIST_DIR at the top of the source code...\nLook carefully at the filename and make sure any directories needed already exist.\nIt is currently: \"$ATTRIBUTELIST_DIR\" \n\n");
			binmode LIST, ":encoding(UTF-8)";
			foreach $tmpfile (@tmpfilelist) {	
			
				#f (%{$ATTRIBUTES{$currentattrib}}->{$tmpfile} >= 1) 
				if (  $ATTRIBUTES{$currentattrib} ->{$tmpfile} >= 1) {
					##### GET WEIGHT:
					$tmpWeight = $ATTRIBUTE_WEIGHTS{"$tmpfile$DELIMITER$currentattrib"};			if ($DEBUG_ATTRIBUTE_WEIGHTS) { &log("\n\t[TW1][$currentattrib][\$tmpWeight = \$ATTRIBUTE_WEIGHTS{\"$tmpfile$DELIMITER$currentattrib\"}; = " . $ATTRIBUTE_WEIGHTS{"$tmpfile$DELIMITER$currentattrib"} . "]"); }
					if ($tmpWeight eq "") { $tmpWeight=1; }											if ($DEBUG_ATTRIBUTE_WEIGHTS) { &log("\n\t[TW1][$currentattrib][\$tmpWeight=$tmpWeight now]"); }

					##### MASSAGE FILENAME & KEEP TRACK OF TOTAL FILES:
					$filesfound++;				
					#if ($USE_BACKSLASHES_INSTEAD_OF_SLASHES) { $tmpfile =~ s/\//\\/g; } else { $tmpfile =~ s/\\/\//g; }

					##### CALCULATE NUMBER OF TIMES WE PRINT THIS ONE: 
					$timestoprint=1;
					if  ($tmpWeight < 1) {									#say the weight is 0.1 = we want it 10% of the time = so we roll rand(1) and if it's less than .1 we do it:
						$roll = rand(1);
						if ($roll > $tmpWeight) { $timestoprint=0; } 
						else                    { $timestoprint=1; } 
						if ($DEBUG_ATTRIBUTE_WEIGHTS) { &log("[roll of $roll for weight $tmpWeight means timesToPrint now=$timestoprint]"); }
					} elsif ($tmpWeight > 1) {
						$timestoprint = $tmpWeight;
						if ($tmpWeight =~ /\./) {			#5.9 would mean timestoprint is 5 + roll against 0.9
							($before,$after)=split(/\./,$tmpWeight);
							$timestoprint=$before;
							$roll = rand(1);
							if ($roll <= ".$after") { $timestoprint++; } 
						}
					}
					if (($DEBUG_ATTRIBUTE_WEIGHTS) && ($tmpWeight != 1)) { &log("\t[tmpWeight=$tmpWeight,roll=$roll]\n\t[*timestoprint*=$timestoprint for tmpfile=$tmpfile]\n"); }

					##### PRINT TO PLAYLIST CORRECT NUMBER OF TIMES (& KEEP TRACK):
					if ($timestoprint == 0) {
						#%{$ATTRIBUTES{$currentattrib}}->{$tmpfile}=0;				#remove from internal data structure so meta-attributes don't pick this file up as being part of this attribute anymore -- a use case that was making it so removing something from an attribute a certain percentage of the time would remove it from meta-attributes comprised of that attribute 0% of the time. Really, if a file is removed from an attribute based on probability, it also should not appear in a meta-attribute that is comprised of that attribute (unless explicitly added by a side effect of some other unrelated directive, of course)
						   $ATTRIBUTES{$currentattrib} ->{$tmpfile}=0;				#remove from internal data structure so meta-attributes don't pick this file up as being part of this attribute anymore -- a use case that was making it so removing something from an attribute a certain percentage of the time would remove it from meta-attributes comprised of that attribute 0% of the time. Really, if a file is removed from an attribute based on probability, it also should not appear in a meta-attribute that is comprised of that attribute (unless explicitly added by a side effect of some other unrelated directive, of course)
						#elete %{$ATTRIBUTES{$currentattrib}}->{$tmpfile};			#DEBUG: &logprint("\n----------------------------------------------\%{\$ATTRIBUTES{$currentattrib}}->{".$tmpfile."}=0=(sanity)".%{$ATTRIBUTES{$currentattrib}}->{$tmpfile}.";--------------------------------------");#
						delete   $ATTRIBUTES{$currentattrib} ->{$tmpfile};			#DEBUG: &logprint("\n----------------------------------------------\%{\$ATTRIBUTES{$currentattrib}}->{".$tmpfile."}=0=(sanity)".%{$ATTRIBUTES{$currentattrib}}->{$tmpfile}.";--------------------------------------");#
					} else {
						for ($i=1; $i<=$timestoprint; $i++) {
							print LIST $tmpfile . "\n"; $linesprinted++;            if ($DEBUG_ATTRIBUTE_WEIGHTS) { &log("[printing because \$i=$i]"); }						
						}
					}
				}#endif
			}#endforeach
			close(LIST);
		}
		&log("\n\t" . sprintf("%5u",$filesfound) . "\t" . sprintf("%5u",$linesprinted) . "\t" . $currentattrib);
    }#endforeach attribute list


	###OHOH - would this be faster if i went file-by-file instead of attribute-by-attribute???
	###i could just flat out write the data to INVERSE2.DAT (skip inverse1.dat) ....

	&log("\n\n*** Generating access attributes...\n");
	my $tmpout="";
	foreach my $currentattrib (@attriblist) {
		###### At this point, $currentattrib is the attribute WITHOUT $ATTRIB_PREFIX prefix. Yippie!

		#DEBUG:
		#if ($DEBUG_META>5) { 
		#	print "\n[X4Q] Doing current non-meta-attrib $currentattrib ..."; 
		#}

		next if $currentattrib =~ /^DATE[\s\-]/i;                 #Date attributes are handled separately
		next if $currentattrib =~ /^DATE$/i;                      #Date attributes are handled separately
		next if $currentattrib =~ /^GENRE-/i;                    #Genre attributes are handled separately
		next if $currentattrib =~ /^caption-/i;                #caption attributes are handled separately
		next if $currentattrib =~ /^postcaption-/i;        #postcaption attributes are handled separately
		next if $currentattrib eq "everything";		       #speedup

		##### Set the access level for this attribute to ultra-high until we hear of a file that is lower:
		$ATTRIBUTES_BY_ACCESS{$currentattrib} = SECURITY_LEVEL_HIGHEST;
 
		##### Get the list of files, then process it:
		@tmpfilelist = keys %{$ATTRIBUTES{$currentattrib}};
		foreach $tmpfile (@tmpfilelist) {
			#f (%{$ATTRIBUTES{$currentattrib}}->{$tmpfile} >= 1) {
			if (  $ATTRIBUTES{$currentattrib} ->{$tmpfile} >= 1) {
				##### Pretty output for someone watching:
				$tmpout = "$currentattrib: $tmpfile";
				$tmpout = substr($tmpout, 0, $MAX_WIDTH) if length($tmpout) > $MAX_WIDTH;
				print "\r" . " " x $MAX_WIDTH . "\r" . $tmpout;

			#	##### Keep track of inverse attributes:
			#	&pushhashofarrays(\%INVERSE_ATTRIBUTES,$tmpfile,$currentattrib);#			#OHOH

			#DEBUG:print "\nbuh? access{$currentattrib}=$ATTRIBUTES_BY_ACCESS{$currentattrib} .. lowest=".SECURITY_LEVEL_LOWEST."...filesbyaccess{$tmpfile}=$FILES_BY_ACCESS{$tmpfile}";#


				##### Keep track of access level for this attribute:
				if 	($ATTRIBUTES_BY_ACCESS{$currentattrib} > SECURITY_LEVEL_LOWEST) {
					if (!defined $FILES_BY_ACCESS{$tmpfile}) {
						$ATTRIBUTES_BY_ACCESS{$currentattrib} = SECURITY_LEVEL_DEFAULT;
						#DEBUG:print "\n=> Lowering access level for attribute $currentattrib to DEFAULT level of ".SECURITY_LEVEL_DEFAULT."!";		
					} elsif ($FILES_BY_ACCESS{$tmpfile} < $ATTRIBUTES_BY_ACCESS{$currentattrib}) {
						$ATTRIBUTES_BY_ACCESS{$currentattrib} = $FILES_BY_ACCESS{$tmpfile};
						#DEBUG:print "\n=> Lowering access level for attribute $currentattrib to $FILES_BY_ACCESS{$tmpfile}!";	#
					}
				}#endif
			}#endif
		}#endforeach
	}#endforeach

	print "\r" . " "  x $MAX_WIDTH;
	print        "\b" x $MAX_WIDTH;

    #print "\n";
    #DEBUG:print @attriblist;#
    $FIRST_REPORT .= "\n*** " . sprintf("%4u",$num_lists_created) . " different std.-filelists were created in $ATTRIBUTELIST_DIR.";
    &log($FIRST_REPORT);

    $TOTAL_ATTRIB_CREATED = @attriblist;
}#endsub create_attribute_filelists
######################################################################################


###############################################################################################################################################################
sub clean_name_for_filenames {	#make filenames safe
	my $s = $_[0];
	$s =~ s/\?/_/g;

	#This part became problematic in 2022 with the post-spotify mp3s that had colons delimiting multiple genres thus
	#creating filenames with lots of colons in them. But we still need the drive letter colon, just not any of the 
	#others. The "/g" option for =~ wouldn't loop properly and needs a while loop around it, unfortunately:
#	$s =~ s/(:.*):/$1- /ig;
#	$s =~ s/^(..)(.*):(.*)$/$1$2--$3/ig;
	while ($s =~ /:.*:/) {
  		$s =~ s/^(..)(.*):(.*)$/$1$2--$3/ig;
    }
	$s =~ s/\*/{ASTERISK}/g;
	$s =~ s/</((/ig;
	$s =~ s/>/))/ig;
	$s =~ s/\|/--/ig;
	if ($SKIP_SLASH_CONVERSION != 1) {
		$s =~ s/\//--/g;
		$s =~ s/\\/--/g;
	}
	$s =~ s/\t/     /g;
	$s =~ s/^\-\-//g;					#20131013 - started finding "--*.m3u" in whatever folder I started "index-mp3" in - let's see if cleaning this up here at least makes them named properly, so we can be sure this is the program creating them
	$s =~ s/"/'/g;						#20160420 - person-Bob "Dobbs" was trying to create filenames with quotes in them
	$s =~ s/�/_/g;						#20160525 - some stupid incoming mp3 has this unicode character that can't be a filename
	$s =~ s/�/_/g;						#20160525 - some stupid incoming mp3 has this unicode character that can't be a filename
	$s =~ s//_/g;						#20160525 - some stupid incoming mp3 has this unicode character that can't be a filename

	return($s);
}#endsub clean_name_for_filenames
###############################################################################################################################################################

##########################################################################################
sub create_inverse_index {
	##### This may seem like an INCREDIBLY STUPID way to deal with creating a reverse
	##### lookup table for transforming our attribute=>filename associations into
	##### filename=>attribute associations.  In many ways, this is stupid.  It only
	##### works if the meta prefix and meta dir is the same as the attribute prefix
	##### and attribute dir (So that metas of same name OVERWRITE the attribute file).
	##### Otherwise, if you have an attribute called preferred, and a meta called 
	##### preferred, they would be in separate files, both would be read in here,
	##### and instead of having what is preferred you would have the union of your
	##### non-meta preferred and meta-preferred.  It would not be good.  But as long
	##### as the meta/attribute prefix/dirs are the same, the meta files of same name
	##### overwrite the nonmeta files, and thus the files left at the end are accurate
	##### representations of our attribute=>filename associations.
	##### The reason I started doing it this way was because keeping that information
	##### in memory was SLOOOW.  Each filename had to be stored in a hash, but since
	##### one file can be associated with many attributes, the attributes had to be put
	##### in an array associated with each hash.  The number of operations, and cost of
	##### the memory seek of each of those operations, caused this program to go two to
	##### three times slower than necessary.  This ("the stupid") way simply reads them
	##### from disk and spits them back out again, using almost zero memory operations,
	##### basically only bound by the speed at which the harddrive can be written to.
	##### Although conceptually inferior, this way of doing it is performance-superior!

	if ($SKIP_INVERSE_LIST) { return; }
	my $verbose	 	= 0;		#
	my @tmparray 		= ();
	my @dirs 			= ();
	#my $tmpfilename  	= $INVERSE_INDEX;
	my $tmpfilename2 	= $INVERSE_INDEX_2;
	my $linenum=0;
	my %printed=();
	my $tmpsize="";
	my $tmpfilename="";
	my $i=0;
	my %attribute_files=();
	my @extensions=($filelistextension);
	my ($filesArrayRef,$subdirsArrayRef)=("","");


	##### Check for allowed, but not recommended INI settings that will cause some minor problems with getting accurate data:
	&log("\n*** Creating inverse attribute index...");
	if ($METAFILELIST_DIR ne $ATTRIBUTELIST_DIR) { &log("\nWARNING: METAFILELIST_DIR and ATTRIBUTELIST_DIR are not the same.  Inverse file may be inaccurate!"); }
	if ($ATTRIB_PREFIX    ne $META_PREFIX)       { &log("\nWARNING: PREFIX_META_FILELISTS and PREFIX_ATTRIB_FILELISTS are not the same.  Inverse file may be inaccurate!"); }


	#DEBUG:
	#print "\nMETAFILELISTDIR=$METAFILELIST_DIR,ATTRIBUTELISTDIR=$ATTRIBUTELIST_DIR";
	#print "\nGENRELISTDIR=$GENREFILELIST_DIR,{TO DO ADD ARTIST/ALBUM/SONG LIST},DATELISTDIR=$DATEFILELIST_DIR";
	#print "\nMETAPREFIX=$META_PREFIX,ATTRIBPREFIX=$ATTRIB_PREFIX";
	#print "\nDATEPREFIX=$DATE_PREFIX,DATERANGEPREFIX=$DATE_RANGE_PREFIX,GENRE_PREFIX=$GENRE_PREFIX";
	#


	##### Get the list of files we will be dealing with:
	if (-e $GENREFILELIST_DIR) { push(@dirs,$GENREFILELIST_DIR); }
	push @dirs,$DATEFILELIST_DIR, $ATTRIBUTELIST_DIR, $METAFILELIST_DIR; 
	foreach my $dir (@dirs) {
		($filesArrayRef,$subdirsArrayRef) = &GetContentsOfDirectory($dir,{extensions=>\@extensions});
	}#endforeach

	##### Traverse the list, making sense of each attribute:
	my @files = @{$filesArrayRef};
	foreach $tmpfile (@files) {
		##### See if zero byte file, if it is, erase it, we don't need it:
		$tmpsize=&GetFileSize($tmpfile);
		#DEBUG:print "\nSize for $tmpfile=$tmpsize";#
		if ($tmpsize==0) { 
			#$tmp="$CLEANPRE " . &osslash($tmpfile) . " $CLEANPOST";
			#DEBUG:print "\nabout to: $tmp";#
			#system("$tmp");
			unlink &osslash($tmpfile);
			next;
		}#endif

		##### Otherwise, scrub the filename to get the attribute back out of it:
		$tmpattr = $tmpfile;
		$tmpattr =~ s/\.$filelistextension$//;
		if      ($tmpattr =~ /^$METAFILELIST_DIR/i) {
			$tmpattr =~ s/^$METAFILELIST_DIR[\\\/]*$META_PREFIX//i;
		} elsif ($tmpattr =~ /^$ATTRIBUTELIST_DIR/i) {
			$tmpattr =~ s/^$ATTRIBUTELIST_DIR[\\\/]*$ATTRIB_PREFIX//i;
		} elsif ($tmpattr =~ /^$DATEFILELIST_DIR/i) {
			$tmpattr =~ s/^$DATEFILELIST_DIR[\\\/]*//i;
			$tmpattr =~ s/^$DATE_RANGE_PREFIX//i;
			$tmpattr =~ s/^$DATE_PREFIX//i;
		} elsif ($tmpattr =~ s/^/$GENREFILELIST_DIR/i) {
			$tmpattr =~ s/^$GENREFILELIST_DIR[\\\/]*$GENRE_PREFIX//i;
		}#endif

		##### Store the filename/attribute pair, now that we have it:
		$attribute_files{$i++}={attribute=>$tmpattr,filename=>$tmpfile};
		#DEBUG:print "attribute_files{$i}=$tmpattr,tmpfile=$tmpfile\n";#
	}#endif


	##### Now that we have our filenames, collect all our inverse data .....  
	&log("\n* Writing inverse index.....\n");
	my @inverse_lines=();
	my @tmpkeys = keys %attribute_files;
	my $numkeys = @tmpkeys;
	my $tmp2 = $numkeys - 1;
	for (my $tmpi=0; $tmpi<$numkeys; $tmpi++) {
		print "\r" . " " x $MAX_WIDTH . "\r[ $tmpi / $tmp2 ]";	#tmp2 is just numkeys-1	
		$tmpfilename = $attribute_files{$tmpi}->{filename};
		$tmpattr     = $attribute_files{$tmpi}->{attribute};
		#DEBUG:print "\n* tmpi=$tmpi,tmpfilename=$tmpfilename,tmpattr=$tmpattr";#

		open(TMP,"<$tmpfilename") || &death("could not open [28] attrib file $tmpfilename");
		binmode TMP, ":encoding(UTF-8)";

		while ($tmpline=<TMP>) { 
			chomp $tmpline;
			push(@inverse_lines,"$tmpline|$tmpattr\n"); 
		}#endwhile
		close(TMP);
	}#endforeach

	##### Now that we have collected all our inverse data, spit it out:
	open (INVERSEINDEX2,">$tmpfilename2") || &death("could not open [30] inverse index \#2 of \"$tmpfilename2\"!!\nPerhaps the directory does not exist... Look carefully at the filename and make sure the directory exists too.\n");
	binmode INVERSEINDEX2, ":encoding(UTF-8)";
	foreach my $line (@inverse_lines) { print INVERSEINDEX2 $line; }
	close(INVERSEINDEX2);
}#endsub create_inverse_index(NEW)
##########################################################################################

##########################################################################################
sub create_collection_index {
	my $tmpfilename  	= $COLLECTION_INDEX;
	#ASSUMES array @COLLECTIONS is populated (Read from INI file)
	&log("\n* Creating collection index.....");
	open (COLLECTIONS,">$tmpfilename") || &death("could not open [27] collections index \#2 of \"$tmpfilename\"!!\nPerhaps the directory does not exist... Look carefully at the filename and make sure the directory exists too.\n");
	binmode COLLECTIONS, ":encoding(UTF-8)";
	foreach $tmp (@COLLECTIONS) { print COLLECTIONS "$tmp\n"; print "."; }
	close(COLLECTIONS);
}#endsub create_collection_index
##########################################################################################


######################################################################################
sub process_attributelist {		#1st pass lists sprinkled everywhere (attrib.lst)
	my    $list   = $_[0];
	local $ISBASE = $_[1];			#1 if we are processing the base attribute list
	my    $n      = $_[2];			#the number of this list
	my    $nn     = $_[3];			#the number of total lists
	my ($listdir,$listname)=&splitdirname($list);
	if ($ISBASE) { $listdir="" }		#used this to optimize an if/then that was inside a loop that gets executed for each line of each file :)

	##### Initialize 'local' variables:
	$linenum=0;
	my $newtmpattrib="";
	my $tmpWeight="";

	##### DEBUG STUFF:
	if ($DEBUG_PROCESS_ATTRIBUTELIST_CALLS) { &log("\n\n* DEBUG: process_attributelist [list=$list,ISBASE=$ISBASE,n=$n,nn=$nn]\n"); }

	##### Read the attribute file to memory:
	if ($ISBASE) { &log("\n*** Processing base attribute list $BASE_ATTRIBUTE_FILE...\n"); }
	if ($DEBUG>=4) { &log("* Opening attribute list $list...\n"); }
	if (!open(AL, "$list")) {
		my $errmsg = "\nCould not open [1] attribute list \"$list\"!!\n";
		if ($SKIP_FILEFIND==1) { &log($errmsg); } else { &death($errmsg); }
	}#endif
	binmode AL, ":encoding(UTF-8)";
	my @lines=<AL>;
	close(AL);

	##### Then process it!:
	my $num_lines=@lines;
	foreach $line (@lines) {
		##### Keep track of the line number:
		$linenum++;

		##### If it's "#!nowarn" then we won't flag errors with the line after this one:
		if ($line =~ /^!NoWarningsForNextLine!/i) { $warnings=0; }

		##### If it's a comment, and it has 'question' or 'todo', snag this line for our TODO.DAT file that will be generated:
		if ($line =~ /^#/) {
			if (($line =~ /QUESTION/i) || ($line =~ /TODO/i)) { push(@TODO,"TODO: $list\n\t$line\n\n"); }
			next;
		}#endif

		##### DEBUG CRAP:		#
		if (($DEBUG>=7)||($DEBUG_BASE_ATTRIB_PRINT_EACH_LINE)) { &log("\n* Processing line $linenum ==> \"$line\"\n"); }		#if ($DEBUG>=7) { &log("    Searching for files matching $fileRegexes in $listdir...\n"); }		#if ($ISBASE) { &log("."); }

		##### "whatever:caption-this is a caption" is a way to caption things, and is NOT an attribute, and should be skipped here...
		if (($line =~ /:caption-/) || ($line =~ /:postcaption-/)) { next; }

		##### Lines without a colon -- ie blank lines -- are just plain skipped:
		next if $line !~ /:./; #need a : with something after it..at least



		##### At this point, it's not a comment and it's a command, so lets figure out the RegExFilelist and AttribList for this command:
		chomp $line;
		($fileRegexes,$attriblist)=split(/:/ ,"$line");
		if ($fileRegexes eq "") {  $fileRegexes="."; }

		##### Check for some error conditions:
		if (($line !~ /:caption-/) && ($line !~ /:postcaption-/)) { 
			if ($line =~ /:.+:/) { 			&log("\n**** CRITICAL ERROR C1: 2 non-continuous colons in line $linenum in list $list...\n\tLINE: $line\n\n");
				$line =~ s/(:.*):/$1/g;		#let's fix it and see what happens
			}
			if ($line =~ /:.*\|/) { 		&log("\n**** CRITICAL ERROR C2: 2 Can't have a pipe after a colon in line $linenum in list $list...\n\tLINE: $line\n\n");
				$line =~ s/:(.*)\|/:$1/g;	#let's fix it and see what happens
			}
		}
		if ($line !~ /:/) { &log("\n**** CRITICAL ERROR C3: 0 colons in line $linenum in list $list...\n\tLINE: $line\n\n"); }

		##### Now go through each RegExFileList and process it:
		#OLD: @regexes=("$fileRegexes");#NEWER:@regexes=split(/\|/,"$fileRegexes");
		#NEWEST: 
		@regexes=("$fileRegexes");		#Yes. Back to the original way. Pipe-splitting is done in the filefind function now.
		foreach $fileRegex (@regexes) {
			##### Display progress "meter":[1/1][1/2342]
			$tmpout="[$n/".$nn."][".$linenum."/".$num_lines."] \"$list\" $fileRegex ...";				##print "\r$tmpout" . " " x ($MAX_WIDTH-length($tmpout));
			$tmpout = substr($tmpout, 0, $MAX_WIDTH) if length($tmpout) > $MAX_WIDTH;					##print "\r" . sprintf("%-$MAX_WIDTHs","$tmpout");			#print "\r$tmpout";
			print "\r" . " " x $MAX_WIDTH . "\r$tmpout";												#STDOUT-only prettiness

			##### Find the files that match this regular expression:
			#i optimized out this if/then by adding this line earlier: #if ($ISBASE) { $listdir="." }
			#if (!$ISBASE) {
				@tmpfilelist=&quickfilefind($listdir,$fileRegex);	#OHOHOH this will speed it up but maybe break for some reasons
			#} else {
            #   	@tmpfilelist=&quickfilefind(".",$fileRegex);
			#}#endif

			#### Now we have found any files that match $fileRegex:
			#if ((@tmpfilelist == 0) && (!$ISBASE)) 			#if you don't want warnings to apply to base attribute file . . .
			if (($SKIP_FILEMATCH_ERRORS==0) && (@tmpfilelist == 0) && ($warnings != 0)) {
				if ($ISBASE) { $tmp=" IN BASE ATTRIBUTE FILE"; } else { $tmp=""; }
				if (($fileRegex =~ /^unsorted$/i) || ($fileRegex =~ /^currently[\-\.\*]*judging$/i)) {
					#Then the unsorted folder is simply empty, so it's not actually an error.	
				} else {
					my $CD_COMMAND="cd \"$listdir\"";
					my $FIXCOMMAND="\%EDITOR\% \"$list\"";
					&log("\n\n\nWARNING$tmp: RegEx of /$fileRegex/ at line ***".$linenum."*** of list $list does not match any actual files...\n" 
							. "\tLine: $line\n" 
							. "        $CD_COMMAND\n" 
							. "        $FIXCOMMAND" 
							. "\n\n\n");
				}
			#} elsif (@tmpfilelist > 0) {
			} else {
              	$attriblist =~ tr/[A-Z]/[a-z]/;					#lowercase all attributes	#too bad we have to do this
				if ($attriblist =~ /^caption-/i) {				#12/2007
					@attributes=("$attriblist");
				} else {
					@attributes=split(/,/,"$attriblist");
				}
				$value=""; $datevalue=""; $datemode=0;
				foreach $tmpfile (@tmpfilelist) {				#there was sorting here, but that takes time!
					if ($ALLFILES{$tmpfile}!=2)	{ next; }
					foreach $tmpattrib (@attributes) {

						##### DETERMINE WEIGHT OF ATTRIBUTE:
						if (($tmpattrib =~ /\*/) && ($tmpattrib !~ /caption-/i) && ($tmpattrib !~ /postcaption-/i) && ($tmpattrib !~ /^thing-/i) && ($tmpattrib !~ /^person-/i) && ($tmpattrib !~ /^activity-/i) && ($tmpattrib !~ /^place-/i)) {
							($newtmpattrib,$tmpWeight)=split(/\*/,$tmpattrib);
							if (($tmpWeight !~ /^\d*\.?\d*$/) || ($tmpWeight eq "") || ($tmpWeight eq ".")) {  #validate weight
								&log("\n\nERROR W2: WEIGHT of \"$tmpWeight\" is not valid [tmpattrib=$tmpattrib,newtmpattrib=$newtmpattrib,tmpWeight=$tmpWeight]!\n\t LINE=$line"); 
								$newtmpattrib = $tmpattrib; $tmpWeight=1;
							}	
						} else {
							$newtmpattrib = $tmpattrib;
							$tmpWeight=1;	#default weight
						}

						##### STORE WEIGHT OF ATTRIBUTE, UNLESS NON-1 ATTRIBUTE ALREADY EXISTS:
						#my %ATTRIBUTE_WEIGHTS=();		#key={$filename$delimiter$attribute},value=weight
						if (($DEBUG_ATTRIBUTE_WEIGHTS) && ($tmpWeight != 1)) { &log("\n\n--------[Processing newtmpattrib=$newtmpattrib,tmpWeight=$tmpWeight]"); }
						if (($tmpWeight==1) && ($ATTRIBUTE_WEIGHTS{"$tmpfile$DELIMITER$newtmpattrib"} != 1)) {
							#don't store the new weight if it's "boring ol' 1", which only ever happens automatically, and should not overwrite a manually set weights	
						} else {
							$ATTRIBUTE_WEIGHTS{"$tmpfile$DELIMITER$newtmpattrib"}=$tmpWeight;
						}
						if (($DEBUG_ATTRIBUTE_WEIGHTS) && ($tmpWeight != 1)) { &log(  "\n         *~*~* \$ATTRIBUTE_WEIGHTS{$tmpfile$DELIMITER$newtmpattrib}=\$tmpWeight=".$ATTRIBUTE_WEIGHTS{"$tmpfile$DELIMITER$newtmpattrib"}.";\n"); }

						##### THEN DO EVERYTHING ELSE:
						if    ($newtmpattrib =~ /^\-\-/) { $mode="removestrong"; }
						elsif ($newtmpattrib =~ /^\-/)   { $mode="remove"      ; }
						elsif ($newtmpattrib =~ /^\+\+/) { $mode="addstrongest"; } #same
						elsif ($newtmpattrib =~ /^\+/)   { $mode="addstrong"   ; } #for now
						else                             { $mode="add"         ; }
						$attrib2use = $newtmpattrib;
						$attrib2use =~ s/^[\+\-]+//;        #gotta scrub 1 or more off...
						$attrib2use =~ s/\s+$//;			#attributes should not have trailing spaces
						$attrib2use =~ s/^\s+//;			#attributes should not have  leading spaces
						##### AT THIS POINT, we know our $attrib2use and our $mode

						#BY_ACCESS
						if ($attrib2use =~ /^ACCESS-(.*)$/i) {
							$tmp2 = &RemapSecurityLevelWordToNumber($1);
							$FILES_BY_ACCESS{$tmpfile}=$tmp2;
							#DEBUG:print "\n==> Setting access level to $tmp2 for file $tmpfile...\n";
						} elsif ($attrib2use =~ /^DATE/i) {
							if ($verbose) { &log("\nDATE tag found: $attrib2use"); }
							$datemode=1;
							$datevalue = $attrib2use;
							$datevalue =~ s/^DATE\s+//i;
							if ($datevalue =~ /^NOW$/i) { $datevalue=$NOWYYYYMMDDHHSS; }
							if ($verbose) { &log("==> datevalue: $datevalue\n"); }
							$attrib2use = "DATE";

							#20080910:
							$datevalue =~ s/ to [0-9].*$//i;	$datevalue =~ s/\-*ish//i;
							$datevalue =~ s/s//i;				$datevalue =~ s/\-$//i;
							$datevalue =~ s/ \(early\)//i;		$datevalue =~ s/ \(mid\)//i;
							$datevalue =~ s/ \(later*\)//i;		$datevalue =~ s/ish//;

							##### Halt on invalid dates, make user fix immediately rather than old approach of "fix later":
							&checkvaliddate($datevalue,"in attribute list $list, line number $linenum, tmpfile=$tmpfile");

							##### Clear the OS-level date attributes for this file, since we have overridden it:
							$YYYY_ENCOUNTERED{$FILEKEY_YYYYDATEVALUE{$tmpfile}}--;
							$YYYYMM_ENCOUNTERED{$FILEKEY_YYYYMMDATEVALUE{$tmpfile}}--;
							$YYYYMMDD_ENCOUNTERED{$FILEKEY_YYYYMMDDDATEVALUE{$tmpfile}}--;
							$YYYYMMDDHH_ENCOUNTERED{$FILEKEY_YYYYMMDDHHDATEVALUE{$tmpfile}}--;
							$YYYYMMDDHHMM_ENCOUNTERED{$FILEKEY_YYYYMMDDHHMMDATEVALUE{$tmpfile}}--;
							$YYYYMMDDHHMMSS_ENCOUNTERED{$FILEKEY_YYYYMMDDHHMMSSDATEVALUE{$tmpfile}}--;
							$FILEKEY_YYYYMMDDHHMMSSDATEVALUE{$tmpfile}="";
							$FILEKEY_YYYYMMDDHHMMDATEVALUE{$tmpfile}="";
							$FILEKEY_YYYYMMDDHHDATEVALUE{$tmpfile}="";
							$FILEKEY_YYYYMMDDDATEVALUE{$tmpfile}="";
							$FILEKEY_YYYYMMDATEVALUE{$tmpfile}="";
							$FILEKEY_YYYYDATEVALUE{$tmpfile}="";

							##### Suck yyyy,yyyymm,yyyymmdd,yyyymmddhh values out of yyyymmddhhss,
							##### and generate dummy values if any are missing . . . 
	
							if ($datevalue =~ /^([0-9]{4})/i) { 															#yyyy
								$yyyyvalue="$1"; 
								if ($datevalue =~ /^([0-9]{4})([01][0-9])/i) {												##yyyymm
									$yyyymmvalue="$1$2";
									if ($datevalue =~ /^([0-9]{4})([01][0-9])([0-3][0-9])/i) {								##yyyymmdd
										$yyyymmddvalue="$1$2$3";    #$yyyymmddhhvalue="";#why?
										if ($datevalue =~ /([0-9]{4})([01][0-9])([0-3][0-9])([0-2][0-9])([0-5][0-9])/i) {	##yyyymmddhh
											$yyyymmddhhvalue="$1$2$3$4";
										}   # else { $yyyymmddhhvalue = $yyyymmddvalue . "12"; }    #halfway through the   day
									}       # else { $yyyymmddvalue   = $yyyymmvalue   . "15"; }    #halfway through the month
								}           # else { $yyyymmvalue     = $yyyyvalue     . "06"; }    #halfway through the  year
							}#

							#OHOH -- currently padding these values by putting them in the center of the timeslice
							# another idea is to give "00" as the value, and have them not be processed like that
							#this may create a high concentration of files in, say, June 15th 12:30:30PM (center of all slices moment)
	
							#An old idea that I decided I did not like: Make unspecified time presion centered. Reason I didn't like it: causes stuff to concentrate in the middle of timespans, ie: June 15th 12:30:30
							#if ($yyyymmvalue 		  eq "") { $yyyymmvalue			= $yyyyvalue         . "06"; }
							#if ($yyyymmddvalue		  eq "") { $yyyymmddvalue		= $yyyymmvalue       . "15"; }
							#if ($yyyymmddhhvalue	  eq "") { $yyyymmddhhvalue		= $yyyymmddvalue     . "12"; }
							#if ($yyyymmddhhmmvalue	  eq "") { $yyyymmddhhmmvalue   = $yyyymmddhhvalue   . "30"; }
							#if ($yyyymmddhhmmssvalue eq "") { $yyyymmddhhmmssvalue	= $yyyymmddhhmmvalue . "30"; }
	
							#at this point, every file should have a yyyy/yyyymm/yyyyymmdd/yyyymmddhh value even if it was only tagged to yyyy
		
							#$verbose=1;#
							#if ($verbose) { 
							#	print "\n=> Setting \$YYYYDATEVALUE      {$tmpfile}=$yyyyvalue       & YYYYMM_ENC    {$yyyyvalue}      =1"; 
							#	print "\n=> Setting \$YYYYMMDATEVALUE    {$tmpfile}=$yyyymmvalue     & YYYYMM_ENC    {$yyyymmvalue}    =1";
							#	print "\n=> Setting \$YYYYMMDDDATEVALUE  {$tmpfile}=$yyyymmddvalue   & YYYYMMDD_ENC  {$yyyymmddvalue}  =1";
							#	print "\n=> Setting \$YYYYMMDDHHDATEVALUE{$tmpfile}=$yyyymmddhhvalue & YYYYMMDDHH_ENC{$yyyymmddhhvalue}=1";
							#}


							##### Update our date table with the new date
							$FILEKEY_YYYYDATEVALUE{$tmpfile}           = $yyyyvalue;       
							$FILEKEY_YYYYMMDATEVALUE{$tmpfile}         = $yyyymmvalue;     
							$FILEKEY_YYYYMMDDDATEVALUE{$tmpfile}       = $yyyymmddvalue;   
							$FILEKEY_YYYYMMDDHHDATEVALUE{$tmpfile}     = $yyyymmddhhvalue; 
							$FILEKEY_YYYYMMDDHHMMDATEVALUE{$tmpfile}   = $yyyymmddhhmmvalue; 
							$FILEKEY_YYYYMMDDHHMMSSDATEVALUE{$tmpfile} = $yyyymmddhhmmssvalue; 
							$YYYY_ENCOUNTERED{$yyyyvalue}++;
							$YYYYMM_ENCOUNTERED{$yyyymmvalue}++;
							$YYYYMMDD_ENCOUNTERED{$yyyymmddvalue}++;
							$YYYYMMDDHH_ENCOUNTERED{$yyyymmddhhvalue}++;
							$YYYYMMDDHHMM_ENCOUNTERED{$yyyymmddhhmmvalue}++;
							$YYYYMMDDHHMMSS_ENCOUNTERED{$yyyymmddhhmmssvalue}++;
						} else {
							$datemode=0;
						}#endif

						#### now that we know the mode/data, do it:				
						#f      (($mode eq "add"        ) && (%{$ATTRIBUTES{$attrib2use}}->{$tmpfile} > -1)) {
						if      (($mode eq "add"        ) && (  $ATTRIBUTES{$attrib2use} ->{$tmpfile} > -1)) {
							if ($datemode)	{ $value=$datevalue; }
							else            { $value=1         ; }
							#%{$ATTRIBUTES{$attrib2use}}->{$tmpfile}=$value;
							   $ATTRIBUTES{$attrib2use} ->{$tmpfile}=$value;
						# elsif (($mode eq "remove"     ) && (%{$ATTRIBUTES{$attrib2use}}->{$tmpfile} <  2)) {
						} elsif (($mode eq "remove"     ) && (  $ATTRIBUTES{$attrib2use} ->{$tmpfile} <  2)) {
							if ($datemode)	{ $value=$datevalue; } 
							else            { $value=-1        ; }	#i REALLY want to change this -1 to a 0! but that's *****stupid!*****
							#%{$ATTRIBUTES{$attrib2use}}->{$tmpfile}=$value;
							   $ATTRIBUTES{$attrib2use} ->{$tmpfile}=$value;
						} elsif ($mode eq "removestrong") {
							if ($datemode)	{ $value=$datevalue; } 
							else            { $value=-2        ; }	#deleting the value from the hash table would undermine the concept of a permanent blacklist by losing the blacklisted value of "-2"
							#%{$ATTRIBUTES{$attrib2use}}->{$tmpfile}=$value;
							   $ATTRIBUTES{$attrib2use} ->{$tmpfile}=$value;
						} elsif ($mode eq "addstrong"   ) {
							if ($datemode)	{ $value=$datevalue; }
							else            { $value=2         ; }
							#%{$ATTRIBUTES{$attrib2use}}->{$tmpfile}=$value;
							   $ATTRIBUTES{$attrib2use} ->{$tmpfile}=$value;
						} elsif ($mode eq "addstrongest") {
							if ($datemode)	{ $value=$datevalue; }
							else            { $value=2         ; }
							#%{$ATTRIBUTES{$attrib2use}}->{$tmpfile}=$value;
							   $ATTRIBUTES{$attrib2use} ->{$tmpfile}=$value;
						}
						if (($DEBUG>=7)||(($tmpfile =~ /$DEBUG_FILEWATCH_FILENAME/i))){ &log("\n\t* DEBUG: Applying **$mode** to $attrib2use:  $tmpfile...\n\t\t- based on[G] tmpatr=$newtmpattrib,attrib2use=$attrib2use,mode=$mode,  attr_file=$list\n\t\t- line=>$line\n"); }
					}#endforeach attributes
				}#endforeach file matching regex
			}#endif any files match regex
		}#endforeach regex
		print "\r" . "\b" x ($MAX_WIDTH-length($tmpout));			#STDOUT-only prettyness
		if ($line !~ /^!NoWarningsForNextLine!/i) { $warnings=1; }

	}#endforeach line in the attrib.lst file

	print "\r" . " " x $MAX_WIDTH . "\r";							#STDOUT-only prettyness
}#endsub process_attributelist
######################################################################################


######################################################################################
sub quickfilefind {                         #hopefully this will speed it up
	my $where     		= &regexquote(&osslash($_[0]));
	my $searchforall	= $_[1];
	my $param     		= $_[2];
	my @results   		= ();
	my $searchfor="";
	my $WASFOUND=0;
	#ASSUMES $ALLFILES{filename}=1 for all files encountered.
	if ($where eq "^\.") { $where="."; }							#kludge-fix: fixing some missing regexquoting ended up corrupting one of our semaphores
	if ($DEBUG_QFF) {$i=0;&log("\n\n ---------------- Quickfilefinding for /$searchforall/ in ".$where." ... \%Allfiles has ".(keys %ALLFILES)." files/keys");} #

	#if ($ISBASE){ &log("\n\n\n\n\n\n\nSetting QFF DEBUG back to 0...\n\n\n\n\n\n\n");$DEBUG_QFF=0;}#RUCK

	$searchforall =~ s/\|\|/|/g;																				#we do allow blank regex'es, for instance a line saying ":cheese" is saying to mark the regex of "" {everything} as cheese. But we do NOT allow blanks in between pipes. Those are errors that should be corrected
	my @regexes=split(/\|/,"$searchforall");																	#multiple regex'es are split by "|" in our parlance
	foreach $tmpfname (keys %ALLFILES) {																		#if (($DEBUG_QFF>=8)||($tmpfname =~ /$DEBUG_FILEWATCH_FILENAME/i)){print "[1]Searchfor=$searchfor, where=$where, tmpfname=\"$tmpfname\"\n";}																										
		if ($DEBUG_QFF) { &log("\n\t *** Checking [".$i++."] if \"$tmpfname\" is in /^$where/i"); }
		if ($tmpfname =~ /^$where/i) {
			($tmpdir,$tmpname)=&splitdirname($tmpfname);														
			#f ($DEBUG_QFF>=2) { &log("\n    ****** --FOUND-- WHERE of $where in $tmpfname (searching for ".@regexes. " regular expressions)...\n");}			#DEBUG: if (($DEBUG_QFF>=7)||(($tmpfname=~/$DEBUG_FILEWATCH_FILENAME/i))){ print qq[===>if (($tmpfname =~ /$searchfor/i) || ($tmpname =~ /$searchfor/i))\n]; 																									
			if ($DEBUG_QFF>=1) { &log("\n    \t\t\t\t\t\t\t\t\t\t\t\t\t\t\t:) This is where we should be looking :) where=$where,searchfor=$searchfor,searchforall=$searchforall,tmpfname=$tmpfname"); }	#
			foreach $searchfor (@regexes) {																		#TODO maybe something here, or when the right is originally read, to keep unmatched parenthesis from making it crap out 20060402
				if ($DEBUG_QFF>=1) { &log("\n\t\t\t*********** So is this a match with /$searchfor/???\n\t\t\t\t*********** tmpfname=$tmpfname [name=$tmpname]"); }
				if (($tmpfname =~ /$searchfor/i) || ($tmpname =~ /$searchfor/i)) {								
					#Premature to declare this just yet: if ($DEBUG_QFF>=1) { &log("\n\t\t\t************************ --FOUND--!! tmpfname=$tmpfname,SEARCHFOR=$searchfor,where=$where...\n"); }
					$WASFOUND=0;
					if ($param->{extensionsonly}) {   
						if (&isValidExtension($tmpfname)) { 
							 $WASFOUND=1; 
						}																						elsif ($DEBUG_QFF>=1) { &log("\n\t\t\t***********BUT*********** Not pushing onto results due to extension.....\n"); }
					} else { $WASFOUND=1; }
					if ($WASFOUND) {
						push(@results,$tmpfname);
						if ($DEBUG_QFF>=2) { &log("\n\t\t\t--YES: MATCH FOUND--"); }
					} else { if ($DEBUG_QFF>=2) { &log("\n\t\t\t--NO: MATCH NOT FOUND--");	} }
				}     else { if ($DEBUG_QFF>=2) { &log("\n\t\t\t--NO: MATCH NOT FOUND--");	} }
			}#endforeach
			#if ($DEBUG_QFF>=1) { &log("\n*********** ^^^DONE "); }	#
		} elsif ($DEBUG_QFF>=2) { &log(" (nope) "); }
	}#endforeach
	if ($DEBUG_QFF>=1) { &log("\n ---------------- There were ".@results." results found!!!\n\n"); }
	return(@results);
}#endsub quickfilefind
######################################################################################

#################################################################################################
sub regexquote {
	my $s = $_[0];
	##### Convert characters that would be interprted as regex back to literals:
	#If i were to convert \ and / to \\ and // I would do it here(first), not later.
	#BLANK: $s =~ s/\X/\\X/g;
	$s =~ s/\\/\\\\/g;		

	$s =~ s/\(/\\(/g;
	$s =~ s/\)/\\)/g;
	$s =~ s/\[/\\[/g;
	$s =~ s/\]/\\]/g;

	$s =~ s/\./\\./g;
	$s =~ s/\+/\\+/g;
	$s =~ s/\*/\\*/g;
	
	$s =~ s/\^/\\^/g;
	$s =~ s/\$/\\\$/g;
	
	#any new additions also need to be propagated to Clio::String

	return($s);
}#endif regexquote
#################################################################################################

#######################################################################
sub death {
	my $s = $_[0];
	&log ( $s);
	close(LOG);
	die  ( $s);
}#endsub death 
#######################################################################

##################################################################
sub log {
	print     $_[0];
	print LOG $_[0];
}
##################################################################

##################################################################
sub logprint {
	#use open ':std', ':encoding(UTF-8)';  # Set encoding for STDOUT
	print     $_[0];
	print LOG $_[0];
}
##################################################################

##################################################################
sub logonly {
	print LOG $_[0];
}
##################################################################

##########################################################
sub openlog {
	open(LOG,">$LOG");
	binmode LOG, ":encoding(UTF-8)";
	&log("\n* Using log file of:\t\t\t$LOG");
}#sub openlog
##########################################################

##############################################
sub closelog {
	close(LOG);
}#sub closelog
##############################################

###########################################################################
sub convertstaticlisttobatfile {
  local @ERRORS=();
  local @INPUTFILELIST=();
  local @INPUTREGEXLIST=();
  local $ATTRIBUTETOUSE="";

  &convert_checkstuff;
  &scriptcomment("Everything works out. No errors.\n\n");

  &converttoattributelistsnow;
  &scriptcomment("Done!");

  exit;
}#endsub convertstaticlisttobatfile
###########################################################################

###########################################################################
sub converttoattributelistsnow {
    #ASSUMES local @ERRORS (to push errors onto)
    #ASSUMES local @INPUTFILELIST,@INPUTREGEXLIST,$ATTRIBUTETOUSE


    my $lineforprinting=""; my $tmperr=""; my $shortmp3="";
    my $dir=""; my $drive=""; my $mp3=""; my $regex="";
    my $curdrive=""; my $curdir=""; my $cd="cd";
    my $nummp3s=@INPUTFILELIST;

    if ($UNIX) { $cd="chdir"; }

    for (my $line=0; $line<$nummp3s; $line++) {
      $mp3   = @INPUTFILELIST [$line];
      $regex = @INPUTREGEXLIST[$line];
      chomp $mp3; chomp $regex;

      ## shortmp3 is just the filename.mp3 without the path...
      ($drive,$dir,$shortmp3)=&convertgetinfo($mp3);
      &scriptcomment("Processing #".($line+1)."/".$nummp3s.": $mp3");
      #&scriptcomment("curdrive/curdir/drive/dir is ".$curdrive."/".$curdir."/".$drive."/".$dir);


      if (($curdrive ne $drive) && (!$UNIX)) {
          my $doit=1;
          if (($curdrive eq "") & ($drive ne "")) { $doit=1; }
          if ($drive eq "") { $doit=0; }
          if ($doit) { $curdrive=$drive; print $drive . ":\n"; }
      }
      if ($curdir ne $dir) {
          $curdir=$dir;
          $dir4test = $curdrive . ":" . $curdir;
          if (-d $dir4test) { print "$cd \"$dir\"\n"; }
          else {
              &scriptcomment("NON-FATAL ERROR: directory $dir4test does not exist!!");
              next;

          }
      }
      print "echo ## Assign attribute '".$ATTRIBUTETOUSE."' to $shortmp3: >>attrib.lst\n";
      print "echo $regex".":"."$ATTRIBUTETOUSE >>attrib.lst\n\n";

      print "\n";
    }
}#endsub converttoattributelistsnow
###########################################################################

###########################################################################
sub tostr {
	my @s = $_[0];
	my $s="";
	foreach $tmp (@s) { $s .= "$tmp "; }
	$s =~ s/\s+$//i;
	return($s);
}
###########################################################################
###########################################################################
sub hashdump {
	my %hash=%{$_[0]};
	my $r="[";
	foreach my $key (sort keys %hash) {
		$r .= "($key=$hash{$key}),\t";
	}
	$r =~ s/,\t$//i;							#strip last trailing delimiter
	$r .= "]";
	return($r);
}
###########################################################################

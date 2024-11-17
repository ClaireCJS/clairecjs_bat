#!/usr/local/bin/perl


use   MP3::Info;
#se Video::Info;								#deprecated: 2000-2011 - install Video::Info::Magic perhaps
use Video::Info::Magic;					        #202306 demona fix attempt
use Image::ExifTool qw(:Public);				#new library for: 2011+	

# Video::Info::ASF                    
# Video::Info::FOO                    
# Video::Info::MPEG                   
# Video::Info::MPEG::Audio            
# Video::Info::MPEG::Constants        
# Video::Info::MPEG::System           
# Video::Info::MPEG::Video            
# Video::Info::Magic                  
# Video::Info::Quicktime              
# Video::Info::Quicktime_PL           
# Video::Info::RIFF    

use utf8;										#20221102
use open ':std',':encoding(UTF-8)' ;
binmode(STDIN,  ':encoding(UTF-8)');
binmode(STDOUT, ':encoding(UTF-8)');

my $DEBUG_TRANSFORMATION      = 0;				#ANNOYING VERBOSE OUTPUT
my $DEBUG_CURDIR              = 0;				
my $DEBUG_INHERITED_RENAMINGS = 0;
my $DEBUG_LIB2011             = 0;				#debug Image::ExifTool libary (added in 2011 to include MKV support, but being backfilled for other filetypes)
my $DEBUG_VIDEO_ATTRIBUTES    = 0;
my $DEBUG_PAREN_CAPITALIZE    = 0;
my $DEBUG_BITRATE_TAGGING     = 0;				#1=some,2=more
my $SAME_BITRATE_THRESHOLD    = 5;				#189kbps and 192kbps are considered the same
my $ATTRIB_LST                = "attrib.lst";	#DO NOT CHANGE. Synchronized with various other scripts.

##### Strictness 
##### Can't do this because of 'TCON' being used as bareword parameter in get_genre for mp3s ... but everything else checks out
#use strict;		
#use vars qw($PARENTHESIS $info $first $rest $word $filename $retval $tmp $isAudio
#			$isVideo $isImage $isComic $padHyphens $padDashes @LINES %FILENAMES $arate @S);


my @DONOTCAPITALIZE=("Animals","Anime Video","Bloopers","Cats","Cops","Computers","Decapitation","Execution",			### THESE NEED TO BE CAPITALIZED IN THE WAY THAT YOU WANT TO STOP
					 "Fan Video","Featurette","Normalization-report","optical illusion","Parody","Panel",				##^^ honestly don't know what the fuck this comment means, but this is for stuff that should always be kept lowercase
					 "Political Satire","Porn","Satire","Sports","spinoff","Short","The Body","Vehicles",
					 "Violence");
my $curdir=Win32::GetCwd();				
my $curdirname=$curdir; $curdirname=~s/^(.*)[\\\/](.*)$/$2/g;			#DEBUG: print "\n\n\n\$curdir=$curdir\n";print "\n\n\n\$curdirname=$curdirname\n";
my $NEW_CAMERA_IMAGE_MODE=0;
my $line;
my %FILEAMES=();					#hash of used filenams
my %BASE_RENAMINGS=();				#key=filename w/o extension,value=renamed filename w/o extension [used for inherited renamings]
local $PARENTHESIS=0;				#used by &capitalize and subordinates to track if we are in parenthesis or not 
my $firstStereo="";
my $firstBitrate="";
my $firstFrequency="";
my $CHANNELS_ALL_THE_SAME=1;
my $BITRATES_ALL_THE_SAME=1;
my $FREQUENCIES_ALL_THE_SAME=1;
my $VBR="";
my $tmp1="";
my $tmp2="";
my $tmp3="";
my $tmp4="";
my $tmpMMSS="";
my $stereo="";
my $bitrate="";
my $frequency="";
my $numVideoFiles=0;
my $numAudioFiles=0;
my %NamesUsed=();
my %NUM_FILES_BY_EXTENSION=();
my @FILENUM_ALREADY_BASERENAMED=();
my $REMOVE_PARENT_FOLDER_NAME_FROM_FILENAME=0; 
my $REMOVE_GRANDPARENT_FOLDER_NAME_FROM_FILENAME=0; 
my $parent_dir="";
my $parent_dir_without_year="";
my $grandparent_dir="";
my $cheating_NotReallyVideo="";													#to track when we are renaming [usually sidecar/companion] files as if they are videos, for filetypes that are not videos, like TXT files. Yeah, it's weird.



if ($ENV{"REMOVE_ARTIST_ALBUM_FROM_FILENAME_MODE"} == 1) {						#2024 behavior added
	     $REMOVE_PARENT_FOLDER_NAME_FROM_FILENAME=1; 
	$REMOVE_GRANDPARENT_FOLDER_NAME_FROM_FILENAME=1; 

	(@segs) = split (/[\\\/]/,$curdir);										    #split current folder into segments
		 $parent_dir = $segs[@segs-1];
	$grandparent_dir = $segs[@segs-2];

	$parent_dir_without_year = $parent_dir;
	$parent_dir_without_year =~ s/^[12]\d\d\d\s?\-?\s?//;

	if (0) {																	#just some debug stuff, do not rename files with this on ever
		print "echo !!!!! curdir = $curdir \n"; 
		print "echo !!!!!   segs = @segs   \n"; 
		print "echo !!!!!     gp = $grandparent_dir \n"; 
		print "echo !!!!!      p = $parent_dir      \n"; 


		print "echo !!!!! curdir = $curdir \n"; 
		$test1 = $curdir;
		$test1 =~ s/$parent_dir//ig;
		print "echo !!!!!  test1 = $test1      \n"; 

		$test2 = $curdir;
		$test2 =~ s/$grandparent_dir//ig;
		print "echo !!!!!  test2 = $test2      \n"; 

		$test3 = $curdir;
		$test3 =~ s/$parent_dir//ig;
		$test3 =~ s/$grandparent_dir//ig;
		print "echo !!!!!  test3 = $test3      \n"; 
	}

}

if ($DEBUG_CURDIR) { print "echo !!!!! curdir = $curdir\n"; }
##### MAKE SOME DETEMRINATIONS REGARDING IMAGE-MODE:
my $CAMERA_FILENAME_PREFIX="";
if (
		((-e $ATTRIB_LST) && ($curdir =~ /[\\\/]pics[\\\/]/))					## *********** IMPORTANT LIST OF FOLDERS!!!! *********** 
	 || ($curdir =~ /[\\\/]pics-blah[\\\/]/i)									## *********** IMPORTANT LIST OF FOLDERS!!!! *********** 
	 || ($curdir =~ /[\\\/]New Pictures[\\\/]/i)								## *********** IMPORTANT LIST OF FOLDERS!!!! *********** 
	 || ($curdir =~ /[\\\/]NewPics[\\\/]/i)										## *********** IMPORTANT LIST OF FOLDERS!!!! *********** 
	 || ($curdir =~ /dropbox[\\\/]Camera Uploads/i)								## *********** IMPORTANT LIST OF FOLDERS!!!! *********** 		
) { 
	$NEW_CAMERA_IMAGE_MODE=1;# die "new camera image mode is $NEW_CAMERA_IMAGE_MODE\n";

	##### GET CURRENT FOLDER OUT OF PATH:
	$CAMERA_FILENAME_PREFIX = $curdir;						if ($DEBUG_INHERITED_RENAMINGS) { print "     :GLOBAL_NAME_PREFIX[0] is \"$CAMERA_FILENAME_PREFIX\"\n"; }
	$CAMERA_FILENAME_PREFIX =~ s/^(.*)[\\\/]//;				if ($DEBUG_INHERITED_RENAMINGS) { print "     :GLOBAL_NAME_PREFIX[1] is \"$CAMERA_FILENAME_PREFIX\"\n"; }

	##### MASSAGE CURRENT FOLDER:
	#CAMERA_FILENAME_PREFIX =~ s/^([12][0-9][0-9][0-9])_([01][0-9])_([0-3][0-9])[\s\-\_]*/$1$2$3 - $3$2/i;	#was like this for a cpl years?
	$CAMERA_FILENAME_PREFIX =~ s/^([12][0-9][0-9][0-9])_([01][0-9])_([0-3][0-9])[\s\-\_]*/$1$2$3 - /i;		#20181227
	$CAMERA_FILENAME_PREFIX =~ s/-pretagged$//i;			if ($DEBUG_INHERITED_RENAMINGS) { print "     :GLOBAL_NAME_PREFIX[2] is \"$CAMERA_FILENAME_PREFIX\"\n"; }

	$CAMERA_FILENAME_PREFIX =~ s/ [1-9]_/ /i;		#to stop "2_"  before multi-folders-per-day type situations where i have "19991231_1" and "19991231_2" and such
	if ($DEBUG_INHERITED_RENAMINGS) { print "     :GLOBAL_NAME_PREFIX[3] is \"$CAMERA_FILENAME_PREFIX\"\n"; }

	$CAMERA_FILENAME_PREFIX =~ s/[0-3][0-9]_/ /i;	#to stop "31_" before multi-days-per-folder type situations where i have "19991230-31"                 and such
	if ($DEBUG_INHERITED_RENAMINGS) { print "     :GLOBAL_NAME_PREFIX[4] is \"$CAMERA_FILENAME_PREFIX\"\n"; }

	#$CAMERA_FILENAME_PREFIX =~ s///i;
	
	$CAMERA_FILENAME_PREFIX .= " - ";
	if ($DEBUG_INHERITED_RENAMINGS) { print "     :GLOBAL_NAME_PREFIX[5] is \"$CAMERA_FILENAME_PREFIX\"\n"; }
	$CAMERA_FILENAME_PREFIX =~ s/Camera Uploads \- //i;
	if ($DEBUG_INHERITED_RENAMINGS) { print "     :GLOBAL_NAME_PREFIX[9] is \"$CAMERA_FILENAME_PREFIX\"\n"; }
} else {
	$NEW_CAMERA_IMAGE_MODE=0; 
}



##### READ THE NAMES OF THE FILES WE PLAN ON RENAMING INTO OUR PROCESSING ARRAYS:
my $file="";
my $filebase="";
my @ORIGINAL_FILENAMES=();
my $fileNumber=0;
open(NEWNAMES,"$ARGV[0]");          ##### 1st file, $tmp1, the   new    filenames
	while ($filename=<NEWNAMES>) {
		$fileNumber++;
		chomp $filename; 
		$filebase = &remove_extension($filename);
		push(@LINES,$filename); 
		$ORIGINAL_FILENAMES{$fileNumber}= $filename;
		$ORIGINAL_FILEBASES{$fileNumber}= $filebase;														#DEBUG#if (1) { print "echo !!!!! \$ORIGINAL_FILEBASES{filenum=$fileNumber=$filename}='$filebase'\n"; }
		$BASE_RENAMINGS{$filebase}        = uc($filebase);
		$FILENAMES{$filename}             = "1";
		$FILEBASES{$filebase}             = "1";
		#DEBUG: print "[filenoext=$fileNoExt]\n";
	}
close(NEWNAMES); 
my $numFiles=@LINES;

##### RUN EACH FILE THROUGH THE RENAMING ENGINE:
my $original_filename;
my @original_filenames=();
my $original_filenameNoExt="";
my      $new_filenameNoExt="";
my $lineNum=0;
my $fileNum="";
foreach $filename (@LINES) {
	if (($filename =~ /\.deprecated$/i) || ($filename =~ /\.dep$/i)) { goto SKIP_PROCESSING; }
	$PARENTHESIS=0;									#in case the previous line ends with a left-paren, this will reset the paren-tracking back to 0 so that we don't stop capitalizing stuff, falsely thinking we are in parens
	$original_filenames[++$lineNum] =                   $filename;	$fileNum=$lineNum;
	$original_filename              =                   $filename;
	$original_filenameNoExt         = &remove_extension($filename);
	$original_extension             =    &get_extension($filename);
	
    # Get the new and old names from the input files and circumcize


    # Determine if it's audio
	$cheating_NotReallyVideo = 0;												#used for internal cheating
    $isAudio  = 0;
    $isImage  = 0;
    $isVideo  = 0;
    $isComic  = 0;
	$isLyrics = 0;
    if ($filename =~ /\.jpe?g$/i)            { $isImage=1; }
    if ($filename =~ /\.jpe?g.deprecated$/i) { $isImage=1; }
    if ($filename =~ /\.gif$/i)              { $isImage=1; }
    if ($filename =~ /\.bmp$/i)              { $isImage=1; }
    if ($filename =~ /\.png$/i)              { $isImage=1; }
    if ($filename =~ /\.tga$/i)              { $isImage=1; }
    if ($filename =~ /\.pdf$/i)              { $isComic=1; }
    if ($filename =~ /\.cb[rz]$/i)           { $isComic=1; }
    if ($filename =~ /\.au$/i)               { $isAudio=1; }

    if ($filename =~ /\.mp3$/i)              { $isAudio=1; $NUM_FILES_BY_EXTENSION{"mp3"}++; }
    if ($filename =~ /\.mp[24]$/i)           { $isAudio=1; }
    if ($filename =~ /\.wav$/i)              { $isAudio=1; }
    if ($filename =~ /\.w[mp]a$/i)           { $isAudio=1; }
    if ($filename =~ /\.flac$/i)             { $isAudio=1; $NUM_FILES_BY_EXTENSION{"flac"}++; }

    if ($filename =~ /\.asf$/i)              { $isVideo=1; }
    if ($filename =~ /\.mp4$/i)              { $isVideo=1; }	#might be bad for AUDIO-ONLY mp4s..
    if ($filename =~ /\.m4v$/i)              { $isVideo=1; }	#added 20120601 - may suck
    if ($filename =~ /\.avi$/i)              { $isVideo=1; }
    if ($filename =~ /\.webm$/i)             { $isVideo=1; }
    if ($filename =~ /\.3gp$/i)              { $isVideo=1; }
    if ($filename =~ /\.avi.deprecated$/i)   { $isVideo=1; }
    if ($filename =~ /\.ts$/i)               { $isVideo=1; }


	##### 20060822 WTF -- I find this, but it's still like this?!?!:
#bad idea: lename =~ /\.idx$/i)     { $isVideo=1; } #20051010 let's try this
    if ($filename =~ /\.idx$/i)     { $isVideo=1; $cheating_NotReallyVideo=1; } #excluded from some things later
#bad idea: lename =~ /\.idx$/i)     { $isVideo=1; $cheating_NotReallyVideo=1; } #20051010 let's try this
#bad idea: lename =~ /\.sub$/i)     { $isVideo=1; $cheating_NotReallyVideo=1; } #20051010 let's try this
    if ($filename =~ /\.sub$/i)     { $isVideo=1; $cheating_NotReallyVideo=1; } #excluded from some things later
    if ($filename =~ /\.srt$/i)     { $isVideo=1; $cheating_NotReallyVideo=1; } #excluded from some things later
#bad idea: lename =~ /\.sub$/i)     { $isVideo=1; } #20051010 let's try this

	if ($filename =~ /\.flv$/i)     { $isVideo=1; }
    if ($filename =~ /\.mkv$/i)     { $isVideo=1; }
    if ($filename =~ /\.mov$/i)     { $isVideo=1; }
    if ($filename =~ /\.mpa$/i)     { $isVideo=1; } #may actually be audio (?)
    if ($filename =~ /\.mpe?g?$/i)  { $isVideo=1; }
    if ($filename =~ /\.nfo$/i)     { $isVideo=1; $cheating_NotReallyVideo=1; }  #Not really a video, but a frequent companion file
    if ($filename =~ /\.ogm/i)	    { $isVideo=1; }
    if ($filename =~ /\.ra?m$/i)    { $isVideo=1; }
    if ($filename =~ /\.swf$/i)     { $isVideo=1; }
    if ($filename =~ /\.txt$/i)     { $isVideo=1; $cheating_NotReallyVideo=1; } #cheating.. a lot of my isvideo logic really should apply to ismedia or something
    if ($filename =~ /\.wmv$/i)     { $isVideo=1; }
    if ($filename =~ /\.viv$/i)     { $isVideo=1; }
    if ($filename =~ /\.vob$/i)     { $isVideo=1; }  
    if ($filename =~ /\.zip$/i)     { $isVideo=1; $cheating_NotReallyVideo=1; } #cheating

	##### lyric files — for now, treat them the same as audio files, even though they are not:
    if ($filename =~ /\.lrc$/i)     { $isLyrics = 1; }
    if ($filename =~ /\.kas$/i)     { $isLyrics = 1; }
	if ($isLyrics)                  { $isAudio  = 1; }

	##### Keep track of what kinds of files make up this folder, so we can decide if it's an album/music folder or not:
	if ($DEBUG_TRANSFORMATION) { print ":Checkpoint 02.B1: $filename\n"; }
	if ($isVideo) { $numVideoFiles++; }
	if ($isAudio) { $numAudioFiles++; }
	if (($isAudio || $isVideo) && !$cheating_NotReallyVideo) { $BASE_FILENAMES_WITH_MEDIA{$original_filenameNoExt}="1"; }


    ##### Determine how to massage the data
    $padHyphens = 0; $padDashes = 0;
    if (($isAudio) || ($isVideo)) { $padHyphens = 1; $padDashes = 1; }

	#### Temp 20221216 for the 1860-1940 music
	$filename =~ s/   */ - /;
	$filename =~ s/[\s\-]+\(*(1[89][0-9][0-9])[\)\s]*(\.$original_extension)/ ($1)$2/;



    ##### Massage the data
    if (($isAudio) || ($isVideo) || ($isComic)) {
		## fix capitalization of extensions
        $filename =~ s/\.MP3$/.mp3/;
        $filename =~ s/\.Avi$/.avi/;
        $filename =~ s/\.AVI$/.avi/;
        $filename =~ s/\.ISO$/.iso/;

        $filename =~ s/([a-z])_/$1 /gi;           #stupid underscores
		
		#next 2 lines expaneded from 1 line 200811:
        $filename =~ s/ - ([0-9][0-9])\-([a-z])/ - $1_$2/i;  #change 05-O to 05_O but only if a " - " is before it
        $filename =~ s/^([0-9][0-9])\-([a-z])/$1_$2/i;       #change 05-O to 05_O but only at the beginning of the line

        $filename =~ s/([a-z])\(/$1 (/;

        $filename =~ s/_-_/ - /g;                 #moved from XV1 below
        $filename =~ s/\s-_/ - /g;                #moved from XV1 below
        $filename =~ s/([a-z]) _([a-z])/$1 - $2/gi;
        $filename =~ s/[,'\!]_/$1 /g;
    }#endif


	#DEBUG: 	print "filename=$filename,isDotTxt=$cheating_NotReallyVideo\n";#



#    #####this just brought me way too much misery:
#    if ($padHyphens) {
#        $filename =~ s/([a-z])(\-)/$1 -/gi;
#        $filename =~ s/(\-)([a-z])/- $2/gi;
#    }#endif

	##### 2022/04/06 - let's try taking off artist - album - ##_trackname.wav prefix to just be ##_Trackname.wav
	#####  this is pretty dangerous! be careful!
	if ($isAudio) {
		$filename =~ s/^[^\-]+ - [^\-]+ - ([0-9]+[_ ].*\.wav)/$1/;
	}
	if (($isImage) && ($numAudioFiles>2)) {
		$filename =~ s/^[^\-]+ - [^\-]+ - ([a-z]+\.[a-z][a-z][a-z])/$1/;
	}


	##### 2024/03/24 - adding peeling off album/artist from filename based on grand/parent foldernames:
	if (0) {			#debug
			print "***** parent_dir=$parent_dir *****\n";#goat
			print "***** parent_dir_without_year=$parent_dir_without_year *****\n";#goat
	}
	if (     $REMOVE_PARENT_FOLDER_NAME_FROM_FILENAME) { $filename =~      s/$parent_dir\s?-?\s?//i; } 
	if (     $REMOVE_PARENT_FOLDER_NAME_FROM_FILENAME) { $filename =~      s/$parent_dir_without_year\s?-?\s?//i; } 
	if ($REMOVE_GRANDPARENT_FOLDER_NAME_FROM_FILENAME) { $filename =~ s/$grandparent_dir\s?-?\s?//i; } 


	#$filename =~ s/�/'/g;			#Noo!!! perl doesn't like the apostrophe just appearing raw like that in here!
	$filename =~ s/\x{2019}/'/g;	#Yes!!! Defeat the evil Al Queda apostrophes, as we used to call them at an old job
	#use Unicode::UTF8 qw[decode_utf8 encode_utf8];
	#$filename = decode_utf8($filename);

	#common mis-spelling
	$filename =~ s/([Dd])ont/$1on't/g;

	if ($DEBUG_TRANSFORMATION) { print ":Checkpoint 02.B21: $filename\n"; }

    if ($padDashes) {
        $filename =~ s/([a-z0-9])(\-\-)/$1 --/gi;
        $filename =~ s/(\-\-)([a-z0-9])/-- $2/gi;
    }#endif


	##### NEW CAMERA PICTURE/VIDEO ONLY NAME MASSAGES:
	if ($DEBUG_TRANSFORMATION) { print ":Checkpoint 02.B24: $filename [camera_filename_prefix=$CAMERA_FILENAME_PREFIX]\n"; }
		if ((($isVideo) || ($isImage)) && (!$isAudio)) {									
			$original_filename = $filename;												#necessary after inherited renamings were added
			if (($NEW_CAMERA_IMAGE_MODE) && ($filename !~ /$CAMERA_FILENAME_PREFIX/i))  {
				if ($filename !~ /^[12][0-9][0-9][0-9][0-9]*.* - /) {
					if ($DEBUG_TRANSFORMATION) { print ":Checkpoint 02.B25.M: $filename [camera_filename_prefix=$CAMERA_FILENAME_PREFIX]\n"; }
					$filename  =  $CAMERA_FILENAME_PREFIX . $filename;
					#$original_filename = $filename;									#necessary after inherited renamings were added
				} elsif ($filename =~ /^([12]\d{3}[01]\d[0-3]\d [0-2]\d[0-5]\d) - /) {
					if ($DEBUG_TRANSFORMATION) { print ":Checkpoint 02.B25.N: $filename [camera_filename_prefix=$CAMERA_FILENAME_PREFIX]\n"; }
					$filename     =~ s/^([12]\d{3}[01]\d[0-3]\d [0-2]\d[0-5]\d - )/$1 - $CAMERA_FILENAME_PREFIX - /;
					#$original_filename = $filename;									#necessary after inherited renamings were added
				}
			}
		}																		
	if ($DEBUG_TRANSFORMATION) { print ":Checkpoint 02.B26: $filename\n"; }

	##### BUT FOR AUDIO, DO THE OPPOSITE - REMOVE THE FOLDERNAME FROM THE FILENAME - BECAUSE MUSIC COMPATIBILITY:
	if (!$NEW_CAMERA_IMAGE_MODE) {
		my $proposed_filename =  $filename;
		   $proposed_filename =~ s/^$curdirname[\\\/]? ?\-? ?//ig;
		   if ($proposed_filename !~ /^\.[^\.]{1,8}$/) { $filename = $proposed_filename; }
	}																		if ($DEBUG_TRANSFORMATION) { print ":Checkpoint 02.B27: $filename\n"; }

	##### firstish rules that failed below and were randomly moved up here:
	$filename =~ s/[\.\s]WS[\.\s]WEBRIP[\.\s]/(widescreen) (web-rip)/;
	$filename =~ s/([\.\s])WEBRIP([\.\s])/$1(web-rip)$2/i;					if ($DEBUG_TRANSFORMATION) { print ":Checkpoint 02.B35: $filename\n"; }
	$filename =~ s/.WEB.([hx]264)/ (web-rip) ($1)/;
	$filename =~ s/x264\.ctu/(x264)/i;
	$filename =~ s/x264[\_\-\.]DIMENSION/(x264)/i;
	if ($DEBUG_TRANSFORMATION) { print ":Checkpoint 02.B3: $filename\n"; }



	##### IMAGE ONLY NAME MASSAGES:
	if (($isImage) && ($numAudioFiles <= 1)) {
		$filename =~ s/_IMG\././i;
		$filename =~ s/\.JPG/.jpg/i;
		$filename =~ s/_0_BG//;
		$filename =~ s/ready-for-flickr-upload//;
		$filename =~ s/ready-for-flickr//;
	}
	if (($isImage) && ($numAudioFiles >= 2)) {
		$filename =~  /^(.)/;
		my $lowerCaseFirstLetter=lc($1);
		$filename =~ s/^./$lowerCaseFirstLetter/gi;
	}
	if ($isImage) {
		#20160529 1842 - 20160529 - Mississippi - 20160529 1842 - 27
		if ($filename =~ /([12]\d{3}[01]\d[0-3]\d) ([0-2]\d[0-5]\d) /i) {
			$tmp1=$1; $tmp2=$2;
			$filename =~ s/($tmp1 $tmp2 - .*)($tmp1 $tmp2)/$1/;
			$filename =~ s/($tmp1 .*)($tmp1 )/$1/;
		}
		
	}
	if ($DEBUG_TRANSFORMATION) { print ":Checkpoint 02.B4: $filename\n"; }

	##### VIDEO ONLY NAME MASSAGES:
	if ($isVideo) {
		$filename =~ s/\.MOV/.mov/ig;
		$filename =~ s/Nick - /Nickelodeon - /i;
	}

	##### COMIC BOOK STUFF:
	if ($isComic) {
		$filename =~ s/Adventure Time Comic/Adventure Time/i;
		foreach $tmp 
				 (
					"\(Bean-Empire\)",
					"\(BlackManta-Empire\)",
					"\(Black Manta\)",
					"\(\-Black Manta\)",
					"\(BlurPixel\)",
					"\(Chairmen-Novus-HD\)",
					"\(digital\)",
					"\(-Empire\)",
					"\(Minutemen-InnerDemons\)",
					"\(Minutemen-PhD\)",
					"\(Minutemen-Spaztastic\)",
					"\(ScanDog & Mao-Novus\)",
					"\(Minutemen-Fantomex\)",
					"\(MarvelBabes-DCP\)",
					"\(UltraBoy-DCP\)",
					"\(WildBlueZero\)",
					"\(Monafekk\)",
					"\(c2c\)",
					#"\(\)",
					#"\(\)",
					#"\(\)",
					#"\(\)",
					#"\(\)",
					#"\(\)",
					#"",
					#"",
					#"",
					#"",
					#"",
				 ) {
			$filename =~ s/$tmp//i;
		}
	}

	if ($DEBUG_TRANSFORMATION) { print ":Checkpoint 02.B5: $filename\n"; }

    if (($isAudio) || ($isVideo) || ($isComic)) {
		### Get rid of people who use dots in between EVERY word, so annoying
		if (!$isAudio) { ### TEST: 200607: but not for mp3s, because a lot of songs have dots. this is a test.
			while ($filename =~ /\..*\./) { $filename =~ s/\./ /; }
		}

		$filename =  &capitalize($filename);


		
		#XV1 #keep this comment

        #after whatever the hell it is i'm doing above, I get a lot of
        #filenames that are like Tears For Fears -_head Over Heels ...
        #must..make..it..stop
        #didn't seem to work that well anyway...whatever
        #my $capitalizedLastLetter = $filename;
        #$capitalizedLastLetter =~ s/([a-z])\s\-_([a-z])/$1/;
        #$capitalizedLastLetter =~ tr/[a-z]/[A-Z]/;
        #$filename        =~ s/([a-z])\s\-_[a-z]/$1 - $capitalizedLastLetter/;


		#global changes:
		$filename =~ s/\%20/ /g;

		#changes if it's an audio or video file:
	    if (($isAudio) || ($isVideo)) {
	        $filename =~ s/khz/kHz/gi;
	        $filename =~ s/khz mono/kHz mono/gi;
	        $filename =~ s/Mono\)/mono\)/;
	        #$filename =~ s/ - Id - )/ - id - /;
	        #$filename =~ s/ - Promo - )/ - promo - /;
	        $filename =~ s/(TV-?rip)/(vidcap)/i;
	        $filename =~ s/(TV-?cap)/(vidcap)/i;
	        $filename =~ s/\-\(vidcap\)/ (vidcap)/i;
	        $filename =~ s/\(Live\)/(live)/;
			if ($isAudio) {
		        $filename =~ s/\(([^(]* ?)vinyl rip\)/($1vinyl rip)/i;
			}
			if ($isVideo) {
		        $filename =~ s/\(Alt\.? credits\)/(alt credits)/i;
		        $filename =~ s/\(No Videos\)/(no videos)/i;
		        $filename =~ s/\(With Videos\)/(with videos)/i;
				$filename =~ s/VHSrip/\(vhs\)/i;
		        $filename =~ s/\(sl U(ncro?p?p?e?d?) vhs\)/(sl u$1 vhs)/i;
		        $filename =~ s/\(end cut off\)/(end cut off)/i;
		        $filename =~ s/\(credits slightly off\)/(credits slightly cut)/i;
			}
		}


		if ($isAudio) {								#track number stuff
			#$filename =~ s/^([0-9][0-9])\.[_\s\-]+/$1_/i;					#never used
			#$filename =~ s/^([0-9][0-9])([a-z\)/$1_$2/i;			#2000/01
			$filename =~ s/^([0-9][0-9])\. /$1_/i;					#2022/02
			$filename =~ s/^([0-9][0-9]) \- /$1_/i;					#2022/02
			$filename =~ s/^([0-9][0-9])([a-z\.])/$1_$2/i;			#2022/02
			$filename =~ s/^([0-9][0-9])[_\s\-]+/$1_/i;				

			#keep these 2 lines together:
				$filename =~ /^([0-9][0-9])_Track([0-9][0-9])/i;
				if ($1 eq $2) { $filename =~ s/^([0-9][0-9])_Track([0-9][0-9])/$1/i; }	
			#keep these 2 lines together:
				$filename =~ /^0([0-9])_Track([0-9])/i;
				if ($1 eq $2) { $filename =~ s/^(0[0-9])_Track([0-9])/$1/i; }
		}


		# pre-main stuff
		$filename =~ s/\s\&_/ & /g;
        $filename =~ s/\(Long version\)/(long version)/i;
        $filename =~ s/\(First version\)/(first version)/i;
        $filename =~ s/\(Cassette vinyl encode\)/(cassette vinyl encode)/i;
        $filename =~ s/\(Shortened version\)/(shortened version)/i;
        $filename =~ s/ Quality\)/ quality)/;
		$filename =~ s/banned episode/BANNED/;

        #1st 11th 2nd 12th 3rd 13th 4th 5th 6th etc
        $filename =~ s/1St/1st/;
        $filename =~ s/2Nd/2nd/;
        $filename =~ s/3Rd/3Rd/;
        $filename =~ s/([0-9])Th/$1th/;

        $filename =~ s/([\s\(])S([0-9]+[eE][0-9]+)([\s\)])/$1s$2$3/;
        if (!$isVideo) {
            #video is sometimes Kbps not kbps so don't fuck with it
            $filename =~ s/\(([0-9]+)Kbps\)/($1kbps)/;
        }
        $filename =~ s/\[/(/g;    #brackets fuck with 4dos
        $filename =~ s/\]/)/g;
        $filename =~ s/\]/)/g;
		if ($DEBUG_TRANSFORMATION) { print ":Checkpoint 005: $filename\n"; }
        my @regeps=
        (           ##### STUFF TO FORCE INTO LOWERCASE:
					##### OSD/osd are case sensitive and should not be put in
            #"(slightly cut off!+)","(buzzy sound)","(some clipping!+)",
            #"(slightly cut off)","(may be cut off)",
            "\\(song only\\)",
            "\\(song plus ","\\([0-9]+ parts\\)",
            "\\(alternate.*?credits\\)",
            "\\(annoying.*?during.*?episode\\)",
            "\\(end.*?cut\\)",
            #"\\(.*?cut off\\)",
            "\\([0-9]+?kbps but ",
            " bad reception\\)",
            " - podcast - ",
            " - promo - ",
            " - id - ",
            "\\(musica?l? episode\\)",
            "\\(deleted scene\\)",
            "\\(no credits\\)",
            "\\(tape problems\\)",
            "\\(vinyl rip\\)",
            " video podcast ",								#made redundant by next entry?
            " trailer ",									
            " fake trailer ",								#made redundant by next entry?
            " fake trailer - as a ([a-z ]+)",				#made redundant by next entry?
		    " fake trailer - .* - as a  ([a-z ]+)",
            " opening theme",
			" opening & closing theme",
            " closing theme",
            "\\([^\\)]* snd\\)",
            "\\([^\\)]* buzz\\)",
            "\\(slight [^\\)]*\\)",
            "\\([betc][enhr][^\\)]* cut\\)",
            "\\([^\\)]*interference\\)",
            "\\([HML]Q [^\\)]*\\)",
            "\\([^\\)]*desync\\)",
            "\\(no theme[^\\)]*\\)",
            "\\(live action\\)",
            "\\(cut off!*\\)",
            "\\(animated\\)",
            "\\(claymation\\)",
            ##"\\([^\\)]*?OSD\\)",		##bad idea as this forces to lowercase
            "\\([^\\)]*? quality\\)",
            "\\(deleted scene only\\)",
            "imperfect audi?o?\\)",
            "imperfect vide?o?\\)",
            "\\(imperfect.*?\\)",
            "\\([0-9]*?k divx\\)",
            "\\([^\\)]*? line at top\\)",
            "\\(sub.?titled in [a-z\-]+?\\)",
            " unencodeable!?\\)"," unencodeable!!+\\)",
            "\\(full song\\)","(full [0-9]\.[0-9]+m ver)",
            "([0-9]+min ver)","(from soundtrack)",
        );
        my ($count,$lc);
        foreach (@regeps) {
			#print "Doing regeps \"$_\"\n";
            $count=1;
            while ($filename =~ /($_)/i) {
                $lc=lc $1;
                $filename =~ s/($_)/$lc/i;
                if ($count++ > 5) { last; }
            }#endwhile
        }#endforeach
        $filename =~ s/DragonBall Z ([A-Z]+)/DragonBall Z - $2/i;
        $filename =~ s/\(TV Ver\)/(TV ver)/;
        $filename =~ s/mg([0-9][0-9])/MG$1/;
    }#endif
	if ($DEBUG_TRANSFORMATION) { print ":Checkpoint 011: $filename\n"; }

    ### SxExx should be in all caps
    if ($filename =~ /(s[0-9][0-9]?e[0-9][0-9]?[0-9]?)/i) {
        my $tmp = uc $1;
        $filename =~ s/$1/$tmp/;
    }#endif
	### other SxExx stuff
	if ($isVideo) {
		#This one sucks for JPGs!:
		$filename =~ s/([^0-9])([0-9])x([0-9][0-9])/$1S$2E$3/i;	#1x01 type stuff
		#Kenny Vs. Spenny-S4E10_(Who Can Commit the Most Crime) (xvid).avi:
		$filename =~ s/-S([0-9]+)E([0-9]+)/ - S$1E$2/;
	}
	$filename =~ s/Season ([0-9]+)/S$1/i;
	if ($filename !~ /monkey.*dust/i) {
		$filename =~ s/Episode ([0-9]+)/E$1/i;
	}
	$filename =~ s/s([0-9]+)[\s_-]+e([0-9]+)/S$1E$2/i;
	if ($filename =~ /--.*--/) { $filename =~ s/--/-/g;	}
	if ($filename =~ /([Ss][0-9][Ee][0-9][0-9]_)([a-z])/) {
		$tmp = $1 . uc($2);
		$filename =~ s/([Ss][0-9][Ee][0-9][0-9]_)([a-z])/$tmp/i;
	}
	if ($DEBUG_TRANSFORMATION) { print ":Checkpoint 012: $filename\n"; }
	### after SxExx some things are pretty much guaranteed BS:
	#DEBUG: print ":filename[5234] is $filename\n";
	$filename =~ s/(S[0-9]+E[0-9]+[ _])INTERNAL /$1/;
	$filename =~ s/(S[0-9]+E[0-9]+[ _])HR /$1/;
	$filename =~ s/([a-z+])(S[0-9]+E[0-9][0-9])/$1 - $2/i;

	### codec names
    $filename =~ s/\(Divx\)/(divx)/i;		#just make it ALL divx .. stupid people & their stupid Capitalization
    $filename =~ s/\)_\(/) (/;
	$filename =~ s/ divx 5.2.1 /(divx)/i;
	$filename =~ s/ divx([\-\s\.])/(divx)$1/i;
	$filename =~ s/.[hx].264([\-\s\.])/($1264)$2/;

	### part x of x
	if ($isVideo) {
		$filename =~ s/Part([0-9])/part $1/;
		$filename =~ s/, Part ([1-2]) / - part $1 of 2 /i;
		$filename =~ s/Part ([0-9]+ )of( [0-9]+)/part $1of$2/i;
		$filename =~ s/ ([0-9]+ )of( [0-9]+)/ $1of$2/i;
		$filename =~ s/ P([1-2]) / - part $1 of 2 /;			# "P1" and "P2" nomenclature
		$filename =~ s/ \(Part ([1-2])\) / - part $1 of 2 /i;	# "(Part 1)"    nomenclature
		$filename =~ s/ \(Pt\.? ([1-2])\) / - part $1 of 2 /i;	# "(Pt. 1)"     nomenclature
		$filename =~ s/ Pt\.? ([1-2]) / - part $1 of 2 /i;		#  "Pt. 1"      nomenclature
	}
	if ($DEBUG_TRANSFORMATION) { print ":Checkpoint 015: $filename\n"; }

    ### show names 
	$filename =~ s/Rick & Morty/Rick And Morty/ig;
	$filename =~ s/Dirk Gentlys/Dirk Gently's/ig;
	$filename =~ s/^Doctor Who Extra - /Doctor Who - extra - Doctor Who Extra - /ig;
	$filename =~ s/Cartoon Network City/Cartoon Network - promo - Cartoon Network City/ig;
	$filename =~ s/Fugget.About.It./Fugget About It /ig;
	$filename =~ s/-? ?Webisodes - Adult Swim Video(.*)(\....)/(AdultSwim) (web-rip)$1 (Osd)$2/ig;
	$filename =~ s/The Agents Of S M A S H /The Agents Of S.M.A.S.H. - /ig;
	$filename =~ s/^Talking Dead/The Talking Dead/ig;
	$filename =~ s/BREAKING BAD/Breaking Bad/;
	$filename =~ s/China IL/China, IL/ig;
	$filename =~ s/TMNT/Teenage Mutant Ninja Turtles/g;
	$filename =~ s/Teenage Mutant Ninja Turtles \(2012\)/Teenage Mutant Ninja Turtles-TAS (2010s)/ig;
	$filename =~ s/Todd & The Book Of Pure Evil/Todd And The Book Of Pure Evil/ig;
	$filename =~ s/MLP *- *EG *-* */My Little Pony- Equestria Girls - /ig;
	$filename =~ s/MLP /My Little Pony- Friendship Is Magic /ig;
	$filename =~ s/MLP[\-\s]?FiM /My Little Pony- Friendship Is Magic /ig;
	$filename =~ s/MLP[\-\s]?EG /My Little Pony- Equestria Girls /ig;
	$filename =~ s/ntsd.sd.suv/National Terrorism Strike Force- San Diego- Sport Utility Vehicle/i;
	$filename =~ s/^Superjail! /Superjail/i;
	$filename =~ s/Mary Shellys/Mary Shelly's/i;
	$filename =~ s/^Superjail-/Superjail /i;
	$filename =~ s/Tim And Eric Awesome Show Great Job/Tim And Eric Awesome Show, Great Job!/;
	$filename =~ s/The Dragon That Wasn't \(Or Was He.\)/The Dragon That Wasn't (Or Was He?)/ig;
	$filename =~ s/The Avengers Earths Mightiest Heroes/The Avengers- Earth's Mightiest Heroes/;
	$filename =~ s/Children's Hospital Us/Childrens Hospital/i;
	$filename =~ s/Children's Hospital/Childrens Hospital/i;
	$filename =~ s/ProducingParker/Producing Parker/i;
	$filename =~ s/^Bobs Burgers /Bob's Burgers /i;
	$filename =~ s/^MTV - Celebrity Deathmatch/Celebrity Deathmatch/i;
	$filename =~ s/^Archer (2009) /Archer /i;
	$filename =~ s/^Dr\.? Who (2005) /Doctor Who (2000s) /i;
	$filename =~ s/^Doctor Who (2005) /Doctor Who (2000s) /i;
	$filename =~ s/^TMBGPodcast/They Might Be Giants - podcast - #/i;
	$filename =~ s/^E7-office/The Office/i;	
	$filename =~ s/Cow And Chicken/Cow & Chicken/ig;
	$filename =~ s/^Aaf-tipdotm/The Increasingly Poor Decisions Of Todd Margaret/i;
	$filename =~ s/Aaf-jbhav/Jon Benjamin Has A Van/i;
	$filename =~ s/^Aaf-onn/Onion News Network/i;
	$filename =~ s/^Aaf-latot/The Life And Times Of Tim/i;
	$filename =~ s/^Aaf-wta/Warren The Ape/i;
	$filename =~ s/^Aaf-tusotu/Tracey Ullman's State Of The Union/i;
	$filename =~ s/^Aaf-tssp/The Sarah Silverman Program/i;
	$filename =~ s/^Aaf-fgsii/Fat Guy Stuck In Internet/i;
	$filename =~ s/^aaf-kvs/Kenny Vs. Spenny/i;
	$filename =~ s/^aaf-fd/Frisky Dingo/i;
	$filename =~ s/^aaf-metalocalypse/Metalocalypse/i;
	$filename =~ s/^aaf-am/Assy McGee/i;
	$filename =~ s/^aaf-sb/Squidbillies/i;
	$filename =~ s/^aaf-sp/South Park/i;
	$filename =~ s/^aaf-athf/Aqua Teen Hunger Force/i;
	$filename =~ s/^aaf-taeas/Tim And Eric Awesome Show, Great Job!/i;
	$filename =~ s/^aaf-bd/The Boondocks/i;
	$filename =~ s/^aaf-tb/The Boondocks/i;
	$filename =~ s/^The Three Stooges -/Three Stooges -/i;
	$filename =~ s/^The Simpsons -/Simpsons -/i;
	$filename =~ s/^AbFab -/Absolutely Fabulous -/i;
	$filename =~ s/^Bobobo-bo Bo-bobo - /BoBoBo - /i;
	$filename =~ s/^12 Oz Mouse/12 Oz. Mouse/i;
	$filename =~ s/^Mr Show/Mr. Show/i;
	$filename =~ s/^ATHF/Aqua Teen Hunger Force/i;
	$filename =~ s/^MITM/Malcolm In The Middle/i;
	$filename =~ s/^KOTH/King Of The Hill/i;
	$filename =~ s/The Venture Brothers/The Venture Bros./i;
    $filename =~ s/beavis&butt\-?head/Beavis & Butt-head/i;
    $filename =~ s/beavis and butt\-?head/Beavis & Butt-head/i;
    $filename =~ s/^ppg[_\s]/PowerPuff Girls - /i;
	$filename =~ s/ren and stimpy/Ren & Stimpy/i;
	$filename =~ s/^O Grady/O'Grady/i;
	#" -- " to ", " for multiple episode titles per airing -- i.e. Grim & Evil, Garfield & Friends, Eek!Stravaganza, etc
	$filename =~ s/^(Angry Beavers.*) -- (.*)$/$1, $2/;
	$filename =~ s/the ren [and&]+ stimpy show/Ren & Stimpy/i;
	$filename =~ s/^Mr Bungle/Mr. Bungle/i;
	$filename =~ s/Batman Tas /Batman-TAS (1990s) /i;
	$filename =~ s/Batman The Brave And The Bold/Batman- The Brave And The Bold/i;
	$filename =~ s/^American Dad! /American Dad /i;
	$filename =~ s/^Itchy & Scratchy[\s-]/Simpsons - clip - Itchy & Scratchy - /i;
	$filename =~ s/^Www Howtobehave Tv/www.HowToBehave.tv/i;
	$filename =~ s/^Fake Trailer /fake trailer  /;

	### segment/act numbers
    $filename =~ s/ - Segment ([0-9]+) / - segment $1 /;
    $filename =~ s/ - Act ([0-9]+) / - act $1 /;

    #1of2 1 of 2 .. etc
    $filename =~ s/([\(\[_])([0-9]+)\s*of\s*([0-9]+)([\)\]_])/- part $2 of $3/i;
    $filename =~ s/([0-9]+)of([0-9]+)/- part $1 of $2/i;

    ## for those cool 200M family guys (hehe, when were 200M MPGs cool??)
    $filename =~ s/^Family\.Guy\.s([0-9]+)e([0-9]+)_anivcd/Family Guy - S$1E$2 (anivcd)/i;
    $filename =~ s/^The Pjs/The PJs/;
    $filename =~ s/([\s_\.])([0-9]+)Th /$1$2th /;
    $filename =~ s/([\s_\.])([0-9]+)Nd /$1$2nd /;
    $filename =~ s/([\s_\.])([0-9]+)Rd /$1$2rd /;
    $filename =~ s/, Smaller\)/, smaller)/;

	## fix malformed dates 2003-04-05 and 2003 04 05 type dates.
	$filename =~ s/([12][90][0-9][0-9])[-\s]([0-1]?[0-9])[-\s]([0-3]?[0-9])/$1$2$3/;

	## fix text dates, like: August 23 1995
	$filename =~ s/January ([0-3]?[0-9]),? ([12][0-9][0-9][0-9])/$2DDD01DDD$1/;
	$filename =~ s/February ([0-3]?[0-9]),? ([12][0-9][0-9][0-9])/$2DDD02DDD$1/;
	$filename =~ s/March ([0-3]?[0-9]),? ([12][0-9][0-9][0-9])/$2DDD03DDD$1/;
	$filename =~ s/April ([0-3]?[0-9]),? ([12][0-9][0-9][0-9])/$2DDD04DDD$1/;
	$filename =~ s/May ([0-3]?[0-9]),? ([12][0-9][0-9][0-9])/$2DDD05DDD$1/;
	$filename =~ s/June ([0-3]?[0-9]),? ([12][0-9][0-9][0-9])/$2DDD06DDD$1/;
	$filename =~ s/July ([0-3]?[0-9]),? ([12][0-9][0-9][0-9])/$2DDD07DDD$1/;
	$filename =~ s/August ([0-3]?[0-9]),? ([12][0-9][0-9][0-9])/$2DDD08DDD$1/;
	$filename =~ s/September ([0-3]?[0-9]),? ([12][0-9][0-9][0-9])/$2DDD09DDD$1/;
	$filename =~ s/October ([0-3]?[0-9]),? ([12][0-9][0-9][0-9])/$2DDD10DDD$1/;
	$filename =~ s/November ([0-3]?[0-9]),? ([12][0-9][0-9][0-9])/$2DDD11DDD$1/;
	$filename =~ s/Decemeber ([0-3]?[0-9]),? ([12][0-9][0-9][0-9])/$2DDD12DDD$1/;
	$filename =~ s/DDD([0-1][0-9])DDD/$1/i;

	$filename =~ s/\(June? (\d{4})\)/(${1}06)/i;
	$filename =~ s/\(July? (\d{4})\)/(${1}07)/i;
	$filename =~ s/\(Sept? (\d{4})\)/(${1}09)/i;

	if ($DEBUG_TRANSFORMATION) { print ":Checkpoint 018: $filename\n"; }

	## S1E01 as 01X10
	$filename =~ s/([0-9]+)X([0-9]+)/S$1 XZXZXZE$2/;
	$filename =~ s/ XZXZXZ//;

	## S09 type stuff - most shows have less than 10 seasons
	if (($filename !~ /simpsons/i) && ($filename =~ /S0/i)) {
		$filename =~ s/S0([1-9])E/SOHHH $1 EXZXZXZXZ/;
		#DEBUG: print ":removing s0 crap .. filename is now $filename";
		$filename =~ s/SOHHH /S/;
		$filename =~ s/ EXZXZXZXZ/E/;
	}



	
	if ($isVideo) {
		## 3-D
		$filename =~ s/Half-SBS/(3-D) (HSBS 3-D)/;

		## southpark 101 type stuff, needs dash after showname
		$filename =~ s/([a-z\s]+[a-z]) ([0-9][0-9][0-9])/$1 - $2/i;
		#turns: South Park 101 - Something Wall-Mart This Way Comes.rm
		#into:  South Park - 101 - Something Wall-Mart This Way Comes.rm
		#BUT CAN MESS UP OTHER STUFF
		## now things like "Unlimited - 101 Ultimatum" need a fix too
		$filename =~ s/([a-z] - )([0-9][0-9][0-9]) ([a-z]+)/$1$2_$3/i;
		## And what about "Development - 101_"
		$filename =~ s/([a-z] - )([0-9][0-9][0-9])(_)([a-z\s])/$1_$2$3$4/i;

		if ($DEBUG_TRANSFORMATION) { print ":Checkpoint 022: $filename\n"; }

		## enc0der names/encoders to take out
		## encoder names/encoders to take out
		foreach $tmp (
					 "x264-METCON",
					 "x264-LEGi0N",
					 "x264-brmp",
					 "x264-esc",
					 "x264-bajskorv",
					 "x264-BluEvo",
					 "x264-hybris",
					 "x264-Absinth",
					 "x264-BATV",
					 "x264-mtg",
					 "x26[45]-AJP69",
					 "x26[45]-MeGusta",
					 "x26[45]-NTG",
					 "x26[45]-strife",
					 "x26[45]-tbs",
					 "x26[45]-TrollHD",
					 "x26[45]-TVSmash",
					 "x264-HDMaNiAcS",
					 "x264-public3d",
					 "x264-CHIPPER",
					 "x264-SADPANDA",
					 "x264-TiMELORDS",
					 "x264-PHOBOS",
					 "x264-c4tv",
					 "x264-rovers",
					 "x264-FLEET",
					 "x264-KILLERS",
					 "x264-TVSmash",
					 "\\(*x264\\)*-psychd",
					 "\\(*x264\\)*-finch",
					 "\\(*x264\\)*-NTb",
					 "\\(*x264\\)*-w4f",
					 "\\(*x264\\)*-EVO",
					 #"",
					 #"x264-",
					 #"x264-",
					 #"x264-",
					 ) {
			$filename =~ s/$tmp/(x264)/i;
		}
		#release groups and other kill-strings
		$filename =~ s/\-WURUHI//;
		foreach $tmp (
					 "h264-Cyphanix",
					 "h264-BTN",
					 "h264-DEADPOOL",
					 "h264-iBOGAiNE",
					 "h.264-iBOGAiNE",
					 "H.264-ECI",
					 "h264-MOBTV",
					 "h264-RARBG",
					 "h264-PHD",
					 "h264-METCON",
					 "h264-monkee",
					 "h264-TVSmash",
					 "\\(*h264\\)*-NTb",
					 "\\(*h264\\)*-iBOGAiNE",
					 "-DEFLATE",
					 "\(A E snd\) ",
					 #"",
					 #"",
					 #"",
					 #"",
					 #"",
					 #"",
					 #"",
					 #"h264-",
					 #"h264-",
					 ) {
			$filename =~ s/$tmp/(h264)/i;
		}
		#group names release group names
		$filename =~ s/\-amiable//;
		$filename =~ s/\-RARBG//;
		$filename =~ s/\-DEiMOS//;
		$filename =~ s/\-BARC0DE//;
		$filename =~ s/\(Phr0stY\)//;
		$filename =~ s/\-iT00NZ//;
		$filename =~ s/x264\-veto/(x264)/;
		$filename =~ s/x264\-TiMEGOD/ (x264) /;
		$filename =~ s/ \- Geophage//i;
		$filename =~ s/DiVX-JAGO//i;
		$filename =~ s/\(RG\)\././;
		$filename =~ s/^Pyro-the/The/i;
		$filename =~ s/\- IcyFlamez//i;
		$filename =~ s/WWW.DOWNVIDS.NET\-?//i;
		$filename =~ s/ +- +SFM//;
		$filename =~ s/\-BTN//;
		$filename =~ s/\-AMIABLE//;
		$filename =~ s/\-CiNEFiLE//;
		$filename =~ s/\-BamHD//;
		$filename =~ s/\-pcsyndicate//;
		$filename =~ s/\-PeDRO//;
		$filename =~ s/ \- Emory//;
		$filename =~ s/\(BT\)//;
		$filename =~ s/-NTb([ \.])/$1/;
		$filename =~ s/xvid-TTT/xvid/i;
		$filename =~ s/HEVC X265/(x265)/i;
		$filename =~ s/xvid-TOPAZ/xvid/i;
		if ($DEBUG_TRANSFORMATION) { print ":Checkpoint 024: $filename\n"; }
		$filename =~ s/pdtv-TTT/pdtv/i;
		$filename =~ s/\(iPodNova\.net\)//i;
		#if ($filename =~ /\(vpc\)/i)  moved to section below because of other considerations
		$filename =~ s/\(chaos2k\)//i;
		$filename =~ s/\(spideyfreak\)//i;
		$filename =~ s/\(cifirip\)//i; 
		$filename =~ s/\(by Rosebud\)//; 
		$filename =~ s/\(tvu Org Ru\)//i; 
		$filename =~ s/x264-sys/ (x264)/i;
		$filename =~ s/x264-bia/ (x264)/i;
		$filename =~ s/\(moonsong\)//i;
		$filename =~ s/h264-BgFr/(h264)/i;
		if ($DEBUG_TRANSFORMATION) { print ":Checkpoint 024.D: $filename\n"; }
		$filename =~ s/x264-tla/(x264)/;
		$filename =~ s/x264-mtg/(x264)/;
		$filename =~ s/x264-QCF/(x264)/;
		$filename =~ s/x264-ingot/(x264)/;
		$filename =~ s/x264-PHOBOS/(x264)/;
		$filename =~ s/x264-rovers/(x264)/;
		$filename =~ s/-SMODOMiTE//;
		$filename =~ s/x264-EVOLVE/(x264)/i;
		$filename =~ s/x264-mSD/(x264)/i;
		if ($DEBUG_TRANSFORMATION) { print ":Checkpoint 024.F: $filename\n"; }
		$filename =~ s/x264/(x264)/i;
		$filename =~ s/x264-iDLE/(x264)/i;
		$filename =~ s/h264-iT00NZ/(h264)/i;
		$filename =~ s/x264-CRON/(x264)/i;
		$filename =~ s/\(sw220\)//i;
		$filename =~ s/h264/(h264)/i;
		$filename =~ s/h264-OOO/(h264)/i;
		$filename =~ s/\(Oj\)//;
		if ($DEBUG_TRANSFORMATION) { print ":Checkpoint 024.G: $filename\n"; }
		$filename =~ s/MP3-BgFr//;
		$filename =~ s/\-?Reaperza//;
		$filename =~ s/x264-psychd/(x264)/i;
		$filename =~ s/x264-Hannibal/(x264)/i;
		$filename =~ s/x264-aAF/(x264)/i;
		$filename =~ s/x264-hd4u/(x264)/i;
		$filename =~ s/x264-SG/(x264)/i;
		$filename =~ s/(\(?[hx]26[45]\)?)-sparks/$1/i;
		$filename =~ s/H.264-TB/h264/;
		$filename =~ s/TVT //i;
		$filename =~ s/([xh]264)-PerfectionHD/($1)/i;
		$filename =~ s/XviD-T00NG0D/xvid/i;
		$filename =~ s/([xh]264)-T00NG0D/$1/i;
		$filename =~ s/XVID-CO/xvid/i;
		$filename =~ s/XVID-JEWRYE/xvid/i;
		$filename =~ s/([HhXx]264)-Reaperza/$1/i;
		$filename =~ s/PhoenixRG//;
		$filename =~ s/-PublicHD//;
		$filename =~ s/\(JewRye\)//;
		$filename =~ s/[_\- ]+Chotab//;
		$filename =~ s/[_\- ]+Orenji//i;
		$filename =~ s/[_\- ]+CtrlHD//;
		$filename =~ s/[_\- ]+CHD//;
		$filename =~ s/\-*HoodBag//;
		$filename =~ s/\(449\)//;
		$filename =~ s/H.264-SC/(h264)/i;
		$filename =~ s/\-*ShittingDickNipples//;
		$filename =~ s/H 264-jhonny2/(h264)/i;
		$filename =~ s/x264-NODLABS/(x264)/i;
		$filename =~ s/x264-AMIABLE/(x264)/i;
		$filename =~ s/h264-KiNGS/(h264)/i;
		$filename =~ s/x264-ESIR/(x264)/i;
		$filename =~ s/x264-EbP/(x264)/i;
		$filename =~ s/x264-x264-PhoenixRG/(x264)/i;
		$filename =~ s/ AVC-NFHD/(h264)/;
		$filename =~ s/ AVC/ (h264)/;
		$filename =~ s/x264-cinefile/(x264)/i;
		$filename =~ s/x264-thugline/(x264)/i;
		$filename =~ s/x264-orenji/(x264)/i;
		$filename =~ s/x264-immerse/(x264)/i;
		$filename =~ s/\{C P\}//i;
		$filename =~ s/DD5 1 AVC-CtrlHD/(dd5.1 snd)/i;
		$filename =~ s/DD5 1 H 264-TjHD/(h264) (dd5.1 snd)/i;
		$filename =~ s/H264 DD51 AAC20/(h264) (dd5.1 snd)/i;
		$filename =~ s/H 264-LP/(h264)/i;
		$filename =~ s/H 264/(h264)/i;
		$filename =~ s/AAC2 0 \(h264\)/(aac snd) (h264)/i;
		$filename =~ s/\(ant\)//is;
		$filename =~ s/ *\(s-mouche\) *//is;
		$filename =~ s/ *\(KiDDoS\) *//;
		$filename =~ s/[\- ]x264\./ (x264)./i;
		$filename =~ s/x264_hV/(x264)/i;
		$filename =~ s/x264_ctu/(x264)/i;
		$filename =~ s/x264_nbs/(x264)/i;
		$filename =~ s/x264_SEPTiC/(x264)/;
		$filename =~ s/x264_XTSF/(x264)/i;
		$filename =~ s/x264-red/(x264)/i;
		$filename =~ s/x264-LXB/(x264)/i;
		$filename =~ s/x264-REFiNED/(x264)/i;
		$filename =~ s/(26[45]\)?)-SiNNERS/$1)/gi;
		$filename =~ s/x264_sitv/(x264)/i;
		$filename =~ s/x264-iBEX/(x264)/i;
		$filename =~ s/x264-BestHD/(x264)/i;
		$filename =~ s/\(*h264\)*-myTV/(x264)/i;
		$filename =~ s/(\([0-9]+[pi]) ([xh]264)/$1) $2/i;	#)))))))))))
		$filename =~ s/(720p.x264.ac3-5.1)/(720p) (x264) (ac3 5.1 snd)/i;
		$filename =~ s/x264-720p/(720p) (x264)/g;
		$filename =~ s/(\(dsr\))-0tv/$1/i; 
		$filename =~ s/x264-0tv/(x264)/i; 
		$filename =~ s/ *\(austin316gb\)//i;
		$filename =~ s/ INTERNAL-hV//i;
		if ($DEBUG_TRANSFORMATION) { print ":Checkpoint 024.L: $filename\n"; }
		#$filename =~ s/divx-TVC/\(divx\)/;
		$filename =~ s/Jem Divx-TVC/\(divx\)/;
		##^^^^ this one needed to happen early
		$filename =~ s/H *264-CtrlHD/(h264)/i;
		$filename =~ s/x264-CtrlHD/(x264)/i;
		$filename =~ s/x264-w4f/(x264)/i;
		$filename =~ s/x264-PHD/(x264)/i;
		$filename =~ s/x264-QCF/(x264)/i;
		$filename =~ s/x264-CG/(x264)/i;
		$filename =~ s/x264-BARC0DE/(x264)/i;
		$filename =~ s/x264-NaRB/(x264)/i;
		$filename =~ s/x264-rusted/(x264)/i;
		$filename =~ s/x264-killers/(x264)/i;
		$filename =~ s/\(IcyFlamez\)//;
		$filename =~ s/\(ed2klinks[\s\.]com\)//;
		$filename =~ s/\(Dinothunderblack\)//;		
		$filename =~ s/-tcm//i;
		$filename =~ s/\(wutang700\)//i;
		$filename =~ s/\(mummra1983\)//i;
		$filename =~ s/\(RavyDavy\)//i;
		$filename =~ s/\(ReApEr\)//;
		$filename =~ s/\(Re-Enc ReApEr\)//;
		$filename =~ s/\(bowbiter\)//i;
		$filename =~ s/^Pyro-//i;			
		$filename =~ s/([0-9]_)DSR /$1 /i;
		$filename =~ s/ - Xavier//i;
		$filename =~ s/\(dummy\)//;
		$filename =~ s/ FrankeY//;		#didn't work with space AFTER
		$filename =~ s/\(Darkside RG\)//;
		$filename =~ s/\(Noggin\)//;
		$filename =~ s/\(rl\) //;
		$filename =~ s/\-gbz//;
		if ($DEBUG_TRANSFORMATION) { print ":Checkpoint 025: $filename\n"; }
		$filename =~ s/\(Viper93\)//;
		$filename =~ s/\(MeR-DeR\)//;
		$filename =~ s/\(RazZLe\)//;
		$filename =~ s/\(rl-dvd\)/(dvd-rip)/;
		$filename =~ s/\(dummyfix\)//;
		$filename =~ s/\(\#?digitaldistractions\)//i;
		$filename =~ s/-fov//;
		$filename =~ s/-lol//;
		#print "filename is $filename\n";
		$filename =~ s/\(?xvid\)?-prerelease/(pre-release) (xvid)/i;	#not an encoder name, actually, but it's a similar kind of rule as the ones nearby :)
		$filename =~ s/ pdtv-r69 / (pdtv)/i;
		$filename =~ s/{C P}  //;
		$filename =~ s/ Moonsong / /;
		$filename =~ s/dsr-loki//i;
		$filename =~ s/-LOKi//;
		$filename =~ s/-NSa//;
		$filename =~ s/-emory//;
		$filename =~ s/-sitv//;
		$filename =~ s/-CONKY//;
		$filename =~ s/-fnt\.mp3//;
		$filename =~ s/\(docslax\)//i;
		$filename =~ s/\(Fester1500\)//i;
		$filename =~ s/\(neverm0re\)//i;
		$filename =~ s/\[vhs cover\]/(vhs) - cover/;
		$filename =~ s/\(?h264\)?-SEPSiS/(h264)/i;
		$filename =~ s/\(?h264\)?-BS/(h264)/i;
		$filename =~ s/\(?h264\)?-YFN/(h264)/i;
		## encoder names/encoders to take out

		## encoder name-like stuff - other annoying filename adverts:
		$filename =~ s/\(found Via Www FileDonkey Com\)//i; #TEST?
		$filename =~ s/ ?-? ?www.torrentazos.com//i;
		$filename =~ s/\(from Www.Suprgamez.Com\)//i;
		$filename =~ s/^2 VIDEO DIVERTENTI //i;

		if ($DEBUG_TRANSFORMATION) { print ":Checkpoint 026: $filename\n"; }

		## comedy at beginning is redundant
		$filename =~ s/^[- ]*\(Comedy\)//i;

		## xvid should be in parens
		$filename =~ s/([^\(])xvid([^\)])/$1(xvid)$2/i;
		## dsr should be in parens
		$filename =~ s/([^\(])dsr([^\)])/$1(dsr)$2/i;
		## but if we end up with (dsr)ip we need to fix that!
		$filename =~ s/\(dsr\)ip/(dsr)/i;

		$filename =~ s/\(XSVCD\)/(xsvcd)/;
		$filename =~ s/\-vcd/ \(vcd\)/i;
		$filename =~ s/\(VCD\)/(vcd)/;
		$filename =~ s/Xvid/xvid/i;		#xvid should always be lowercase
		$filename =~ s/\(iPod\)/(ipod)/;
		$filename =~ s/ DD *5 1 / (dd5.1 snd) /g;
		## _401_(xvid) is not acceptible
		#xvid-whatever changes / xvid)-whatever actually
		$filename =~ s/hdtv-TTT/hdtv/i;
		$filename =~ s/\(?xvid\)?-gnarly/(xvid)/i;				
		$filename =~ s/\(?xvid\)?-LOL/(xvid)/i;				
		$filename =~ s/\(?xvid\)?-BitMeTV/(xvid)/i;
		$filename =~ s/\(?xvid\)?-NBS/(xvid)/i;
		$filename =~ s/\(?xvid\)?-TBS/(xvid)/i;
		$filename =~ s/\(?xvid\)?-TTT /(xvid) /i;
		$filename =~ s/\(?xvid\)?-umd /(xvid) /i;
		$filename =~ s/H 264_HoodBag/(h264)/i;
		$filename =~ s/\(?xvid\)?-etach[\s]*/(xvid) /i;
		$filename =~ s/\(?xvid\)?-SSTV /(xvid) /i;
		$filename =~ s/\(?xvid\)?-xor /(xvid) /i;
		$filename =~ s/\(?xvid\)?-fqm/(xvid)/i;
		$filename =~ s/\(?xvid\)?-kyr/(xvid)/i;
		$filename =~ s/\(?xvid\)?-aAF/(xvid)/i;
		$filename =~ s/\(?xvid\)?-omicron/(xvid)/i;
		$filename =~ s/\(?xvid\)?-MEDiEVAL/(xvid)/i;
		$filename =~ s/\(?xvid\)?-crimson/(xvid)/i;
		$filename =~ s/\(?xvid\)?-NoTV/(xvid)/i;
		$filename =~ s/\(?xvid\)?-2hd/(xvid)/i;
		$filename =~ s/([^\s])\(xvid\)/$1 (xvid)/i;
		$filename =~ s/\(xvid\)-SAiNTS/(xvid)/i;
		$filename =~ s/\(xvid\)-SAPHiRE/(xvid)/i;
		$filename =~ s/x264-CTU/(x264)/i;
		$filename =~ s/x264-DON/(x264)/i;
		$filename =~ s/x264-HAiDEAF/(x264)/i;
		$filename =~ s/\(x264\)-CTU/(x264)/i;
		$filename =~ s/\(x264\)-aaf/(x264)/i;
		$filename =~ s/\(xvid\)-CTU/(xvid)/i;
		$filename =~ s/\(xvid\)-TVT/(xvid)/i;
		$filename =~ s/\(xvid\)-CRiMSON/(xvid)/;
		$filename =~ s/\(xvid\)-wat/(xvid)/;
		$filename =~ s/\(xvid\)-sys/(xvid)/i;
		$filename =~ s/\(xvid\)-ffndvd/(xvid)/i;
		$filename =~ s/\(ws\)/(widescreen)/;
		$filename =~ s/Ws / (widescreen) /;
		$filename =~ s/ ITunes / (web-rip) /i;
		$filename =~ s/WEB[\-\s]DL/(web-rip)/i;

		$filename =~ s/([a-z]) EP([0-9][0-9])/$1 - $2/;			#"adventures ep01" should be "adventures - 01"

		$filename =~ s/ 720p\./ (720p)./i;
		$filename =~ s/ DTS / (dts) /;

	}	#endif $isVideo


	#print "echo !!!!! currentNewName is $filename \n";
    if ($filename =~ /(\([^\)]* - )(just the [a-z\s]+\))/i)
    {
        my $lcd2 = lc($2);
        my $new = "$1$lcd2";
        #print "echo !!!!! \$1/\$2 is $1/$2, while \$lcd2 is $lcd2\necho !!!!! new is $new\n";
        $filename =~ s/$1$2/$new/;
    }#endif

    #Arts 'n Crass
    $filename =~ s/ 'n / 'N /;



    ##### Certain beginnings should not be in capitals, because they
    ##### are descriptions of the file and not titles
    foreach (@DONOTCAPITALIZE)
           #{ my $lc = lc $_; $filename =~ s/^$_ - /$lc - /; }		#worked for years, but doesn't lowercase normalization report
            { my $lc = lc $_; $filename =~ s/^$_/$lc/; }			#20081028



    #Mr._Robinson's neighborhood...
    $filename =~ s/\._([a-z0-9])/. $1/g;

	$filename =~ s/ WEB-DL / (web-rip) /i;
	$filename =~ s/HDDVD/hd-dvd-rip/i;
	$filename =~ s/hd-dvd-?rip/(hd-dvd-rip)/i;
	$filename =~ s/( *)BluRay( *)/$1(bluray-rip)$2/;
	$filename =~ s/B[RD]RiP/(bluray-rip)/i;
	$filename =~ s/ UNRATED / (unrated) /;


	$filename =~ s/DVD\s*Rip/(dvd-rip)/i;
	$filename =~ s/\(dvd\)/(dvd-rip)/i;
	$filename =~ s/[_\(\s]dvdrip[_\)\s]/(dvd-rip)/i;
	$filename =~ s/-\(dvd-rip\)/(dvd-rip)/i;
	$filename =~ s/([^\s]*)\(dvd-rip\)([^\s]*)/$1 (dvd-rip) $2/i;
	$filename =~ s/\(English\)//;



	## phenomenon of having -(divx)- and -(dvd-rip)- type strings as a result of other stuff
	$filename =~ s/-\(([^\)]*)\)-/($1)/i;

	if ($DEBUG_TRANSFORMATION) { print ":Checkpoint 055: $filename\n"; }

    $filename =~ s/ Aka / aka /g;
	foreach my $word ("clip","short","music video","commercial","appearance","promo","id") {
			$filename =~ s/ - $word - / - $word - /i;
	}
    #$filename =~ s/ - Clip - / - clip - /g;
	#$filename =~ s/ - Short - / - short - /;
	#$filename =~ s/ - Music Video - / - music video - /;
	#$filename =~ s/ - Commercial(s*) - / - commercial$1 - /;

	$filename =~ s/\(swim\)//;
	$filename =~ s/(-?)timeattack(-?)/$1 time attack$2/;	
	#$filename =~ s/AXCXKZXZAZZZZZZXCK/$1/;

	## PROBLEM:  numbers before a second dash normally do not have spaces
	## SOLUTION: " - " becomes "_"
	## EXAMPLE:  South Park - 809 - Something Wall-Mart This Way Comes.rm
	## EXAMPLE:  The Venture Bros. - 13 - Return To Spider-Skull Island.avi
	#$filename =~ s/(-.*) - /$1_/;
	#stimpy - stupid - humps
	## NEW PROBLEM (4/2008): This sucks for images, so let's not do it for images:
	if (!$isImage) {
		$filename =~ s/(-.*)([0-9]+)\s*- /$1$2_/;
	}


	## S1E01 EpTitle with no underscore before title
	$filename =~ s/(S[0-9]+E[0-9]+) -* *([a-z])/$1_$2/i;
	## Showname S1E01 or Showname - S1E01 with no underscore before S1E01
	#print ":before=$filename\n";#ohohoh
	$filename =~ s/([a-z]) (-?\s?)(S[0-9]+E[0-9]+)/$1 $2 _$3/i;
	#print ": after=$filename .. \$1=$2,\$2=$2,\$3=$3\n";#ohohoh
	## show names like "Showname - S1E01" well since it's season 1, the ep # is the air #
	$filename =~ s/( - )_?(S1E)([0-9]+)/$1$3_$2$3/i;

	if ($DEBUG_TRANSFORMATION) { print ":Checkpoint 075: $filename\n"; }


    ### Get rid of ((nested)) ((parenthesis)):
    $filename =~ s/\(\(/(/g;
    $filename =~ s/\)\)/)/g;
	### And a word(withparensrightafter)
	$filename =~ s/([a-z])(\()/$1 $2/i;

	### misc
	$filename =~ s/x264[-_]2hd/(x264)/i;
	$filename =~ s/ DD2 0 / (dd2.0 snd) /i;


    ### Change certain extensions that are not Clio approved:
    $filename =~ s/ -\.srt/.srt/;								#doesn't really belong here, but - simple kludge to fix specific case
    $filename =~ s/\.ram/.rm/;
    $filename =~ s/\.mpeg?/.mpg/;
    $filename =~ s/\.jpeg?/.jpg/;

	### hdtv ... .pdtv.
	#print "\n:filename1=$filename\n"; #201_Hdtv
	$filename =~ s/\(ws Pdtv\)/(pdtv)/i;
	$filename =~ s/_hdtv/_ hdtv/i;
	$filename =~ s/_pdtv/_ pdtv/i;
	#print ":filename2=$filename\n";   #201_ hdtv.
	$filename =~ s/ hdtv([\s\.])/ (hdtv)$1/i;
	$filename =~ s/ pdtv([\s\.])/ (pdtv)$1/i;
	$filename =~ s/\(HDTV\)/(hdtv)/;
	$filename =~ s/\(PDTV\)/(pdtv)/;
	$filename =~ s/\(hdtv\)/(vidcap)/;		#between 2000 and 2010 things changed, and 'hdtv' started to mean 'vidcap' vs 'webrip', rather than 'hdtv-encoded low-def' vs 'sdtv-encoded low-def'
	#print ":filename3=$filename\n";

	if ($DEBUG_TRANSFORMATION) { print ":Checkpoint 085: $filename\n"; }

	### fix order of things:
	$filename =~ s/(\(?[4806407201080]+p\)?) \((.*)-rip\)/($2-rip) $1/i;

	if ($isVideo) {
		# put parenthesis around years!
		$filename =~ s/ ([12][09][0-9][0-9]) / ($1) /g;
		### Drawn Together - _106_Dsr (xvid)
		#added [^0-9] to stop years like 1943 from getting munged:
		$filename =~ s/ - ([0-9][0-9][0-9][^0-9])/ - _$1/i;  
		### South Park _S8E13_Ds
		$filename =~ s/([a-z\s]) _S([0-9])/$1 - _S$2/i;
		# put parenthesis around x264!
		$filename =~ s/( )(x264)([ \.])/$1($2)$3/ig;
		$filename =~ s/X264/x264/;
		#other stuff
		$filename =~ s/\.*ENG\.x264/ (x264)/i;
		# put parenthesis around 720p/i or 1080p/i!
		$filename =~ s/ (1?[07][28]0[pi])[\- ]/ ($1) /gi;
		$filename =~ s/1080P/1080p/;
		$filename =~ s/1080I/1080i/;
		$filename =~ s/720P/720p/;
		$filename =~ s/720I/720i/;
	}


	if ($DEBUG_TRANSFORMATION) { print ":Checkpoint 087: $filename\n"; }

	### For video files, let's attempt to start extracting codec and FPS type information
	### and inserting it into the filename. this will be a BIG timesaver
	if (($isVideo) && ($filename !~ /\.webm/i) && ($filename !~ /\.mpe?g/i) && ($filename !~ /\.sub/i) && ($filename !~ /\.srt/i) && ($filename !~ /\.idx/i) && ($filename !~ /\.vob/i)) { 
		if ($DEBUG_TRANSFORMATION) { print "&InsertVideoAttributesIntoFilename(filename=$filename,original_filename=$original_filename);\n"; }
		$filename = &InsertVideoAttributesIntoFilename($filename,$original_filename); 
	}

	if ($DEBUG_TRANSFORMATION) { print ":Checkpoint 088 [after InsertVideoAttributesIntoFilename]: $filename\n"; }

	#### HDTV/AC3 sound and such:
	$filename =~ s/\s+$//;	#trailing spaces
	if ($filename =~ /AC3 5[\.\s]1/) {
		#DEBUG: print "\t1* $filename\n";
		$filename =~ s/AC3 5[\.\s]1//;
		#DEBUG: print "\t2* $filename\n";
		$filename =~ s/(\.[a-z][a-z][a-z])$/ (48kHz 5.1 ac3 snd)$1/i;
		#DEBUG: print "\t3* $filename\n";
		$filename =~ s/(S[0-9]?[0-9]E[0-9][0-9]?)_HR/$1_/;
		#DEBUG: print "\t4* $filename\n";
	}

	if ($DEBUG_TRANSFORMATION) { print ":Checkpoint 089: $filename\n"; }

	### encoder-specific stuff, pass 2:
	### sofar this is just stuff that will put things at end before extension as side-effect of, say, encoder who always has credits cut
	$filename =~ s/ Notv / /;
	if ($filename =~ /\(vpc\)/i) {
		$filename =~ s/\(vpc\)//;
		$filename =~ s/^(.*)(\..*?)$/$1 (UR OSD) (credits cut)$2/;
	}


	if ($DEBUG_TRANSFORMATION) { print ":Checkpoint 090: $filename\n"; }


	### new stuff here is maybe a good place to put new stuff
	if ($isAudio) {
		$filename =~ s/^Unknown Artist/unknown artist/ig;
	}


	### more fix order of things: 
	$filename =~ s/1 \(mono\)ch/mono/i;
	$filename =~ s/(\(dd[25]\.[01] snd\))(.*)(\([0-9]*fps\))/$2$3$1/i;
	$filename =~ s/(\(dd[25]\.[01] snd\))(.*)(\([hx]264\))/$2$3$1/i;
	$filename =~ s/(\([^\)]* snd\)) (\([0-9]+fps\))/$2 $1/i;
	$filename =~ s/(\([0-9]+[ip]\)) (\([0-9]+x[0-9]+\)) (\(vidcap\))/$3 $1 $2/i;
	$filename =~ s/(\(xvid\)) *(\([0-9]+x[0-9]+\))/$2 $1/i;
	$filename =~ s/(\(x264\))( *\([0-9]+[pi]\) *\([0-9]+x[0-9]+\))/$2$1/;
	#print "filename[after] =$filename\n";


	### Get rid of ()() parenthesis groups without a space between them
	$filename =~ s/\)\(/) (/g;

	if ($DEBUG_TRANSFORMATION) { print ":Checkpoint 095: $filename\n"; }

	if ($isAudio) {  
		#DON'T WANT: (64kbps) = (64_bps) 
		#WANT: "01 name" into "01_name"
		#filename =~ s/([^0-9][0-9][0-9])[^_012346789]([a-z])/$1_$2/i;
		$filename =~ s/([^0-9][0-9][0-9])[^_012346789kM]([a-z])/$1_$2/i;
		#DEBUG: if ($DEBUG_TRANSFORMATION) { print "\$1=$1,\$2=$2,\$3=$3\n"; }

		$filename =~ s/O'clock/O'Clock/;
	}

	if ($DEBUG_TRANSFORMATION) { print ":Checkpoint 100: $filename\n"; }

	$filename =~ s/dual audio -- /dual audio--/;

	if ($isVideo) {
		# cd 1 of 3, cd 2 of 3, cd 3 of 3 
		# a more advanced version could figure out of 3 is really the magic number
		my $MAGIC_NUMBER=2;															#used 3 in the autogk days but most stuff i susually 1 file or 2 files these days
		$filename =~ s/cd([1-9])/cd $1 of $MAGIC_NUMBER/i;
		# also, if it is "The Pianist cd 1" it should be "The Pianist - cd 1"
		if ($filename =~ /^(.*)(cd [1-9] of [1-9])(.*)(\..*?)$/) {
			#DEBUG 
			#print ": dealing with cd x of x crap for $filename ..\n\t\$1=$1\n\t\$2=$2\n\t\$3=$3\n\t\$4=$4\n";
			$filename = $1 . $3 . $2 . $4;
		}
		$filename =~ s/\)(cd [1-9] of)/) - $1/;
	}


	$filename =~ s/repack/REPACK/ig;		#seems extreme, but repack usually shouldn't be there, it usually means the episode has been repacked, not that repack is part of the title, and thus needs to be removed, thus making it uppercase will draw attention to it

	#extra stuff
	#"- Extra 2_"
	$filename =~ s/ - Extra ([0-9])_/ - extra $1 - /;
	if (($filename =~ / extra /i) && ($filename =~ /\s-\s.*\s-\s/)) {
		$filename =~ s/Interview With/interview with/;
		$filename =~ s/extra - S([0-9]*)_/extra - S$1 - /i;
	}
	$filename =~ s/ ([0-9][0-9])S([0-9])E([0-9][0-9][0-9]) / ($1$2x$3) /;

	## comic book only rules (is_comic)
	if ($isComic) {
		$filename =~ s/ V([0-6])/ v$1/;
		$filename =~ s/ ([0-9][0-9][0-9]?\.)/ #$1/;
		$filename =~ s/spider-?man/Spider-Man/i;
		$filename =~ s/\s+\\(toyjesus-dcp\\)//i;
		$filename =~ s/\(Stryfe13_DCP\)//i;
		$filename =~ s/\(Cypher 2*0\)//i;
		$filename =~ s/The Matrix/Matrix, The/;
		$filename =~ s/\s*\([A-Za-z][a-z]+-DCP\)//;
		$filename =~ s/Star Trek TOS/Star Trek-TOS/i;
		$filename =~ s/Star Trek TNG/Star Trek-TNG/i;
		$filename =~ s/Star Trek DS9/Star Trek-DS9/i;

		#Scanner groups / scanning groups / release groups:
		$filename =~ s/\(A-Team-DCP\)//ig;
		$filename =~ s/SCAN Comic EBook-iNTENSiTY//;
		$filename =~ s/-iNTENSiTY//;
		$filename =~ s/\(Zone\)//;
		$filename =~ s/\(TLK-HD\)//;

		$filename =~ s/(\d)(\([12][90]\d\d\))/$1 $2/;
		$filename =~ s/Covers\)/covers)/;
		$filename =~ s/Doctor Who The/Doctor Who - The/i;

		$filename =~ s/([^a-zA-Z])Jan[\s\.]([12][0-9][0-9][0-9])([^0-9])/$1${2}01$3/;
		$filename =~ s/([^a-zA-Z])Feb[\s\.]([12][0-9][0-9][0-9])([^0-9])/$1${2}02$3/;
		$filename =~ s/([^a-zA-Z])Mar[\s\.]([12][0-9][0-9][0-9])([^0-9])/$1${2}03$3/;
		$filename =~ s/([^a-zA-Z])Apr[\s\.]([12][0-9][0-9][0-9])([^0-9])/$1${2}04$3/;
		$filename =~ s/([^a-zA-Z])May[\s\.]([12][0-9][0-9][0-9])([^0-9])/$1${2}05$3/;
		$filename =~ s/([^a-zA-Z])Jun[\s\.]([12][0-9][0-9][0-9])([^0-9])/$1${2}06$3/;
		$filename =~ s/([^a-zA-Z])Jul[\s\.]([12][0-9][0-9][0-9])([^0-9])/$1${2}07$3/;
		$filename =~ s/([^a-zA-Z])Aug[\s\.]([12][0-9][0-9][0-9])([^0-9])/$1${2}08$3/;
		$filename =~ s/([^a-zA-Z])Sep[\s\.]([12][0-9][0-9][0-9])([^0-9])/$1${2}09$3/;
		$filename =~ s/([^a-zA-Z])Oct[\s\.]([12][0-9][0-9][0-9])([^0-9])/$1${2}10$3/;
		$filename =~ s/([^a-zA-Z])Nov[\s\.]([12][0-9][0-9][0-9])([^0-9])/$1${2}11$3/;
		$filename =~ s/([^a-zA-Z])Dec[\s\.]([12][0-9][0-9][0-9])([^0-9])/$1${2}12$3/;
		#Batman The Dark Knight Vol 2 No 1 Nov 2011.pdf
	}

	if ($DEBUG_TRANSFORMATION) { print ":Checkpoint 110: $filename\n"; }


	#if ($isVideo) {					#let's try applying these to everything
		## some show-specific renames / show names / shownames
		$filename =~ s/AdventureTime /Adventure Time /;
		$filename =~ s/Popeye The Sailer - /Popeye - /;
		$filename =~ s/Spiderman/Spider-Man/gi;
		$filename =~ s/CN - promo/Cartoon Network - promo/i;
		$filename =~ s/^Power Puff/PowerPuff/i;
		$filename =~ s/^Sym-bionic/Sym-Bionic/;
		$filename =~ s/^Space Ghost C2C/SGCTC/i;
		$filename =~ s/southpark/South Park/i;
		$filename =~ s/^Tim And Eric Awesome Show *- */Tim And Eric Awesome Show, Great Job! -/i;
		$filename =~ s/^ppg-/PowerPuff Girls - /i;
		$filename =~ s/that 70s show/That 70's Show/i;
		$filename =~ s/ 70S / 70's /;
		$filename =~ s/^kmfdm/KMFDM/i;
		$filename =~ s/Venture Bros /Venture Bros./i;
		$filename =~ s/The Office Us([\s\-\.])*/The Office$1/i;
	#}




	## post-processing shownames, some names will get mangled by above rules:
	if ($isVideo) {
		$filename =~ s/ WED-DL / (web-dl) /;
		$filename =~ s/Deleted Scene/deleted scene/;

		#dvd-rip, dvd extra, audi ocommentary stuff
		$filename =~ s/\( \(dvd-rip\) \)/(dvd-rip)/i;
		$filename =~ s/audio Commentary/audio commentary/;
		if ($filename =~ / extra/i) {
			$filename =~ s/Dvd Extra/dvd extra/;
			$filename =~ s/Deleted Scenes/deleted scenes$1/;
			$filename =~ s/(dvd.*extra.*) Maybe/$1 maybe/;
			$filename =~ s/Interviews/interviews/;
			$filename =~ s/ Outtake/ outtake/;
		}


		$filename =~ s/Sealab[\s\(\)-_]+2021\)?/SeaLab 2021/i;
		$filename =~ s/([a-z]) - _([0-9][0-9][0-9]) - /$1 - $2 - /i;
		#ter-1x02
		$filename =~ s/([a-z]+)-([1-9])xE?([0-9][0-9])/$1 - _S$2E$3/i;
		$filename =~ s/ - \(/ (/g;
#		$filename =~ s/\) - / )/g;

		# we were getting stuff like: Something - Part 1_ (divx)...
		$filename =~ s/ - Part ([0-9])_ \(/ - part $1 of 2 (/i;		#)))

		$filename =~ s/\(xvid-Vorbis\)/(xvid)/i;

		#(1970s ) should be (1970s)
		$filename =~ s/\(([12][90][0-9][0-9]s) \)/($1)/ig;
		$filename =~ s/\(([12][90][0-9][0-9]s?)\)(_)/($1) - $2/ig;
		$filename =~ s/3Rd/3rd/g;
		$filename =~ s/\(xvid \)cd ([0-9])/(xvid) - cd $1/ig;
		$filename =~ s/fps \)cd ([0-9])/fps) - cd $1/ig;

		#Chapter 13_Shrie
		$filename =~ s/Chapter ([0-9]+)_([a-z])/Chapter $1 - $2/i;

		#Batman-TAS (1990s)14_title should have " - " between ")" and "14"
		$filename =~ s/\(1990s\)([0-9][0-9][ _])/(1990s) - $1/;
		$filename =~ s/(\(19[5-9]0s\))([0-9][0-9]_S[0-9]E[0-9])/$1 - $2/;

		#Babylon 5 (S5E01 )No Compromises (xvid) (24fps).avi
		$filename =~ s/^([^-]+) \((S[0-9]E[0-9][0-9]) *\) */$1 - _$2_/i;

		$filename =~ s/H - _264/(h264)/;
	}#endif isVideo

	if ($DEBUG_TRANSFORMATION) { print ":Checkpoint 150: $filename\n"; }


	if (($isAudio) && ($filename =~ /\.mp3$/i)) {
		my $info   = get_mp3info($original_filename);

		$VBR       = $info->{VBR};
		$bitrate   = $info->{BITRATE};
		$stereo    = $info->{STEREO};
		$frequency = $info->{FREQUENCY};

		#VERSION,LAYER,STEREO,VBR,BITRATE,FREQUENCY,SIZE,SECS,MM,SS,MS,TIME,COPYRIGHT,PADDING,MODE,FRAMES,FRAME_LENGTH,VBR_SCALE 
		if ($DEBUG_BITRATE_TAGGING) { printf "DEBUG: $file length is %d:%d,stereo=%b,bitrate=%d,freq=%d,vbr=%d,vbr_scale=%d,firstBirate=$firstBitrate\n", $info->{MM}, $info->{SS}, $info->{STEREO}, $info->{BITRATE}, $info->{FREQUENCY}, $VBR, $info->{VBR_SCALE}; }
		if ($DEBUG_BITRATE_TAGGING>1)  { print "> ".abs($firstBitrate-$bitrate)."\n"; }

		#Keep track of whether the file encoding in this folder is consistent or not.
		#If it is, we can simply make a zero-byte marker file saying that...
		#If it isn't, then we should modify each filename...
		if ($VBR) { $bitrate="VBR";	}
		if    ($firstBitrate   eq "")         { $firstBitrate             = $bitrate  ; } 
		elsif ((abs($firstBitrate-$bitrate) > $SAME_BITRATE_THRESHOLD) && ($bitrate > 0)) { $BITRATES_ALL_THE_SAME    = 0         ; }
		if    ($firstStereo    eq "")         { $firstStereo              = $stereo   ; } 
		elsif ($firstStereo    != $stereo   ) { $CHANNELS_ALL_THE_SAME    = 0         ; }
		if    ($firstFrequency eq "")         { $firstFrequency           = $frequency; } 
		elsif ($firstFrequency != $frequency) { $FREQUENCIES_ALL_THE_SAME = 0         ; }

	}



	#^^^^^^^^^^>
	############################ NEW STUFF GOES ABOVE HERE

	if ($DEBUG_TRANSFORMATION) { print ":Checkpoint 300: $filename\n"; }

	############################ FINISHING UP!

	##### SPACES, UNDERSCORES AND PERIODS
    ### DAMN I just put this in on 11/8/2000.  I wonder how many have files
    ### have trailing spaces due to me renaming hundreds of files with this!
    $filename =~ s/\s+$//;
	## also beware of more than 1 space:
	$filename =~ s/\s\s/ /g;
	## also beware of an underscore just before the extension/before a dot:
	$filename =~ s/_*\././g;
	## and underscores bewteen_words are proably bad
	$filename =~ s/([a-z])_([a-z])/$1 $2/i;
	## spaces before the externsion make no sense either:
	$filename =~ s/ +(\.[a-z0-9~]{3,4})/$1/i;
	## some stuff should have periods like Dr. Mr. Vs.
	$filename =~ s/([^a-z])Mr ([A-Za-z])/$1Mr. $2/i;
	$filename =~ s/([^a-z])Dr ([A-Za-z])/$1Dr. $2/i;
	$filename =~ s/([^a-z])Vs ([A-Za-z])/$1Vs. $2/i;

	$filename =~ s/ \- \- / - /g;
	$filename =~ s/^Trailer - /trailer - /;
	$filename =~ s/^Trailers - /trailers - /;
	if ($isAudio) { 
		##### fix "Disc 2_Of 3 - " pattern
		$filename =~ s/^Disc (\d+)[_ ]?O?f?[_ ]?\d?[_ ]?\-?[_ ]?/$1_/;


		##### fix broken _ext .ext patterh
		$filename =~ s/_mp3$/.mp3/i;	
		#same for wave. let's write it more generally:
		$filename =~ s/_([^\.][^\.][^\.])$/.$1/i;	
	}

	if ($DEBUG_TRANSFORMATION) { print ":Checkpoint 400: $filename\n"; }

	$filename =~ s/ - Extra - / - extra - /;
	$filename =~ s/extra - Web Exclusive/extra - web exclusive/i;
	$filename =~ s/ - Commercial / - commercial /;

	### started seeing: part 1 of 2_Somet
	$filename =~ s/ Pt([1-2]) /- part $1 of 2/;
	$filename =~ s/ - part ([0-9]) of ([0-9])_([a-z])/ - part $1 of $2 - $3/i;

	### keep quality markers uppercase as intended
	$filename =~ s/\(hq/\(HQ/;   #))))
	$filename =~ s/\(hmq/\(HMQ/; #))))
	$filename =~ s/\(mhq/\(MHQ/; #))))
	$filename =~ s/\(mq/\(MQ/;   #))))
	$filename =~ s/\(mlq/\(MLQ/; #))))
	$filename =~ s/\(lmq/\(LMQ/; #))))
	$filename =~ s/\(lq/\(LQ/;	 #))))
	$filename =~ s/(\([0-9]+)_(kbps\))/$1$2/;	#I added this to change (64_kbps) into (64kbps), but then when i took it out the 64_ thing mysteriously wasn't happening!  I'll leave this in for now since it doesn't currently matter or hurt.

	if ($DEBUG_TRANSFORMATION) { print ":Checkpoint 500: $filename\n"; }

	### NEAR-LAST: NEAR LAST:
	#$filename =~ s///;
	#$filename =~ s///;
	#$filename =~ s///;
	#$filename =~ s///;
	if ($isAudio) { $filename =~ s/^([0-9][0-9])(\.\.\.)/$1_$2/; }
	$filename =~ s/\(1080p\) \(1920x1080\) \(web-rip\)/(web-rip) (1080p) (1920x1080)/i;
	$filename =~ s/\(a opus\)/(h264)/;
	$filename =~ s/\(A E snd\) //;
	$filename =~ s/dts 5.1/5.1 dts/;
	if (($filename =~ /\(1280x720\)/) && ($filename !~ /720p/i)) { $filename =~ s/\(1280x720\)/(720p) (1280x720)/i; }
	$filename =~ s/AAC2 0(.*) (snd\))/$1 aac $2/i;
	$filename =~ s/ 720p / (720p) /;
	$filename =~ s/H264/h264/g;
	$filename =~ s/X264/x264/g;
	$filename =~ s/\(X264\)\-taxes/(x264)/ig;
	$filename =~ s/h264(.*h264)/$1/i;
	$filename =~ s/vorbis-2 0\)/vorbis/;
	$filename =~ s/vorbis(.*vorbis)/$1/i;
	$filename =~ s/divx(.*divx)/$1/i;
	$filename =~ s/ac3-5 1\) (.*ac3.*5\.1.*snd\))/$1/i;
	$filename =~ s/A VORBIS/vorbis/i;
	$filename =~ s/ac3(.*ac3)/$1/i;
	### near-last fix order of things: 
	$filename =~ s/(\([hx]264\)) *(\([0-9]+x[0-9]+\))/$2 $1/i;
	$filename =~ s/(X-Men *)(.*)(\(anime\))/$1$3$2/;
	$filename =~ s/_\(live\)/ (live)/i;
	$filename =~ s/ - Webisode - / - webisode - /;
	$filename =~ s/music video Directed By/music video directed by/i;
	$filename =~ s/\(xvid\)-mac /(xvid) /;
	$filename =~ s/\(mtv com\)/(mtv.com)/i;
	$filename =~ s/(\(tq[0-9]) ([0-9])\)/$1.$2)/i;
	$filename =~ s/CD ([1-3]) of ([1-3])/cd $1 of $2/;
	$filename =~ s/ _720p / (720p) /i;
	$filename =~ s/ Bluray / (bluray-rip) /i;
	$filename =~ s/- \(720p\)/ (720p)/i;
	$filename =~ s/dvd extra - (S[0-9]+)_/dvd extra - $1 - /i;
	$filename =~ s/hissy \)/hissy)/i;
	$filename =~ s/ - Interview/ - interview/;
	$filename =~ s/ Music Video/ music video/;
	$filename =~ s/VTS ([0-9][0-9]_[0-9])/VTS_$1/;
	$filename =~ s/^Commercial(s?) - /commercial$1 - /;
	$filename =~ s/ - _([0-9]{3}-[0-9]{4})_MVI/ - $1/i;
	$filename =~ s/(\(?[4806407201080]+p\)?) \(vidcap\)/(vidcap) $1/i;
	$filename =~ s/ ([HX]264) / ($1) /i;
	if (($filename =~ /\([0-9]+x1080\)/) && ($filename !~ /1080p/i)) {
		$filename =~ s/(\([0-9]+x1080\))/(1080p) $1/i;
	}
	#(24_ps)
	$filename =~ s/\(([0-9]+)_ps\)/($1fps)/;
	$filename =~ s/con - (20[0-9][0-9])_/Con $1 - /i;

	if ($DEBUG_TRANSFORMATION) { print ":Checkpoint 600: $filename\n"; }

	### FIX COMMON ABBREVIATIONS:
	$filename =~ s/ O J / O.J. /;

	$filename =~ s/ h264\- / (h264) /i;
	$filename =~ s/_JPG.jpg$/.jpg/i;
	$filename =~ s/2 \(stereo\)ch/2ch/;
	$filename =~ s/([a-z!]) (S[0-9]+E[0-9]+)/$1 - _$2/i;
	$filename =~ s/LIVE - ([12][0-9][0-9][0-9][01][0-9][0-3][0-9]) /LIVE $1 /i;
	$filename =~ s/ -.mkv/.mkv/i;
	$filename =~ s/H 264_HoodBag/(h264)/i;			#was failing earlier in code
	$filename =~ s/^G I Joe Renegades/G.I. Joe Renegades/gi;		
	$filename =~ s/\(dd5 1\)/(dd5.1)/ig;
	$filename =~ s/ - Parody - / - parody - /;
	$filename =~ s/^Pilot - /pilot - /;
	$filename =~ s/ - (Extras*) - / - $1 - /;
	$filename =~ s/- Fake Commercial -/- fake commercial -/;
	$filename =~ s/\(divx3\)(.*)\(divx3\)/$1 (divx3)/;
	$filename =~ s/Atari - ([257][628]00)/Atari $1/i;
	$filename =~ s/(Atari [257][628]00)_/$1 - /;
	$filename =~ s/Ac3 5 1/5.1 ac3/i;
	$filename =~ s/5 1 Ac3/5.1 ac3/i;
	$filename =~ s/dd2 0 snd/dd2.0 snd/i;
	$filename =~ s/\t/ /g;						#this actually happened once!
	if ($isImage) {
		#Let's also fix this:	20120106 18.49.58.jpg
		$RA=int(rand(10));
		$RB=int(rand(10));
		$filename =~ s/([12][0-9][0-9][0-9][01][0-9][0-3][0-9]) ([0-2][0-9])\.([0-5][0-9])\.([0-5][0-9])/$1 $2$3 - $4$3$2$RA$RB/;
		$filename =~ s/([12]00-[0-9][0-9][0-9][0-9])_/$1 - /;
	}
	$filename =~ s/\(A.AAC 2ch snd\)/(aac 2ch snd)/;


	if ($DEBUG_TRANSFORMATION) { print ":Checkpoint 700: $filename\n"; }

	$filename =~ s/\.nfo$/.txt/i;
	$filename =~ s/dd5 1 snd/dd5.1 snd/;		#long time comin' :)
	$filename =~ s/(\(30fps\))(.*\.avi)/$2/i;	#30fps is considered the default fps for AVI files
	$filename =~ s/ *\(44kHz *snd\).avi/.avi/i;	#44kHz is considered the default kHz for MKV files
	$filename =~ s/ *\(48kHz *snd\).mkv/.mkv/i;	#48kHz is considered the default kHz for MKV files
	$filename =~ s/48kHz(.*)\.mkv/$1.mkv/i;		#48kHz is considered the default kHz for MKV files
	$filename =~ s/A AAC/aac/i;
	$filename =~ s/([\-_ ])File ([0-9]+) of ([0-9]+)/ - file $2 of $3 /i;
	$filename =~ s/Web Series/web series/;
	$filename =~ s/ac3 5\.1/5.1 ac3/i;

	#bad:: 1_05 - I Need Therapy - OMITTED - on Kill The Musicians
	#good: 1_05_I Need Therapy - OMITTED - on Kill The Musicians
	#We'll make this work w/both OMITTED and MISSING
	$filename =~ s/^([0-9]?_?[0-9][0-9]?) - (.*[OM][MI][IS][TS][TI][EN][DG].*)$/$1_$2/;

	$filename =~ s/aac 2ch/2ch aac/i;
	$filename =~ s/DTS-?H?D?(.*dts snd)/$1/;
	$filename =~ s/(\(bluray-rip\))(.*)(\(3\-D\) \(HSBS 3\-D\))/$3$1$2/gi;



	#nearing the end!
	$filename =~ s/ _*480p / (480p) /i;
	if (($filename =~ /vidcap/) && ($filename !~ /osd/i)) { $filename =~ s/(\.[^\.]*$)/ (Osd)$1/; }
	$filename =~ s/\(aac snd\)(.*)\(dd5\.1 snd\)/$1 (dd5.1 aac snd)/ig;
	$filename =~ s/dd5 1/dd5.1/g;
	$filename =~ s/\(aac snd\) \(h264\) \(24fps\)/(h264) (24fps) (aac snd)/;

	$filename =~ s/\(dts\)(.*\([0-9\.a-z ]*dts snd\))/$1/i;
	$filename =~ s/ - wtf - / - WTF - /;
	$filename =~ s/dd2.0 snd/dd snd/;
	$filename =~ s/ \(65_x480\) / (655x480) /;			#a rarity to come by
	$filename =~ s/\(1080([pi])\) \(1920x800\) \(bluray-rip\)/(bluray-rip) (1080$1) (1920x800)/; 
	$filename =~ s/\(720([pi])\) \(1920x800\) \(bluray-rip\)/(bluray-rip) (1080$1) (1920x800)/; 
	$filename =~ s/11024 *snd/11kHz snd/g;
	$filename =~ s/22048 *snd/22kHz snd/g;
	$filename =~ s/ MVI - ([0-9][0-9][0-9][0-9])/ MVI_$1 /i;
	$filename =~ s/ IMG - ([0-9][0-9][0-9][0-9])/ IMG_$1/i;
	$filename =~ s/dts 8ch snd/7.1 dts snd/i;

	if ($DEBUG_TRANSFORMATION) { print ":Checkpoint 800: $filename\n"; }


	$filename =~ s/\(aac\)(.* snd)/$1 aac snd)/;
	$filename =~ s/ - Song - / - song - /i;
	$filename =~ s/ac3 2ch snd/2ch ac3 snd/i;
	$filename =~ s/11025 snd/11kHz snd/i;

	$filename =~ s/^cats Millionaire/Cats Millionaire/;
	$filename =~ s/(mono snd.*)(\(mono snd\))/$1/i;
	$filename =~ s/\.(\(\d+x\d+\))/ $1/i;
	$filename =~ s/(\(aac snd\))(.*\(\d+fps\))/$2$1/i;
	$filename =~ s/\) WEB \(/) (web-rip) (/i;
	$filename =~ s/Tim And Erics Bedtime Stories/Tim And Eric's Bedtime Stories/i;
	$filename =~ s/(\(\d+p\)) (\(\d+x\d+\)) \(bluray-rip\)/(bluray-rip) $1 $2/i;
	$filename =~ s/\(aac snd\) \(h264\) \(24fps\)/(h264) (24fps) (aac snd)/i;
	$filename =~ s/dts 2ch snd/2ch dts snd/i;
	$filename =~ s/ *(\.flv)/$1/;
	$filename =~ s/22050 mono snd/22kHz mono snd/i;
	$filename =~ s/22050 snd/22kHz snd/i;
	$filename =~ s/aac aac/aac/i;
	$filename =~ s/ \- \- / - /g;
	$filename =~ s/\(\)//g;
	$filename =~ s/\)\(/) (/g;
	$filename =~ s/\( /(/g;						#)))))))))))
	$filename =~ s/ +(\.cb[rz])$/$1/gi;
	$filename =~ s/(DD51)(.*)(ac3 snd)/${2}dd $3/;
	$filename =~ s/ -Cyphanix //;
	$filename =~ s/\(Phr0sty\)//;
	$filename =~ s/\(A FLAC/(flac/i;			#)))))))))))
	$filename =~ s/\(A TRUEHD/(TrueHd/i;		#)))))))))))
	$filename =~ s/5 1 dts snd/5.1 dts snd/;
	$filename =~ s/7 1 dts snd/7.1 dts snd/;
	$filename =~ s/(\(\d{2,}0[ip]\))(.*)(\(web-dl\))/$3$2$1/;
	$filename =~ s/Windows Media Audio/WMA/g;
	$filename =~ s/a mpeg -- l2 2ch snd/mpg 2ch snd/;
	$filename =~ s/TrueHd 8ch snd/7.1 TrueHD snd/;
	$filename =~ s/A? ?MPEG\/L2/mpg/;
	$filename =~s/\(44kHz 1ch snd\) \(mono snd\)/(44kHz mono snd)/;
	$filename =~ s/^Adventure Time - /Adventure Time With Finn And Jake - /ig;		
	$filename =~ s/Fishcenter LIVE /Fishcenter Live /;
	$filename =~ s/_\[\]\.jpg/.jpg/i;
	$filename =~ s/\(([0-9]+)m0s\)/(${1}min)/ig;		#change (25m0s) to (25min)

	if ($DEBUG_TRANSFORMATION) { print ":Checkpoint 900: $filename\n"; }

	if ($isAudio) {
		$filename =~ s/^\(([0-9][0-9]*)\) */$1_/;
		$filename =~ s/_flac$/.flac/i;
	}
	$filename =~ s/11025 snd/11kHz snd/;
	$filename =~ s/22050 snd/22kHz snd/;
	$filename =~ s/22050 /22kHz /i;
	$filename =~ s/A_TRUEHD/TrueHD/i;

	
	## LAST IMAGE RULES
	if ($DEBUG_TRANSFORMATION) { print ":Checkpoint 950: $filename\n"; }
	if ($isImage) {			
		#dropbox image filenames	
		if ($filename =~ /^([12]\d{3}[01]\d[0-3]\d) ([0-2]\d)([0-5]\d) - /) {
			$tmp1     = "$1 $2$3 help";
			$tmpMMSS  = "$2$3";
			$tmpMM    =  $2;
			$tmpSS    =  $3;
			$filename =~ s/^$tmp1 - $tmp1 *\-* */$tmp1 - /;
			$filename =~ s/^($tmp1 - .*)$tmp1 - (.*)$/$1$tmpMMSS$tmpMM/;
		}


		#eliminate patterns like 20180427 1646 - fashion show - 20180427 1646 - 21461699.jpg
		if ($filename =~ /^([12][0-9][0-9][0-9])([01][0-9])([0-3][0-9]) ([0-2][0-9])([0-5][0-9]) - /) {
			$tmp1="$1$2$3 $4$5 - "  ; $filename =~ s/^($tmp1)(.*)($tmp1)/$1$2/;
			$tmp2="$1$2$3 $4\.$5 - "; $filename =~ s/^($tmp1)(.*)($tmp2)/$1$2/;
		}
	}
	if ($DEBUG_TRANSFORMATION) { print ":Checkpoint 999: $filename\n"; }
	#$DEBUG_TRANSFORMATION=0;
	
	
	### ^^^^^^^^^^^^^^^^^^---- ALMOST FINAL RULE:
	$filename =~ s/\(1080p\) \(1920x1080\) \(web-rip\)/(web-rip) (1080p) (1920x1080)/;
	$filename =~ s/\(A E snd\)//;
	$filename =~ s/\)\)\./)./g;
	$filename =~ s/\//--/g;
	$filename =~ s/snd aac snd/aac snd/i;
	$filename =~ s/\(1920x1080\) \(REPACK\)/(repack) (1920x1080)/i;
	$filename =~ s/5 1 snd\)/5.1 snd)/i;
	#$filename =~ s///i;
	#$filename =~ s///i;

	if ($DEBUG_TRANSFORMATION) { print ":Checkpoint 1000: $filename\n"; }
	$filename =~ s/METCON\-//i;




	
	$filename =~ s/ \- \- / - /gi;
	$filename =~ s/  / /g;						#good for a final final cleanup

	if ($NEW_CAMERA_IMAGE_MODE) { goto INHERITED_RENAMINGS_DONE; }			#this is for incoming video more than incoming pictures - suppress inherited renamings for newpics, it just screws things up

	################ INHERITENCE / INHERITED RENAMINGS:
	####roll back renaming 

	#dev test logs:
	#should not rollback but does:
	#[A:isV=1,isA=0,ch=0,orig_filebase=Terminator.Genisys.2015.1080p.BluRay.x264-SPARKS,
	#baseRenamingsForThatFilebase=Terminator.Genisys.2015.1080p.BluRay.x264-SPARKS] -- 
	#[BFWM:YES][IV+IA+NC:NO]
	#[[[[[ROLLBACK YES: Terminator Genisys (2015) (2h05m43s) (bluray-rip) (1080p) (1920x808) (x264)-SPARKS (24fps) (5.1 ac3 snd).mkv TO OG OF Terminator.Genisys.2015.1080p.BluRay.x264-SPARKS.mkv!!!!]]]]]
	#
	#should rollback but does not:
	#[A:isV=1,isA=0,ch=1,orig_filebase=terminator.genisys.2015.1080p.bluray.x264-sparks,
	# baseRenamingsForThatFilebase=terminator.genisys.2015.1080p.bluray.x264-sparks] 
	#-- [BFWM:NO][[[[[ROLLBACK NO: Terminator Genisys (2015) (1080p) (bluray-rip) (x264)-sparks.txt!!]]]]]
	# [B] [D] -- BASE_RENAMINGS NOT updated 	 ... original_filename: terminator.genisys.2015.1080p.bluray.x264-sparks.nfo

	#[A:isV=1,isA=0,ch=1,orig_filebase=terminator.genisys.2015.1080p.bluray.x264-sparks,
	#     baseRenamingsForThatFilebase=terminator.genisys.2015.1080p.bluray.x264-sparks] -- [BFWM:NO][[[[[ROLLBACK NO: Terminator Genisys (2015) (1080p) (bluray-rip) (x264)-sparks.txt!!]]]]]
	 #[B] [D] -- BASE_RENAMINGS NOT updated 	 ... original_filename: terminator.genisys.2015.1080p.bluray.x264-sparks.nfo


	#[A:isV=1,isA=0,ch=1,orig_filebase=terminator.genisys.2015.1080p.bluray.x264-sparks,
	#     baseRenamingsForThatFilebase=terminator.genisys.2015.1080p.bluray.x264-sparks] -- 
	#[BFWM:NO][[[[[ROLLBACK NO: Terminator Genisys (2015) (1080p) (bluray-rip) (x264)-sparks.txt!!]]]]]

	#[A:isV=1,isA=0,ch=1,orig_filebase=terminator.genisys.2015.1080p.bluray.x264-sparks,baseRenamingsForThatFilebase=terminator.genisys.2015.1080p.bluray.x264-sparks] -- [BFWM:NO]
	#[[[[[ROLLBACK NO: Terminator Genisys (2015) (1080p) (bluray-rip) (x264)-sparks.txt!!]]]]]


	my $rollback=0;
	my $originalFilebaseForThisLine = $ORIGINAL_FILEBASES{$lineNum};			if ($DEBUG_INHERITED_RENAMINGS) { print "\n[A:isV=$isVideo,isA=$isAudio,ch=$cheating_NotReallyVideo,orig_filebase=$originalFilebaseForThisLine,baseRenamingsForThatFilebase=".$BASE_RENAMINGS{uc($originalFilebaseForThisLine)}."] -- "; }
	if ($BASE_FILENAMES_WITH_MEDIA{$originalFilebaseForThisLine} eq "1") {		if ($DEBUG_INHERITED_RENAMINGS) { print "[BFWM:YES]"; }
		$rollback=1;
		if (($isVideo || $isAudio) && !$cheating_NotReallyVideo) { 
			$rollback=0;														if ($DEBUG_INHERITED_RENAMINGS) { print "[IV+IA+NC:YES]"; }
		} else {																if ($DEBUG_INHERITED_RENAMINGS) { print "[IV+IA+NC:NO]"; }
		}
	} else {																	if ($DEBUG_INHERITED_RENAMINGS) { print "[BFWM:NO]"; }
	}
	if ($rollback) {															if ($DEBUG_INHERITED_RENAMINGS) { print "\n[[[[[ROLLBACK YES: $filename TO OG OF $original_filename!!!!]]]]]\n"; }
		$filename = $original_filename;
	} else {																	if ($DEBUG_INHERITED_RENAMINGS) { print "\n[[[[[ROLLBACK NO: $filename!!]]]]]\n"; }
	}

	### TRACK THIS SET OF RENAMINGS AS BEING THE OFFICIAL/BEST RENAME FOR THIS BASE FILE:
	### RULES:  IF BASE_RENAMINGS NOT DEFINED FOR THIS FILEBASE, ADD IT.
	###         IF IT            *IS* DEFINED, THEN WE ONLY NEED TO UPDATE IT IF IT IS A SUPERIOR TYPE.
	###					SO IF THE CURRENT TYPE IS AUDIO/VIDEO - YES
	###                 BUT NOT IF IT'S VIDEO and also "CHEATING VIDEO" {files that we want renamed in the same manner as videos are marked as videos but also as cheating videos becuase they aren't really videos}
	$new_filenameNoExt=&remove_extension($filename);
	my $UpdateBaseRenamings=0;
	if (($original_filenameNoExt ne $new_filenameNoExt)		#if a rename occurred
	      && ($new_filenameNoExt ne "")						#and it wasn't such a shitty rename that we have NO filebase left (derp)
	) {

		# [A:isV=1,isA=0,ch=0,orig_filebase=Vacation.2015.1080p.WEB-DL.X264.AC3-EVO,
		#	  baseRenamingsForThatFilebase=Vacation.2015.1080p.WEB-DL.X264.AC3-EVO] -- BASE_RENAMINGS NOT updated 	 ... original_filename: Vacation.2015.1080p.WEB-DL.X264.AC3-EVO.mkv

		$UpdateBaseRenamings=0;												#do nothing by default

		if ($BASE_RENAMINGS{uc($original_filenameNoExt)} eq "") {			#comment possibly wrong: just being redundant here, but: if a rename already exists...
			$UpdateBaseRenamings=1;                                         #comment possibly wrong: ...then don't update anything.  Doing so is an override of default conditions.
		}
		if ($BASE_RENAMINGS{uc($original_filenameNoExt)} ne "") {			#comment possibly wrong: but if it is defined
			$UpdateBaseRenamings=0;											#and
			if ($DEBUG_INHERITED_RENAMINGS) { print " [B]"; }
			if (($isVideo || $isAudio) && !$cheating_NotReallyVideo) {		#only update it if it's a superior type {but not cheating}
				if ($DEBUG_INHERITED_RENAMINGS) { print " [C]"; }
				$UpdateBaseRenamings=1;										#and
			} else {														#...
				if ($DEBUG_INHERITED_RENAMINGS) { print " [D]"; }
				$UpdateBaseRenamings=0;										#don't if it isn't!		
			}
		}

		if ($UpdateBaseRenamings) {											if ($DEBUG_INHERITED_RENAMINGS) { print "\n -- setting BASE_RENAMINGS{".uc($original_filenameNoExt)."}=$new_filenameNoExt \t ... original_filename: $original_filename"; }
			$BASE_RENAMINGS{uc($original_filenameNoExt)}=$new_filenameNoExt;
			$FILENUM_ALREADY_BASERENAMED[$lineNum]=1;
			#no $BASE_RENAMINGS{$ORIGINAL_FILEBASES{$lineNum}}=$new_filenameNoExt;
			#no if ($DEBUG_INHERITED_RENAMINGS) { print " -- setting BASE_RENAMINGS{\$ORIGINAL_FILEBASES{$lineNum}=".$ORIGINAL_FILEBASES{$lineNum}."}=$new_filenameNoExt \t ... original_filename: $original_filename"; }
		} else {															if ($DEBUG_INHERITED_RENAMINGS) { print " -- BASE_RENAMINGS NOT updated \t ... original_filename: $original_filename"; }
		}																	if ($DEBUG_INHERITED_RENAMINGS) { print "\n"; }
	}

	INHERITED_RENAMINGS_DONE:												#this is a label we GOTO to just to avoid indentation
	$kludge=1;																#apparently you can't have 2 labels in a row?!?!?!?!?
	SKIP_PROCESSING:														#this is a label we GOTO to just to avoid indentation

	### DONE MASSAGING FILENAME, PRINT IT OUT:
    $NEW_FILELIST .= "$filename\n";                 #print the (possibly) new name
}#endwhile



if ($DEBUG_INHERITED_RENAMINGS) { print "** 1ST PASS FILELIST: \n$NEW_FILELIST\n"; }


#DEBUG: print "[a] newfilelist=\n$NEW_FILELIST\n";#


#DEBUG:print "Should we do a 2nd pass? if (($BITRATES_ALL_THE_SAME==1) && ($FREQUENCIES_ALL_THE_SAME) && ($CHANNELS_ALL_THE_SAME))\n";

##### SECOND PASS FOR MP3 STUFF.....
if (($BITRATES_ALL_THE_SAME==1) && ($FREQUENCIES_ALL_THE_SAME) && ($CHANNELS_ALL_THE_SAME)) {
	#This situation (roughly equivalent) is covered below.
} else {
	#DEBUG: print "Yes!\n";

	#2nd pass only to put bitrates into individual mp3 files!
	my $SECONDPASS_FILELIST = "";
	my $lineNum=0;
	my $original_filename;
	my @LINES2NDPASS = split(/\n/,$NEW_FILELIST);
	foreach $filename (@LINES2NDPASS) {
		$original_filename = $filename;
		$lineNum++;
		if ($filename =~ /\.mp3$/i) {

			my $info = get_mp3info($original_filenames[$lineNum]);

			$VBR       = $info->{VBR};
			$bitrate   = $info->{BITRATE};
			$stereo    = $info->{STEREO};
			$frequency = $info->{FREQUENCY};

			#VERSION,LAYER,STEREO,VBR,BITRATE,FREQUENCY,SIZE,SECS,MM,SS,MS,TIME,COPYRIGHT,PADDING,MODE,FRAMES,FRAME_LENGTH,VBR_SCALE 
			if ($DEBUG_BITRATE_TAGGING  ) { printf "DEBUG: $file length is %d:%d,stereo=%b,bitrate=%d,freq=%d,vbr=%d,vbr_scale=%d,firstBirate=$firstBitrate\n", $info->{MM}, $info->{SS}, $info->{STEREO}, $info->{BITRATE}, $info->{FREQUENCY}, $VBR, $info->{VBR_SCALE}; }
			if ($DEBUG_BITRATE_TAGGING>1) { print "> ".abs($firstBitrate-$bitrate)."\n"; }

			#Keep track of whether the file encoding in this folder is consistent or not.
			#If it is, we can simply make a zero-byte marker file saying that...
			#If it isn't, then we should modify each filename...
			if ($VBR) { $bitrate="VBR";	} else { $bitrate.="kbps"; }
			my $chans="";
			if (!$stereo) { $chans=" (mono)"; }
			my $freq="";
			if ($frequency !~ /^44/) { 
				$frequency =~ s/22\.05/22/i;
				$frequency =~ s/11\.025/11/;	#11kHz
				$freq = " ($frequency"."kHz)"; 
			}
			#DEBUG: print "filename[a]=$filename\n";
			my $newinfo =  " ($bitrate)$freq$chans";
			$newinfo =~ s/\) \(/ /gi;
			if (( $filename =~ /[0-9]kbps/) || ($filename =~ /\(VBR\)/ )) {				#if the info is already in a file
				#don't put info in there; do nothing
			} else {
				$filename =~ s/(\.mp3)$/$newinfo$1/i;									#but if it's not in there, put it in!
			}
			$filename =~ s/ \(kbps kHz mono\)//i;	#sometimes this happens - it shouldn't
			#DEBUG: print "filename[b]=$filename\n";
		}#endif mp3

		$filename =~ s/ *\(11024 snd\)/ (11kHz snd)/i;			#bug elsewhere makes this, let's just fix it here; easier

		##### STOP AUTO-NAMING LOGIC FROM HAPPENING WHEN CAROLYN USES THIS:
		if ($ENV{"username"} =~ /^carolyn$/i) { $SECONDPASS_FILELIST .= "$original_filename\n"; } 
		else                                  { $SECONDPASS_FILELIST .=          "$filename\n";	}


		if ($DEBUG_TRANSFORMATION) { print ":Checkpoint 1500: original_filename=$original_filename, filename=$filename\n"; }

	}
	$NEW_FILELIST = $SECONDPASS_FILELIST;
}






##### THIRD PASS FOR INHERITED RENAMINGS.....
if ($NEW_CAMERA_IMAGE_MODE) { goto INHERITED_RENAMINGS_DONE2; }			#this is for incoming video more than incoming pictures - suppress inherited renamings for newpics, it just screws things up
my  $DO_THIRD_PASS=1;
if ($DO_THIRD_PASS) {
			my @LINES3RDPASS = split(/\n/,$NEW_FILELIST);
			my $THIRDPASS_FILELIST="";
			my $current3rdPassFileBase="";
			my $tmpBaseNameUsedInAPreviousRenaming="";
			my $newName="";
			my $fileNum=0;
			foreach $current3rdPassFileName (@LINES3RDPASS) {
				$fileNum++;
				chomp $current3rdPassFileName;
				
				$current3rdPassFileBase = &remove_extension($current3rdPassFileName);		
#NO!			$current3rdPassFileBase = $ORIGINAL_FILEBASES{$fileNum};
				$tmpFileExt  =    &get_extension($current3rdPassFileName);		
				if ($DEBUG_INHERITED_RENAMINGS) {
					print "[3rd pass]       tmpFileName=$current3rdPassFileName ...... current3rdPassFileBase=$current3rdPassFileBase [ext=$tmpFileExt]\n";
					print "          [O]\$BASE_RENAMINGS{".uc($current3rdPassFileBase)."}=".$BASE_RENAMINGS{uc($current3rdPassFileBase)}."\n";
				}

					my $originalFileBaseForThisLine      = $ORIGINAL_FILEBASES{$fileNum};
					my $BaseRenamingForOriginalFileBase  = $BASE_RENAMINGS{uc($originalFileBaseForThisLine)};		
					my $thisFileNumberAlreadyBaseRenamed = $FILENUM_ALREADY_BASERENAMED[$fileNum];
					                      
					if ($DEBUG_INHERITED_RENAMINGS) {
						print "\tmy \$originalFileBaseForThisLine      = ".$ORIGINAL_FILEBASES{$fileNum}                    .";\n";
						print "\tmy \$BaseRenamingForOriginalFileBase  = ".$BASE_RENAMINGS{uc($originalFileBaseForThisLine)}.";\n";
						print "\tmy \$thisFileNumberAlreadyBaseRenamed = ".$FILENUM_ALREADY_BASERENAMED[$fileNum]           .";\n";
					}

					#	my $originalFileBaseForThisLine      = Vacation.2015.1080p.WEB-DL.X264.AC3-EVO;
					#	my $BaseRenamingForOriginalFileBase  = Vacation (2015) (1h38m59s) (web-rip) (1080p) (1912x792) (x264) -EVO (24fps) (5.1 ac3 snd);
					#	my $thisFileNumberAlreadyBaseRenamed = ;
					#       ************* NEWNAME=Vacation.2015.1080p.WEB-DL.X264.AC3-EVO.nfo

					if (($BaseRenamingForOriginalFileBase ne $current3rdPassFileBase) && ($BaseRenamingForOriginalFileBase ne "") &&
						(!$thisFileNumberAlreadyBaseRenamed)) {
						$current3rdPassFileBase = $BaseRenamingForOriginalFileBase;														if ($DEBUG_INHERITED_RENAMINGS) { print "[UPDATING!!]"; }
					}
				#}

				$newName = $current3rdPassFileBase . "." . $tmpFileExt;

				if ($DEBUG_INHERITED_RENAMINGS) {
					print "       ************* NEWNAME=$newName\n";
					print "---------- \n";
				}
				$THIRDPASS_FILELIST .= "$newName\n";
			}

			##### NOW THAT WE'RE DONE, PRINT OUT THE FILELIST:
			$NEW_FILELIST = $THIRDPASS_FILELIST;
}


INHERITED_RENAMINGS_DONE2:													#GOTO label for skipping over section without increasing indentation level

print $NEW_FILELIST;
#DEBUG: print "Done!\n";




#DEBUG: if ($DEBUG_BITRATE_TAGGING) { print "* vid/aud = $numVideoFiles / $numAudioFiles ... if (($BITRATES_ALL_THE_SAME==1) && ($FREQUENCIES_ALL_THE_SAME) && ($CHANNELS_ALL_THE_SAME)&& ($numVideoFiles    <=    5) && ($numAudioFiles  >=  5)) \n"; }



##### IF WE HAD CONSISTENT FILE-ENCODING INFORMATION (FOR MP3 FOLDERS), 
##### MAKE A ZERO-BYTE FILE INDICATING THIS, IN THE FORM I WISH AUTOMATICALLY.
##### AN MP3 FOLDER HAS AT LEAST 5 MP3S AND NO MORE THAN 5 VIDEO FILES...

#DEBUG: print "if (($BITRATES_ALL_THE_SAME==1) && ($FREQUENCIES_ALL_THE_SAME) && ($CHANNELS_ALL_THE_SAME) && ($numVideoFiles <= 5) && ($numAudioFiles  >=  3)) \n";



if (($BITRATES_ALL_THE_SAME==1) && ($FREQUENCIES_ALL_THE_SAME) && ($CHANNELS_ALL_THE_SAME) 
								&& ($numVideoFiles    <=    5) && ($numAudioFiles  >=  3)) {
	my $filenameNoteFilename="";
	my $niceFrequency = $firstFrequency;
	$niceFrequency =~ s/44\.1/44/;		#44kHz
	$niceFrequency =~ s/11\.025/11/;	#11kHz

	if ($niceFrequency eq "44") { $niceFrequency=""; } else { $niceFrequency=" ".$niceFrequency."kHz"; }

	$filenameNoteFilename .= "__ ";
	$filenameNoteFilename .= $firstBitrate;
	if ($firstBitrate !~ /VBR/i) { $filenameNoteFilename .= "kbps"; }
	$filenameNoteFilename .= $niceFrequency;
	$filenameNoteFilename .= " __";

	##### Keep track of what kinds of files make up this folder, so we can decide if it's an album/music folder or not:
	if ($filenameNoteFilename eq "__ kbps kHz __") {
		$filenameNoteFilename = "__ VBR __";
	}

	##### A folder full of FLACs incorrectly gets flagged as "__ VBR __" and not the "__ flac source __" we'd ideally like:
	if (($NUM_FILES_BY_EXTENSION{"flac"} > $NUM_FILES_BY_EXTENSION{"mp3"}) && ($filenameNoteFilename eq "__ VBR __")) {
		#####20221118 - no longer doing this because we are now accepting actual FLAC files into our collection:
		#$filenameNoteFilename = "__ flac source __";
		#####instead, setting it to empty string so that we don't create one at all:
		$filenameNoteFilename = "";
	}

	##### Actually add (or not, if it's already there) the zero byte file indicating our bitrate/source info:
	if ("" == $filenameNoteFilename) {
		print "***** NOT ADDING ZERO-BYTE FILE BECAUSE WE HAVE NONE TO ADD *****\n";
	} elsif (-e $filenameNoteFilename) {
		print "***** NOT ADDING ZERO-BYTE FILE BECAUSE IT ALREADY EXISTS: $filenameNoteFilename ***\n";
	} else {
		print "***** ADDING ZERO-BYTE FILE: ******     $filenameNoteFilename\n";
		open (ZEROBYTEFILE,">$filenameNoteFilename");
		close(ZEROBYTEFILE);
	}
}

##############################################################################
################################## END MAIN ##################################
##############################################################################




























































































##############################################################################
sub InsertVideoAttributesIntoFilename {
	my $filename          = $_[0];						
	my $original_filename = $_[1];	
	$original_filename    =~ s/ *$//i;  #no trailing spaces!
	$filename             =~ s/ *$//i;	#no trailing spaces!
	$filename             =~  /^(.*)(\..*?)$/;
	my $extension         = $2;
	my $base              = $1;         if ($base eq "") { $base=$filename; $extension=""; } 
	my $LIB2011           = 0;

	if ($DEBUG_TRANSFORMATION) { print ":Checkpoint IVAIF 000: filename=$filename / base=$base , extension=$extension\n"; }
	$base =~ s/\s+$//;	#remove trailing spaces, a 1off prob
	if ($DEBUG_TRANSFORMATION) { print ":Checkpoint IVAIF 005: filename=$filename / base=$base , extension=$extension\n"; }

	#DEBUG:	#if (-e $original_filename) { print "\n:$original_filename exists"; } else { print "\n:NOO, it does not exist ($original_filename)"; }	#


	##### GET AND PROCESS VIDEO INFO:
	my %info=();
	my $codec="";
	if (    ($filename =~ /\.mkv/i) || ($filename =~ /\.avi/i) || ($filename =~ /\.flv/i) || ($filename =~ /\.wmv/i)
		||  ($filename =~ /\.mp4/i)						#Yes this is redundant with the next line.. testing something.
	    || (($filename =~ /\.mp4/i) && (!$isVideo))
	    ||  ($filename =~ /\.m4v/i)
	   ) {
		#print "branch 1 - $filename\n";
		$LIB2011=1;
		$info=&ImageInfo($original_filename);
		if ($DEBUG_LIB2011) { print "info for mkv is:\n" . &hashdump($info) . "\n"; }
	} else {
		#print "branch 2 - $filename\n";
		%info=&GetVideoInfo($original_filename);
	}


	##### GET INFO, USING OLD LIBRARY FOR 2000S FILES, NEW LIBRARY FOR 2010S FILES:	
	my $tmpcodec   = "";
	my $tmpfps     = "";
	my $tmpheight  = "";
	my $tmpwidth   = "";
	my $tmpchans   = "";
	my $tmplength  = "";
	my $tmparate   = "";
	my $tmpacodec = "";
	if ($LIB2011) { 
		$tmpfps    = $info->{VideoFrameRate};
		$tmpheight = $info->{ImageHeight};
		$tmpwidth  = $info->{ImageWidth};
		$tmpchans  = $info->{AudioChannels};
		$tmplength = $info->{Duration};
		$tmpcodec  = $info->{VideoCodecID}; 
		$tmparate  = $info->{SampleRate};
		$tmpacodec = $info->{AudioCodecID};
		#$tmp  = $info->{};
		#$tmp  = $info->{};
		#$tmp  = $info->{};
		if ($tmplength eq ""     ) { $tmplength = $info->{PlayDuration}   ; }
		if ($tmpcodec  eq ""     ) { $tmpcodec  = $info->{Compression}    ; }
		if ($tmparate  eq ""     ) { $tmparate  = $info->{AudioSampleRate}; }
		if ($tmpacodec eq "A_AC3") { $tmpacodec = "ac3"                   ; }
		if ($tmpacodec eq "A_DTS") { $tmpacodec = "dts"                   ; }
		if ($tmplength =~ /\.[0-9 ]+s/) { $tmplength =~ s/\.[0-9 ]+s/s/   ; }			#drop "29.04 s" to just "29s"
	} else { 
		$tmpfps    = $info{fps};
		$tmpheight = $info{height};
		$tmpwidth  = $info{width};
		$tmpchans  = $info{achans};
		$tmplength = $info{length};
		$tmpcodec  = $info{vcodec};
		$tmparate  = $info{arate};
		#$tmp  = $info{};
		#$tmp  = $info{};
	}	

	#die "tmpcodec is $tmpcodec!\n";

	#DEBUG:#print "\n:Information on $original_filename successfully gathered...\n\n";
	if (($filename =~ /\(divx\)/i) || ($filename =~ /xvid/i) || ($filename =~ /mjpeg/i) || ($filename =~ /[hx]264/i)) {	#oh changed this on 20060929,20080513
		## DO NOTHING. DON'T GET CODEC. IT'S ALREADY IN THERE.
	} else {
		if     ($tmpcodec =~ /MJPG/   ) { $codec="mjpeg"; } 
		elsif (($tmpcodec =~ /^divx/  ) || ($tmpcodec =~ /^dx5/i)) { $codec="divx" ; }
		elsif (($tmpcodec =~ /^mpeg1$/) && (($extension =~ /mpg$/i) || ($extension =~ /mpeg$/i))) { $codec=""; }
		elsif ($tmpcodec =~ /^V_MPEG4\/ISO\/AVC$/) { $codec="h264"; }													#201106
		#lsif ($$tmpcodec =~ /^$/) { $codec=""; }
		#lsif ($$tmpcodec =~ /^$/) { $codec=""; }
		#lsif ($$tmpcodec =~ /^$/) { $codec=""; }
		else { $codec = lc($tmpcodec); }
		#die "codec is $codec!\n";
	}

	if ($DEBUG_TRANSFORMATION) { print ":Checkpoint IVAIF 020: $filename / base=$base\n"; }

	my $fps="";
	my $resolution="";
	my $vrate="";
	if (($tmpcodec ne "") || ($tmpfps ne "") || ($tmpheight ne "") || ($tmpwidth ne "") || ($info{vrate} ne "")) { 	
		if ($tmpfps > 0) { $fps=&round($tmpfps); }
		if (($tmpheight ne "") && ($tmpwidth ne "")) { 
			$resolution = $tmpwidth . "x" . $tmpheight;																			#DEBUG: print "rez is $resolution\n";
		}
		if ($info{vrate} ne "") { $vrate=$info{vrate}; }
	}
	my $mono=0;
	my $achans=$tmpchans;

	if ($DEBUG_TRANSFORMATION) { print ":Checkpoint IVAIF 040: $filename / base=$base\n"; }


	##### AUTO-TIMESTAMPING:
	my $length=$tmplength;
	my $lengthNice = $length;			#make it look nice
	if ($LIB2011) { 
		$lengthNice =~ s/([0-9]*):([0-9]*):([0-9]*)/$1h$2m$3s/;	
		$lengthNice =~ s/^0*h//i;
		$lengthNice =~ s/^0*m//i;
		$lengthNice =~ s/([0-9]m)0([0-9]s)/$1$2/i;
		$lengthNice =~ s/^0*//i;
	} else {
		$lengthNice =~ s/hr */h/;
		$lengthNice =~ s/min */m/;
		$lengthNice =~ s/sec */s/;
	}
	my $has=0;

	#This next line might be considered a bug - if no length is found, we end up setting has to 1. 
	#It's kind of a lie, because it does NOT have the timestamp.
	#But honestly, this works within my designs.  It only happens when no length is found
	#Since there's no length anyway, there really is nothing to put in!
	#So it's acceptable for $has to be incorrect in this situation.
	if ($filename =~ $lengthNice) { $has=1; } else { $has=0; }					#is it in already?
	#DEBUG:	print "$filename --> length is $lengthNice .. filename has it already=$has\n";


	if ($DEBUG_TRANSFORMATION) { print ":Checkpoint IVAIF 060: $filename / base=$base\n"; }


	#If $has==0, it's not in, so we put it in -- unless it's an episode that has a SxExx type filename
	if (($has==0) && (
						(($base !~ /S[0-9]+E[0-9]+/i) && (&is_show($base)==0))
									||
						($base =~ /Doctor.Who/i)													#whitelist shows that we want to always timestamp even though they are shows
					 )
	) {												
		my $lengthFinal = "($lengthNice)";

		#If the filename has a year, we put it after the year
		if ($base =~  /(\([12][90][0-9][0-9]\))/i) {
			#DEBUG: print "scenario A\n";
			$base =~ s/(\([12][90][0-9][0-9]\))/$1 $lengthFinal/i;
		#If the filename has no year but "(live)", we put it after live
		} elsif ($base =~ /(\(live\))/i) {
			#DEBUG: print "scenario B\n";
			$base =~ s/(\(live\))/$1 $lengthFinal/i;
		#if the file just has parens in general, insert timestamp before first one:
		} elsif ($base =~ /\(.*\)/) {
			#DEBUG: print "scenario D - base is originally $base\n";
			$base =~ s/(^[^\(]+)(\(.*\).*$)/$1 $lengthFinal $2/;
			#DEBUG: print "scenario D - base is now        $base\n";
		#if the file has no parenthesis whatsoever, we put it at the end
		} else {
			#DEBUG: print "scenario C - base is originally $base\n";
			$base .= " $lengthFinal";
			#DEBUG: print "scenario C - base is now        $base\n";
		}
	}
	##### END AUTO-TIMESTAMPING

	#Let's start adding resolution:
#	die "resolution is $resolution, retval=$retval\n";
	if (($resolution ne "") && ($retval !~ /$resolution/)) {
		if ($base =~  /\([72108]*0[pi]\)/) {
			$base =~ s/(\([72108]*0[pi]\))/$1 ($resolution)/i;
		} else {
			$base .= " ($resolution)";
		}
	}

	if ($DEBUG_TRANSFORMATION) { print ":Checkpoint IVAIF 080: $filename / base=$base\n"; }

	if (($info{acodec} ne "") || ($achans ne "") || ($tmparate ne "")) { 
		#if ($info{acodec} ne "") { print $info{acodec}; }
		if (($achans ne "") || ($tmparate ne "")) {
			if ($achans == 1) { $mono=1; }
			if ($tmparate != 44) { $arate=$tmparate; }
		}
	}
	#if ($info{length} ne "") { print "<BR><B>Length:</B> " . $info{length}; }


	##### DEBUG	#	print "\n: codec=$codec,$fps"."fps,mono=$mono,arate=$arate,achans=$achans\n";
	if ($DEBUG_TRANSFORMATION) { print ":Checkpoint IVAIF 100: $filename / base=$base\n"; }


	##### NOW THAT WE HAVE THE INFO, FORMAT THE NEW FILENAME:
	my $retval = $base;
	if (($codec ne "") && ($retval !~ /\($codec\)/))  { $retval .= " ($codec)";	}
	if ($DEBUG_TRANSFORMATION) { print ":Checkpoint IVAIF 110: retval=$retval / filename=$filename / base=$base\n"; }

	if (($base !~ /\([0-9]+fps\)/i) && ($fps ne "") && ($fps ne "29.97")) { 
		if ($DEBUG_TRANSFORMATION) { print ":Checkpoint IVAIF 113: $filename / base=$base\n"; }
		$retval .= " ($fps"."fps)"; 
		if ($DEBUG_TRANSFORMATION) { print ":Checkpoint IVAIF 116: $filename / base=$base\n"; }
	}
	if ($DEBUG_TRANSFORMATION) { print ":Checkpoint IVAIF 120: retval=$retval / filename=$filename / base=$base\n"; }

	if ($tmpchans ne "") { 
		$tmpchans .= "ch"; 
		$tmpchans =~ s/6ch/5.1/i;
	}

	if (($tmparate ne "") && ($retval !~ / snd/)) {
		$arate   =~ s/44100/44kHz/;
		$arate   =~ s/000$/kHz/;
		$retval .= " ($arate $tmpacodec $tmpchans snd)";
	}

	if (($mono) && ($base !~ /mono.*snd/i)) {
		$retval .= "(";
		if ($mono) { $retval .= "mono"; }
		$retval .= " snd)";
	}
	$retval .= $extension;

	if ($DEBUG_TRANSFORMATION || $DEBUG_LIB2011) { print ":Checkpoint IVAIF 140: retval=$retval / filename=$filename / base=$base\n"; }

	##### ELIMINATE DUPE NAMES:
	my $tmpkey=$retval;
	if ($NamesUsed{$tmpkey} == 1) { 
		$retval =~ s/(\.[^\.]+)$/ (dupe)$1/;	
	}
	$NamesUsed{$retval}=1;

	##### AND RETURN IT:
	return($retval);
}#endsub InsertVideoAttributesIntoFilename
###############################################################################




################################################################################################################################################
{
	$last_randcolor;
	sub randcolor_simple {
		my $color_code = int(rand(8)) + 30;
		while ($color_code == $last_randcolor) {
			$color_code = int(rand(8)) + 30;
		}
		$last_randcolor = $color_code;
		return "\e[${color_code}m";
	}
}
################################################################################################################################################



################################################################################################################################################
sub GetVideoInfo {
	#uses global $cheating_NotReallyVideo
	my $real = $_[0];		#the filename to our video
	my %attributes=();

	if ($cheating_NotReallyVideo) {
		#then don't do any of this stuff!!
	} else {
		eval { $info = Video::Info->new(-file=>$real); };
		#$info = Video::Info->new(-file=>$real); };
		if ($DEBUG_VIDEO_ATTRIBUTES) { %tmpattributes=%{$info}; foreach my $key (sort keys %tmpattributes) { print "\t* Tmpattributes{$key}=$tmpattributes{$key}\n"; }  }
		if ($info ne "") {
			my ($fps,$vcodec,$acodec,$length,$achans,$arate,$width,$height,$vframes,$vrate)=("","","","","","","","","","");
			#bless $info;
			eval {			$fps    	= $info->fps();		    };  warn &randcolor_simple() . $real . ":\t " . $@ if $@; #|| warn("asdf");		};
			eval {			$vcodec 	= $info->vcodec();	    };  warn &randcolor_simple() . $real . ":\t " . $@ if $@; #|| warn("asdf"); 		};
			eval {			$acodec 	= $info->acodec();		};	warn &randcolor_simple() . $real . ":\t " . $@ if $@;
			eval {			$vframes	= $info->vframes();		};	warn &randcolor_simple() . $real . ":\t " . $@ if $@;
			eval {			$achans 	= $info->achans();		};	warn &randcolor_simple() . $real . ":\t " . $@ if $@;
			eval {			$arate  	= $info->arate();		};	warn &randcolor_simple() . $real . ":\t " . $@ if $@;
			eval {			$width  	= $info->width();		};	warn &randcolor_simple() . $real . ":\t " . $@ if $@;
			eval {			$height		= $info->height();		};  warn &randcolor_simple() . $real . ":\t " . $@ if $@;
			eval {			$vrate		= $info->vrate();		};  warn &randcolor_simple() . $real . ":\t " . $@ if $@; #vrate doesn't work right
			#print "<BR>length is $length";
			if ($height>0) { $attributes{height}=$height; }
			if ($width >0) { $attributes{width} =$width; }
			#if ($vrate>0) { $attributes{vrate}= $vrate; }
			#print "vrate is $vrate";
			#print ":achans is $achans\n";
			#
			if (($fps>0) && ($vframes>0)) { $length = &round($vframes / $fps); }
			if ($vcodec ne "") { $attributes{vcodec}=&nicecodec($vcodec); }

			#Kludge fix:
			$attributes{achans}=$achans;
			if ($acodec ne "") { 
				$attributes{acodec}=&nicecodec($acodec); 
				if (($achans ne "") || ($arate ne "")) {
					if ($arate ne "") { $attributes{arate} = &round_audio_kbps($arate / 1024) . "kbps"; }
					#this block was good for photo-album, but killing allfiles-mv:
					#if ($achans ne "") {
					#	if ($achans == 0) { $attributes{achans}="broken"; }		#theoretically should not happen
					#	if ($achans == 1) { $attributes{achans}="mono"; }
					#	if ($achans == 2) { $attributes{achans}="stereo"; }
					#	if ($achans >  2) { $attributes{achans}="$achans" . "-channel"; }
					#}
				}
			}
			if ($length ne "") { $attributes{length}=&convert_seconds_to_readable_length($length); }
			if ($fps     >  0) { $attributes{fps}   =&nicefps                           ($fps   ); }
		}
	}

	if ($DEBUG_VIDEO_ATTRIBUTES) { foreach my $key (sort keys %attributes) { print "\t* Attributes{$key}=$attributes{$key}\n"; } print "\n"; }

	return(%attributes);
}#endsub GetVideoInfo
################################################################################################################################################
###############################################################################################
sub nicecodec {
	my $codec = $_[0];

	if ($codec =~ /^DIV([0-9])/) { $codec = "DivX$1"; }
	if ($codec =~ /MPEG Layer ([2-4])/) { $codec = "MP$1"; }
	if ($codec =~ /Uncompressed PCM/) { $codec = "PCM (Uncompressed)"; }

	return $codec;
}#endsub nicecodec
###############################################################################################


##### Including PCM bitrates like 174:
my @AUDIO_BITRATES=(8,16,24,32,48,56,64,80,88,96,112,128,160,174,192,224,256,320);
###########################################################################
sub get_genre_for_one_mp3 {
	###################### UNTESTED
	my $filename = $_[0];

	my ($genrev1,$genrev2)=("","");
	my $id3v2;
	my $tag = MP3::Tag->new($filename); 
	$tag->get_tags();
	if ($tag->{ID3v2} ne "") {
		$id3v2 = $tag->{ID3v2};
		$genrev2 = $id3v2->get_frame(TCON); #no clue what TCON is
	}
	if ($tag->{ID3v1} ne "") { $genrev1 = $tag->{ID3v1}->genre; }
	return($genrev1,$genrev2);
}
###########################################################################

##############################################################################
sub round_audio_kbps {
	my $kbps = $_[0];
	my $ugly = $kbps;
	#ASSUMES @AUDIO_BITRATES is a list of valid bitrates
	$kbps = int($kbps);
	my $THRESHOLD=5;

	my $lastkbps=0;
	foreach my $tmpkbps (@AUDIO_BITRATES) {
		#print "kbps=$kbps,tmpkbps=$tmpkbps,lastkbps=$lastkbps<BR>\n";
		if     (($kbps > $lastkbps) &&   ($kbps < $tmpkbps)) {
			if (($kbps - $lastkbps) > ($tmpkbps -    $kbps)) { 
				if (abs($tmpkbps - $kbps)     < $THRESHOLD) { return $tmpkbps;  }
			} else {
				if (abs($tmpkbps - $lastkbps) < $THRESHOLD) { return $lastkbps; }
			}
		}
		$lastkbps = $tmpkbps;
	}
	return (&round($ugly));
}#endsub round_audio_kbps
##############################################################################
###############################################################################
sub convert_seconds_to_readable_length {
	#USAGE: &convert_seconds_to_readable_length($seconds,"YEAR MONTH DAY YYYY MM DD HOUR HH MIN mm SEC ss",{leadingzerofields=>0,addabbrsuffix=>1});
	#USAGE: best & most-tested format string: "YEAR MONTH DAY HOUR MIN SEC",

	my $totalseconds		= $_[0];
	my $format				= $_[1];
	my $options	 			= $_[2];
	my $leadingzerofields 	= $options->{leadingzerofields}	|| 0;
	my $suffix				= $options->{addabbrsuffix}		|| 1;


	####### Options 
	# {leadingzerofields=>0}	#erases leading fields like 0000:00
	# {addabbrsuffix=>1}		#adds stuff like "1 yr 2 mo"
	####### Format 
	### specifies how to format the answer
	#SS=seconds with leading zero
	#SEC=seconds without leading zero
	#mm=minutes with leading zero	-- LOWERCASE!
	#MIN=minutes without leading zero
	#HH=hours with leading zero
	#HOUR=hours without leading zero
	#DD=days with leading zero
	#DAY=days without leading zero
	#MM=months with leading zero
	#MONTH=months without leading zero
	#YYYY=years with leading zero - 4 digits
	#YEAR=years without leading zero


	##### Set default format:
	if ($format eq "") { $format="YEAR MONTH DAY HOUR MIN SEC"; }
	my $retval = $format;


	##### THIS NEXT SECTION HAS BEEN PORTED TO THE &FORMAT_DATETIME functin

	##### Processnumerical values:
	my $totalminutes	= int($totalseconds / (60));
	my $totalhours		= int($totalseconds / (60*60));
	my $totaldays		= int($totalseconds / (60*60*24));
	my $totalweeks		= int($totalseconds / (60*60*24*7));
	my $totalmonths		= int($totalseconds / (60*60*24*30));
	my $totalyears		= int($totalseconds / (60*60*24*365));
	my $SEC				= $totalseconds % 60;
	my $SS				= sprintf("%02d",$SEC);
	my $MIN				= $totalminutes % 60;
	my $mm      		= sprintf("%02d",$MIN);
	my $HOUR			= $totalhours % 24;
	my $HH				= sprintf("%02d",$HOUR);
	my $DAY				= $totaldays % 30;
	my $DD				= sprintf("%02d",$DAY);
	my $MONTH			= $totalmonths % 12;
	my $MM				= sprintf("%02d",$MONTH);
	my $YEAR			= $totalyears;
	my $YYYY			= sprintf("%04d",$YEAR);

	##### Process suffix:
	my ($SFXYEAR,$SFXMONTH,$SFXDAY,$SFXHOUR,$SFXMIN,$SFXSEC)=("","","","","","");	
	if ($suffix) {
		($SFXYEAR,$SFXMONTH,$SFXDAY,$SFXHOUR,$SFXMIN,$SFXSEC)=("yr","mon","d","hr","min","sec");
		if ($YEAR==0)	{ $SFXYEAR=""; }
		if ($MONTH==0)	{ $SFXMONTH=""; }
		if ($DAY==0)	{ $SFXDAY=""; }
		if ($HOUR==0)	{ $SFXHOUR=""; }
		if ($MIN==0)	{ $SFXMIN=""; }
		if ($SEC==0)	{ $SFXSEC=""; }
		if ($leadingzerofields==0) {
			if ($YEAR==0)	{ $YEAR=""; }
			if ($MONTH==0)	{ $MONTH=""; }
			if ($DAY==0)	{ $DAY=""; }
			if ($HOUR==0)	{ $HOUR=""; }
			if ($MIN==0)	{ $MIN=""; }
			if ($SEC==0)	{ $SEC=""; }
		}
	}

	#print "Sfxyear is $SFXYEAR";
	##### Process format:
	$retval =~ s/YEAR/$YEAR$SFXYEAR/;	
	$retval =~ s/YYYY/$YYYY$SFXYEAR/;
	$retval =~ s/MONTH/$MONTH$SFXMONTH/;
	$retval =~ s/MM/$MM$SFXMONTH/;
	$retval =~ s/DAY/$DAY$SFXDAY/;
	$retval =~ s/DD/$DD$SFXDAY/;
	$retval =~ s/HOUR/$HOUR$SFXHOUR/;
	$retval =~ s/HH/$HH$SFXHOUR/;
	$retval =~ s/MIN/$MIN$SFXMIN/;
	$retval =~ s/mm/$mm$SFXMIN/;
	$retval =~ s/SEC/$SEC$SFXSEC/;
	$retval =~ s/SS/$SS$SFXSEC/;

	if ($leadingzerofields==0) {
		while ($retval =~ /^0+:?/) { 
			$retval =~ s/^0+:?//g; 
			#print "\nnow retval=$retval";
		}
	}

	##### Clean it up:
	$retval = &remove_leading_and_trailing_spaces($retval);
	$retval =~ s/\s\s/\s/g;

	return($retval);
}#endsub convert_seconds_to_readable_length
###############################################################################


###############################################################################
sub remove_leading_and_trailing_spaces {
	my $s = $_[0];
	$s =~ s/\s+$//;
	$s =~ s/^\s+//;
	return($s);
}
###############################################################################
################################################
sub nicefps {
	my $fps=$_[0];
	if ($fps =~ /29.97/) { return "29.97"; }
	return &round($fps);
}#endsub nicefps
################################################


###############################################################################
sub capitalize {
	my $s=$_[0];
	my $retvcal="";
	#### It's necessary to do it this way, because we need to ADD BACK IN
	#### whatever it is we're splitting on.  Thus, we can't split on both
	#### space and underscore at once or we won't know which it was once
	#### it's spilt away.  By doing it separately, we can split-by-spaces
	#### first, then add the spaces back after capitalizing, then split-by-
	#### underscores next, then add back the underscores after capitalizing.
	#### ETC. ETC. for new delimiters (hyphen?)

	#DEBUG: print "=====> going to have to capitalize $s <======\n";

	$tmp    = &capitalize_inner($s,0);
	$retval = &capitalize_inner($s,1);

	return($retval);
}#endusb capitalize
###############################################################################
###############################################################################
sub capitalize_inner {
	my $s=$_[0];                                      #DEBUG: print "s is $s\n";
	my $splittype=$_[1];
	my $retval="";
	my $DELIMITER = "::::";  #just needs to be unique

	if ($splittype == 0) { @S=split(/_/, "$s"); }     #maybe add \- (hyphen) too
	if ($splittype == 1) { @S=split(/\s/,"$s"); }

	foreach $word (@S) {
		#DEBUG: print "** CAPITALIZING WORD $word [ST=$splittype]\n";

		$first = $word;
		$rest  = $word;

		#stop capitalizing paranthesized words..that was a bad idea.
		$first =~ s/^([0-9_]*.)(.*)$/$1/i;
		$rest  =~ s/^([0-9_]*.)(.*)$/$2/i;

		if ($DEBUG_PAREN_CAPITALIZE) { "word is \"$word\""; }
		if ($word =~ /^\(/) { $PARENTHESIS=1; }		#in a way, I want to do ++ instead of =1, to deal with nested parens :)
		if ($word =~ /\)$/) {						#can't be an elsif or "(x)" wont result in the right paren being noticed
			$PARENTHESIS=0;							#in a way, I want to do -- instead of =1, to deal with nested parens :)
		} elsif ($PARENTHESIS==0) {					#needs to be an elsif so that "word)" doesn't turn $PARENTEHSIS to 0 and then we check that it's 0 and capitalize it because we think we're not in parenthesis anymore when really we're just closing them
			$first =~ tr/[a-z]/[A-Z]/;
		}


		$retval .= "$first" . "$rest" . $DELIMITER;

		if ($DEBUG_PAREN_CAPITALIZE) { print "...first is now \"$first\", rest is \"$rest\"" . ", parenthesis is $PARENTHESIS, returning \"$retval\"\n"; }

	}#endforeach
	if ($splittype == 0) { $retval =~ s/$DELIMITER/_/g; }
	if ($splittype == 1) { $retval =~ s/$DELIMITER/ /g; }
	return($retval);
}#endsub capitalize($filename)
###############################################################################

#####################################################################################################################################
sub is_show {
	my $IS_SHOW = 0;
	my ($base) = $_[0];				#base filename; no extension

	if ($base =~ / MOVIE/) { return(0); }		#anything with mvoie in the title is probably not a show!

	##### EPISODE INFORMATION MEANS IT IS PROBABLY A SHOW:
	if ($base =~ /Ep [0-9]+/i)              { $IS_SHOW=1; }
	if ($base =~ / - _[0-9][0-9][0-9]_/)    { $IS_SHOW=1; }

	##### Some shows that don't have SxExx but are just numbered like "01_" ..... will return 0 here. ARGH.

	##### SPECIFIC NAMES MEAN THEY ARE PROBABLY SHOWS:
	if ($base =~ /Dana.Carvey.Show/i)                    { $IS_SHOW=1; }
	if ($base =~ /Aqua.Teen.Hunger.Force/i)              { $IS_SHOW=1; }
	if ($base =~ /Xavier.Renegade.Angel/i)               { $IS_SHOW=1; }
	if ($base =~ /The.Simpsons/i)                        { $IS_SHOW=1; }
	if ($base =~ /^Superjail/i)                          { $IS_SHOW=1; }
	if ($base =~ /^Wolverine And The X-Men/i)            { $IS_SHOW=1; }
	if ($base =~ /^Simpsons/i)                           { $IS_SHOW=1; }
	if ($base =~ /Star.Trek/i)                           { $IS_SHOW=1; }
	if ($base =~ /^Metalocalypse/i)                      { $IS_SHOW=1; }
	if ($base =~ /^SGCTC/i)                              { $IS_SHOW=1; }
	if ($base =~ /^Daria/i)                              { $IS_SHOW=1; }
	if ($base =~ /^Squidbillies/i)                       { $IS_SHOW=1; }
	if ($base =~ /^Space Dandy/i)                        { $IS_SHOW=1; }
	if ($base =~ /^Assy.*McGee/i)                        { $IS_SHOW=1; }
	if ($base =~ /^nofx.*backstage.*passport/i)          { $IS_SHOW=1; }
	if ($base =~ /^fat.*guy.*stuck.*internet/i)          { $IS_SHOW=1; }
	if ($base =~ /Marvelous.*Misadventures.*Flapjack/i)	 { $IS_SHOW=1; }
	if ($base =~ /^The Rising Son/i)                     { $IS_SHOW=1; }
	if ($base =~ /Goode Family/i)                        { $IS_SHOW=1; }
	if ($base =~ /^Chowder - /i)                         { $IS_SHOW=1; }
	if ($base =~ /^Time Squad -/i)                       { $IS_SHOW=1; }
	if ($base =~ /^Eek! The Cat/i)                       { $IS_SHOW=1; }
	if ($base =~ /^Titan Maximum/i)                      { $IS_SHOW=1; }
	if ($base =~ /^Producing Parker/i)                   { $IS_SHOW=1; }
	if ($base =~ /^Total Drama /i)                       { $IS_SHOW=1; }
	if ($base =~ /^Bromwell High/i)                      { $IS_SHOW=1; }
	if ($base =~ /^PowerPuff Girls/i)                    { $IS_SHOW=1; }
	if ($base =~ /^Adventure Time/i)                     { $IS_SHOW=1; }
	if ($base =~ /^Transformers Prime/i)                 { $IS_SHOW=1; }
	if ($base =~ /^Aqua Unit Patrol Squad/i)             { $IS_SHOW=1; }
	if ($base =~ /^Producing *Parker/i)                  { $IS_SHOW=1; }
	if ($base =~ /^X-Men \(anime\)/i)					 { $IS_SHOW=1; }
	#if ($base =~ /^/i)									{ $IS_SHOW=1; }
	#if ($base =~ /^/i)									{ $IS_SHOW=1; }
	#if ($base =~ /^/i)									{ $IS_SHOW=1; }
	#if ($base =~ /^/i)									{ $IS_SHOW=1; }
	#if ($base =~ /^/i)									{ $IS_SHOW=1; }
	#if ($base =~ /^/i)									{ $IS_SHOW=1; }


	return($IS_SHOW);
}
#####################################################################################################################################




########################################################################################################
sub hashdump {
	my %hash=%{$_[0]};
	my $s="";
	foreach my $key (sort keys %hash) {
		$s .= "key = $key \t value = " . $hash{$key} . "\n";
	}
	return($s);
}
########################################################################################################

########################################################
sub round {
	my ($number) = shift;
	return int($number + .5 * ($number <=> 0));
}#endif
########################################################


##########################################
sub remove_extension {
	my     $s =  $_[0];
	       $s =~ s/\.([^\.]{1,8})$//;
	return($s);
}
##########################################
##########################################
sub get_extension {
	my     $s =  $_[0];
	if ($s !~ /\./) { return ""; }
	$s =~ s/^.*\.(.{1,8})$/$1/;
	return($s);
}
##########################################


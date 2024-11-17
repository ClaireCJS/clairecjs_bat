#!/usr/local/bin/perl

use utf8;										#20221102
use open qw( :std :encoding(UTF-8) );			#20221102
binmode(STDIN,  ':encoding(UTF-8)');
binmode(STDOUT, ':encoding(UTF-8)');


my $NEXT_DAY_HH_THRESHOLD = "08";		#For example, if set to 08, This means that any picture taken before 08AM will be considered part of the previous day -- assuming there were pics that previous day and this is a running set



use strict;

my $DEBUG_TIME=1;						#set to 1 to display retrieved time info in raw format after exiftools extracts it
my $DEBUG=0;							#set to 2 to actually see hash tables
my $TIME=0;								#do we add the TIME past the date? This will be set to 1 if we do.
my $PAST_MIDNIGHT="";					#used in "allfiles exif time" ($TIME=1) mode to un-do the post-midnight-threshold logic used in $TIME=0 mode - basically, pics just past midnight need to sort into the previous day's folder because it's really just an event past midnight. But if we then supplimentally run it in TIME mode, that change needs to be UN-done. This makes perfect sense if you REALLY REALLY think about it: Past midnight pictures should be in the previous day's folder, and even be tagged with the previous day's date -- but that date should not be used in the filename or they will upload out of order for alphabetical uploaders
my $filenameprefix="";
my $filename="";
my $info="";
my $tmpdateinfo="";
my $filenameprefix="";
my $original_filenameprefix1="";
my $original_filenameprefix2="";
my $SKIP="";
my $original_filename="";
my $scrubbed_date="";
my $YYYYMMDD="";
my $HH="";
my $MM="";
my $SS="";
my %YYYYMMDD_USED=();
my $newyyyymmdd="";
my $temp="";
my $filename2use="";
my $line=1;
my $newfilename="";

if ($ENV{"ADDTIME"} == "1") { $TIME=1; }															if ($DEBUG_TIME) { print "echo time is $TIME\n"; }

use Image::ExifTool 'ImageInfo';
#use Clio::Date;					#the ~2 functions used have now been copied into this script so as to not rely on a Clio library

open(NEWNAMES,"$ARGV[0]");          ##### 1st file, $tmp1, the   new    filenames
#hile ($filename=<STDIN>) 
while ($filename=<NEWNAMES>) {
	#DEBUG: print "line " . $line++ . " is $filename";
    chomp $filename;

	##### Determine if we skip renaming this kind of file:
	$SKIP=1;
    if ($filename =~ /\.jpg$/i)             { $SKIP=0; }
    if ($filename =~ /\.jpg\.?dep$/i)       { $SKIP=0; }
    if ($filename =~ /\.jpg\.deprecated$/i) { $SKIP=0; }
    if ($filename =~ /\.wav$/i)             { $SKIP=0; }		#wikipedia says WAV  can have exif
    if ($filename =~ /\.tiff$/i)            { $SKIP=0; }		#wikipedia says TIFF can have exif
    if ($filename =~ /\.raw$/i)             { $SKIP=0; }		#no clue if RAW files have EXIF or not
    if ($filename =~ /~__/i)                { $SKIP=1; }		#no clue if RAW files have EXIF or not
	if ($filename eq "")                    { $SKIP=1; }
	if ($SKIP)                              {  next  ; }

	##### Store original filename:
	$original_filename=$filename;
	if ($DEBUG) { print "filename is $filename\n"; }

	##### Grab EXIF datetime info:
	if (($filename =~ /\.jpg/i) || ($filename =~ /\.dep/i) || ($filename =~ /\.deprecated/i)) {
		$info        = &ImageInfo($filename);																	if ($DEBUG>1) { foreach my $key (sort keys %$info) { print "key=$key, data=$info->$key\n"; } }
		$tmpdateinfo = $info->{DateTimeOriginal};																if ($DEBUG>0) { print "tmpdateinfo for $filename is \"$tmpdateinfo\"\n"; }
		$tmpdateinfo =~ /^([0-9]{4}):([01][0-9]):([0-3][0-9]) ([0-2][0-9]):([0-5][0-9]):([0-5][0-9])/;			#2009:01:24 23:58:15
			$YYYYMMDD = $1 . $2 . $3;		#YYYYMMDD --- the date
			$HH=$4;  $MM=$5;  $SS=$6;		#HHMMSS ----- the time
			$YYYYMMDD_USED{$YYYYMMDD}="1";								#store date, so if past midnite we can "remember" there were pix before midnite 
		$filenameprefix = $YYYYMMDD;
		$original_filenameprefix1 = $filenameprefix;
		$original_filenameprefix2 = $filenameprefix;
	} else {
		print ":Skipping grabbing exif info from $filename\n";
		#Let's try doing nothing, this will re-use values from the last JPG which may or may not be a smart thing to do; wait and see; my surgeryhuts too much to think about it right now
	}


	##### Clio-specific logic: If I haven't stopped taking pictures for 8 hrs, I've stayed up past midnight, and still want to use the previous date's date:
	$PAST_MIDNIGHT=0;
	if (($HH >= 00) && ($HH < $NEXT_DAY_HH_THRESHOLD)) {					#if it's between midnight and our next-day-threshold (ex: 8AM)
		if ($DEBUG) { print ":** The \$HH of $HH for $filename falls between 00 and $NEXT_DAY_HH_THRESHOLD!\n"; }
		$newyyyymmdd=&decrement_date_by_one_day($YYYYMMDD);					#then we need to figure out what the previous day is in YYYYMMDD format
		if ($DEBUG) { print ":** So we decrement $YYYYMMDD one day to get $newyyyymmdd and check if there were pictures\n"; }
		if ($YYYYMMDD_USED{$newyyyymmdd} eq "1") {							#and if we "remember" there being pictures on that date
			$filenameprefix = $newyyyymmdd;									#then this is a continuance of that event, and we should use that date instead
			$original_filenameprefix2 = $filenameprefix;
			$PAST_MIDNIGHT=1;
		}
	}
	if ($TIME) { $filenameprefix .= " $HH$MM"; }							#add MMSS (time of day) if requested

	##### Add " - " to the filename prefix:
	if ($filenameprefix ne "") { $filenameprefix .= " - "; }														if ($DEBUG>0) { print "fileprefix for $filename is $filenameprefix\n"; }
	if (($DEBUG>0)||($DEBUG_TIME>0)) { print ":for $filename, \$1=$1,\$2=$2,\$3=$3,\$4=$4,\$5=$5,\$6=$6, filenameprefix=\"$filenameprefix\",original1=\"$original_filenameprefix1\",orig2=\"$original_filenameprefix2\"\n"; }

	##### BONUS FUNCTIONALITY BEYOND THE ORIGINAL SCOPE: CLEAN UP SOME STUPID CAMERA-AUTOMATED NAMINGS:
	$filename =~ s/_IMG.JPG$/.jpg/i;						#I've always thought "_IMG.JPG" is redundant. All JPGs are images. "_IMG" is just stupid
	$filename =~ s/.JPG$/.jpg/;								#capital extensions are bad!
	$filename =~ s/.MOV$/.mov/;								#capital extensions are bad!
	$filename =~ s/.AVI$/.avi/;								#capital extensions are bad!

	##### Don't rename it if it already has the original prefix:
	if      (($original_filename =~ /^$filenameprefix/i) && ($filenameprefix != "")) {
		print qq[::::: Skipping "$original_filename" -- already prefixed with "$filenameprefix" (final)! (TIME=$TIME)\n];
		$SKIP=1;
	}

	##### If we are going ahead and renaming it, we need to remove any other dates that are incorrect (due to the fact TIME=0 and TIME=1 mode will name the same file 2 differnet dates BY DESIGN) off the beginning of the filename:
	$filename2use=$filename;
	$filename2use =~ s/^$original_filenameprefix1 *\-* *//i;
	$filename2use =~ s/^$original_filenameprefix2 *\-* *//i;													if ($DEBUG_TIME) { print ":: Filename2use=$filename2use, originalprefix1=$original_filenameprefix1, originalprefix2=$original_filenameprefix2, pastmidnight=$PAST_MIDNIGHT\n"; }
	##### If it's a "past midnight" file, we need to change the date to the past midnight date, despite the fact that folder and tag wise, it's considered the previous date. This is an issue of sorting pictures from multiple cameras in proper chronological order for upload:
	if (($TIME==1) && ($PAST_MIDNIGHT==1)) {
		$filenameprefix =~ s/^$original_filenameprefix2/$original_filenameprefix1/;
	}

	##### Do the actual rename:
	$newfilename = "$filenameprefix$filename2use";														#DEBUG FOR DEV ONLY: print qq[::::: 	if ($original_filename =~ /^$newfilename$/i) \n];
	if (($original_filename =~ /^$newfilename$/i) || ($original_filename eq $newfilename)) {
		print qq[::::: Skipping "$original_filename" -- no name change!\n];
	} elsif (!$SKIP) { 
		print qq[*move /r /g /h /E "$original_filename" "$newfilename"\n]; 
	}

}









#################################################################################################################################
sub decrement_date_by_one_day {		#USAGE: ($newyymmdd)=&decrement_date_by_one_day($yymmdd);
	#USES last_day_of_month;
	my $date = $_[0];
	my $year="";
	my $month="";
	my $day="";
	my $MONTH_DECREMENTED=0;

	#DEBUG: print "\n\ndate=$date,length(\$date) is ";print length($date);print "\n\n";

	#FIRST let us define all the numbers and strings we will need:
	if (length($date) == 8) {
		$year = $day = $month = $date;
		$year      =~ s/(....)..../$1/;
		$month     =~ s/....(..)../$1/;
		$day       =~ s/......(..)/$1/;
	} else {
		$year = $day = $month = $date;
		$year      =~ s/(..)..../$1/;
		$month     =~ s/..(..)../$1/;
		$day       =~ s/....(..)/$1/;
	}

	$day--;                         #decrement day

	if (!$day) {                    #if day is zero, decrement month, set flag
			$month--;
			$MONTH_DECREMENTED=1;
	}#endif

	if (!$month) {                  #if month is zero, it's really december of the last year
			$year--;
			$month=12;
	}#endif

	if ($year == -1) { $year=99; }  #if year is -1, it's really <century>99

	if ($MONTH_DECREMENTED) {       #if month was decremented, set day to last day of month
			$day=&last_day_of_month($month,$year);
	}#endif
	if ($day   =~ /^[1-9]$/) { $day   = "0$day";   }        #normalize values to have 0 in front of them if less than 10
	if ($month =~ /^[1-9]$/) { $month = "0$month"; }
	if ($year  =~ /^[1-9]$/) { $year  = "0$year";  }

	return "$year$month$day";

}#endsub decrement_date_by_one_day
#################################################################################################################################


#########################################################################################################################
sub last_day_of_month {		#USAGE: ($day)=&last_day_of_month(2,1998);
	my ($month)=$_[0];
	my ($year)=$_[1];
	my $day="";

	#### months with 31 days:
	if (($month==1) || ($month==3) || ($month==5) || ($month==7)
	 || ($month==8) || ($month==10) || ($month==12)) {
			$day=31;
	#### months with 30 days:
	} elsif (($month==4) || ($month==6) || ($month==9) || ($month==11)) {
			$day=30;
	### february is special:
	} elsif ($month==2) {
			if (($year % 4)==0) {
					$day=29;
			} else {
					$day=28;
			}#endif it's a leap year
			if ((($year % 4)==0) && (($year % 100)==0)) {				
					$day=28;
			}
			if ((($year % 4)==0) && (($year % 100)==0) && (($year % 400)==0)) {
					$day=29;
			}
			if ((($year % 4)==0) && (($year % 100)==0) && (($year % 400)==0) && (($year % 10000)==0)) {
					$day=28;
			}
	} else {
			$temp  = "\n\n******* INTERNAL ERROR MONTH_1_X: month=$month,year=$year *******\n";
			$temp .= "        (THIS SHOULD NEVER HAPPEN)\n\n";
			print $temp;
	}#endif

	#print "<h1>Last day of month \"$month\" in year \"$year\" is \"$day\"</h1>\n\n";	#
	 
	return($day);
}#endsub last_day_of_month
#########################################################################################################################

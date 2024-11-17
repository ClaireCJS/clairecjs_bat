#!/usr/local/bin/perl
use utf8;
use open ':std',':encoding(UTF-8)' ;
binmode(STDIN,  ':encoding(UTF-8)');
binmode(STDOUT, ':encoding(UTF-8)');

my $TIME=0;
if ($ENV{"ADDTIME"} == "1") {  $TIME=1; }
print qq[rem TIME is $TIME\n];

##### Take any passed additional file descriptors:
my $ADDITIONAL_FILENAME_STUFF="";
if ($ENV{"ADDITIONAL_FILENAME_DESCRIPTOR"} ne "") {
	$ADDITIONAL_FILENAME_STUFF = $ENV{"ADDITIONAL_FILENAME_DESCRIPTOR"} . " - ";
}
print qq[rem ADDITIONAL_FILENAME_STUFF is "$ADDITIONAL_FILENAME_STUFF"\n];

open(NEWNAMES,"$ARGV[0]");          ##### 1st file, $tmp1, the   new    filenames
while ($filename=<NEWNAMES>) {
#while ($filename=<STDIN>) 
    chomp $filename;

	##### Store original filename:
	$original_filename = $filename;
	$new_filename      = $filename;
	if ($DEBUG) { print " filename is $filename\n"; }

	##### Grab file date info:
	($dev,$ino,$mode,$nlink,$uid,$gid,$rdev,$size,
		   $atime,$mtime,$ctime,$blksize,$blocks)
		       = stat($filename);

	##### Format the date info:
	use Date::Format;				#good for a year!
#	use DateTime::Format;	
	if ($ENV{"ADDTIME"} == "1") { $created = time2str('%Y%m%d %H%M', $mtime); }
	else                        { $created = time2str('%Y%m%d'     , $mtime); }


	##### Do the rename: exclude extensions we don't want to rename:
	if (
		    (($original_filename !~ /^[12][0-9][0-9][0-9][0-9][01][0-9][0-3][0-9] [0-2][0-9][0-5][0-9]/) && ($TIME==1))
		 || (($original_filename !~ /^[12][0-9][0-9][0-9][0-9][01][0-9][0-3][0-9]/)                      && ($TIME==0))
	     ||  ($original_filename !~ /^_/)
	     ||  ($original_filename !~ /\.bat$/)
	     ||  ($original_filename !~ /\.btm$/)
	     ||  ($original_filename !~ /\.exe$/)
	     ||  ($original_filename !~ /\.lst$/)
	     ||  ($original_filename !~ /\.txt$/)
	     ||  ($original_filename !~ /\.stackdump$/)
	   )
	{
		$ADDITIONAL_FILENAME_STUFF_TO_USE = $ADDITIONAL_FILENAME_STUFF;	   if ($original_filename =~ /$ADDITIONAL_FILENAME_STUFF/i) { $ADDITIONAL_FILENAME_STUFF_TO_USE=""; }	#don't add if it's already in
		$created_to_use="$created - ";		                               if ($original_filename =~ /$created/i)                   { $created_to_use="";                   }	#don't add if it's already in

		print qq[mv "$original_filename" "$created_to_use$ADDITIONAL_FILENAME_STUFF_TO_USE$original_filename"\n]; 
	}

	##### DEBUG:
	#print "rem \$atime  =$atime\n";
	#print "rem \$mtime  =$mtime\n";
	#print "rem \$ctime  =$ctime\n";
	#print "rem \$created=$created\n\n";

}






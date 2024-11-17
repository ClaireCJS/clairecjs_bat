#!perl
my @SPECIAL_FILENAME_PREFIXES=("SubGenius");
my $MAKEDIR = "mkdir";	#unix folks would want "mkdir"
my $MOVE    = "*move /r /g /h /E";		#windows people may need to set this to "move"
my %dates=();			#key=??? value=??? ... I want to say key is the filename (20181231) to match the file[s], 
						#                      and the value is the folder name (2018_12_31) that files of the key*.* would be moved to
my $date="";			
my $date2use="";
my $line="";
my $key="";
my $tmpkey="";
my $value="";
my $tmpvalue="";
my $tmp1="";
my $tmp2="";
my $tmp3="";
my $tmp4="";
foreach $line (<STDIN>) {
	#DEBUG:	print "$line";
	if ($line =~ /^([12][0-9][0-9][0-9]) - /) {												#2010 - 
		#DEBUG: print "$dates{$1}=\"$1\";\n";
		$dates{$1}="$1";
	}
	if ($line =~ /^([12][0-9][0-9][0-9]) [0-2][0-9][0-5][0-9] - /) {						#2010 1231 - 
		#DEBUG: print "$dates{$1}=\"$1\";\n";
		$dates{$1}="$1";
	}
	if ($line =~ /^([12][0-9][0-9][0-9][0-1][0-9]) - /) {									#201012 - 
		#DEBUG: print "$dates{$1}=\"$1\";\n";
		$dates{$1}="$1";
	}
	if ($line =~ /^([12][0-9][0-9][0-9][0-1][0-9]) [0-2][0-9][0-5][0-9] - /) {				#201012 2359
		#DEBUG: print "$dates{$1}=\"$1\";\n";
		$dates{$1}="$1";
	}
	if ($line =~ /^([12][0-9][0-9][0-9][0-1][0-9][0-3][0-9]) - /) {							#19991230 - 
		#DEBUG: print "$dates{$1}=\"$1\";\n";
		$dates{$1}="$1";
	}
	if ($line =~ /^([12][0-9][0-9][0-9][0-1][0-9][0-3][0-9]) [0-2][0-9][0-5][0-9] - /) {	#19991231 2159 - 
		#DEBUG: print "$dates{$1}=\"$1\";\n";
		$dates{$1}="$1";
	}
	if ($line =~ /^([12][0-9][0-9][0-9][0-1][0-9][0-3][0-9])_/) {							#2014 / android
		#DEBUG: 		print "$dates{$1}=\"$1\";\n";
		$dates{$1}="$1";
	}
	if ($line =~ /^IMG_([12][0-9][0-9][0-9][0-1][0-9][0-3][0-9])_/) {						#2014 / some weird source
		#DEBUG: 		print "$dates{$1}=\"$1\";\n";
		$dates{$1}="$1";
	}
	if ($line =~ /^([12][0-9][0-9][0-9]\-[0-1][0-9]\-[0-3][0-9])/) {						#2014 dropbox or something
		#DEBUG: 		print "$dates{$1}=\"$1\";\n";
		$dates{$1}="$1";
	}
	#Frame_2015-08-11_19-52-49
	if ($line =~ /^Frame_([12][0-9][0-9][0-9])\-([0-1][0-9])\-([0-3][0-9])/) {				#Frame_2015-08-11 iSpy IP-cam grabs
		#DEBUG: 		print "$dates{$1}=\"$1\";\n";
		$dates{$1}="$1$2$3";
	}


	#MPC snapshots
	#snapshot.*\[2015.12.27_22.47.03\]
	if ($line =~ /snapshot.*\[([12][0-9][0-9][0-9])\.([0-1][0-9])\.([0-3][0-9])_/i) {			
		$tmp1=$1;		$tmp2=$2;		$tmp3=$3;
		$tmpkey   = $tmp1 . "." . $tmp2 . "." . $tmp3;	#specific to this filename pattern
		$tmpvalue = $tmp1 . "_" . $tmp2 . "_" . $tmp3;	#same for everything
		$dates{$tmpkey}=$tmpvalue;
		#DEBUG: 		print "\$dates{$tmpkey}=$tmpvalue;\n"
	}


	#*2015-08-11*
	#VLC snapshots
	if ($line =~ /vlcsnap-([12][0-9][0-9][0-9])\-([0-1][0-9])\-([0-3][0-9])/) {			
		$tmp1=$1;		$tmp2=$2;		$tmp3=$3;
		$tmpkey   = $tmp1 . "-" . $tmp2 . "-" . $tmp3;
		$tmpvalue = $tmp1 . "-" . $tmp2 . "-" . $tmp3;
		$dates{$tmpkey}=$tmpvalue;
		#DEBUG: print "$dates{$1-$2-$3}=\"" . $dates{"$1-$2-$3"} . "\";\n";
	}


#	#20181109_002534[. ].jpg - best pattern to copy as of 201811
#	if ($line =~ /([12][0-9][0-9][0-9])([0-1][0-9])([0-3][0-9])\_([0-2][0-9])([0-5][0-9])([0-5][0-9])([\. ])/) {			
#		$tmp1=$1;		$tmp2=$2;		$tmp3=$3;		$tmp4=$4;   $tmp5=$5;   $tmp6=$6;
#		$tmpkey   = $tmp1 .       $tmp2 .       $tmp3;		#how the file is named
#		$tmpvalue = $tmp1 . "-" . $tmp2 . "-" . $tmp3;		#how the folder to put the file in is named
#		$dates{$tmpkey}=$tmpvalue;
#		#DEBUG: print "$dates{$1-$2-$3}=\"" . $dates{"$1-$2-$3"} . "\";\n";
#	}

	#2018-11-22 18.32.03.jpg
	if ($line =~ /^([12][0-9][0-9][0-9])-([0-1][0-9])-([0-3][0-9])/) {			
		$tmp1=$1;		$tmp2=$2;		$tmp3=$3;
		$tmpkey   = $tmp1 . "-" . $tmp2 . "-" . $tmp3;		#how the file is named
		$tmpvalue = $tmp1 . "_" . $tmp2 . "_" . $tmp3;		#how the folder to put the file in is named
		$dates{$tmpkey}=$tmpvalue;
		#DEBUG: print "[[[ $dates{$1-$2-$3}=\"" . $dates{"$1-$2-$3"} . "\";\n ]]]";
	}
	#20181109_002538.jpg
	if ($line =~ /^([12][0-9][0-9][0-9])([0-1][0-9])([0-3][0-9])/) {			
		$tmp1=$1;		$tmp2=$2;		$tmp3=$3;
		$tmpkey   = $tmp1 .       $tmp2 .       $tmp3;		#how the file is named
		$tmpvalue = $tmp1 . "_" . $tmp2 . "_" . $tmp3;		#how the folder to put the file in is named
		$dates{$tmpkey}=$tmpvalue;
		#DEBUG: print "$dates{$1-$2-$3}=\"" . $dates{"$1-$2-$3"} . "\";\n";
	}

	#^YYYY_MM_DD generic - no longer "best pattern to copy as of 201602"
	if ($line =~ /([12][0-9][0-9][0-9])\_([0-1][0-9])\_([0-3][0-9])/) {			
		$tmp1=$1;		$tmp2=$2;		$tmp3=$3;
		$tmpkey   = $tmp1 . "_" . $tmp2 . "_" . $tmp3;		#how the file is named
		$tmpvalue = $tmp1 . "-" . $tmp2 . "-" . $tmp3;		#how the folder to put the file in is named
		$dates{$tmpkey}=$tmpvalue;
		#DEBUG: print "$dates{$1-$2-$3}=\"" . $dates{"$1-$2-$3"} . "\";\n";
	}


}
foreach $date (keys %dates) {
	$key   = $date;
	$value = $dates{$key};
	$date2use = $date;
	$date2use =~ s/^(....)\-?(..)\-?(..)$/$1_$2_$3/;
	$date2use =~ s/^(....)\-?(..)$/$1_$2/;
	if ($value ne $key) { $date2use = $value; }
	
	print "$MAKEDIR \"$date2use\"\n";
	#rint "$MOVE \"$date - *.*\" \"$date2use\"\n";
	#rint "$MOVE \"$date *.*\" \"$date2use\"\n";		#updated for 'allfiles exif time' JPGs that also have time, i.e. named like "YYYYMMDD HHSS - " instead of "YYYYMMDD - "
	print "if isdir \"$date2use\" $MOVE \"*$date*.*\" \"$date2use\"\n";		#updated 20140426, 20181215
}


foreach my $prefix (@SPECIAL_FILENAME_PREFIXES) {
	print "if exist \"$prefix*.*\" if not isdir \"$prefix\" $MAKEDIR \"$prefix\"\n";
	print "if exist \"$prefix*.*\" $MOVE \"$prefix*.*\" \"$prefix\"\n";
}

### OFFLINEDIR.PL.
### PURPOSE:	to easily catalog files being placed offline (ie burned cdrs, dvdrs, floppies, etc)
### USAGE:  	dir /b | offlinedir <name-of-offline-media-these-files-appear-on> >>catalog_file
### EXAMPLE: 	dir /b | offlinedir data-cdr-1 >>"c:\my documents\my offline files.txt"
### EXPLANATION:	takes a filelist, formats it, and adds the file's sizes (with commas) to the end of each line
### DEFINITIONS:	
#			filelist - a list of filenames, 1 per line (easily generated with dir /b)
#			format - the number of spaces the media name fits in, defined by the number in $OFFLINEFORMAT
#					for example, if offlineformat was 15, the output of the example above would look like: "data-cdr-1    - filename (filesize)". notice how from the d in "data" to the "-" it is 15 characters
#			| - used to pipe the output of dir /b into this script
#			>> - used to append this output to the catalog file.  Note that using > would overwrite the file, so keep daily backups!




my $OFFLINEFORMAT="%-17s";
####################^^^^ this is how offline.txt is set up -- it is X characters before the " - episode/filename" is written...
####################A sample line would look like:
####################data-dvdr-95      - PlayStation2 Network Disk Backup.nrg (143,133,421)





####################################################################################
use strict;
my $line, my $date, my $time, my $fileSize, my $fileName, my $LAST_WAS_MULTIPART;
my $tally_filename, my $tally, my $fileSizeUgly, my $output, my $part_number;
my $parts_tallied=0, my $IS_ARCHIVED_VIDEO=0, my $last_part_number = -1;
my @LINES=();

##### Get disc-number from command-line arguments or current path:
my $OfflineMediaEntityName = $ARGV[0];
#my $curdir = Win32::GetCwd();
#if ($curdir =~ /(video-dvdr-[0-9]+)/) {
#	$OfflineMediaEntityName=$1;
#	$IS_ARCHIVED_VIDEO=1;
#}

#use File::Find;
#&find({wanted=>\&wanted, no_chdir=>1},$curdir);


##### Format the left (disc) side of the offline listin:
my $leftside=sprintf($OFFLINEFORMAT,$OfflineMediaEntityName) . " - ";

##### For each file:
while ($line=<STDIN>) {	push(@LINES,$line); }

#### FORK: offlinedir.pl: IF NO LINES PASSED, JUST GET EACH FILE FROM THE DIRECTORY.


foreach $line (@LINES) {
	chomp $line;  $line =~ s/^\s+//g;  $line =~ s/\s+$//g;	$output="";
	if ($line =~ /[0-9]\/[0-9]+\/[0-9]+/) {
		($date,$time,$fileSize,$fileName)=split(/\s+/,"$line",4);
		$output .= "$fileName ($fileSize)\n";
	} else {
		$fileName=$line;
		if (!-e $fileName) {
			$output .= $line . "\n";
		} else {
			$fileSizeUgly = -s $fileName;
			$fileSize     = &commaize($fileSizeUgly);
			if (-d $fileName) {
				$fileSize="directory"; next;		#If it's a directory, say nothing & start loop over.
			}#endif
			if (($OfflineMediaEntityName ne "") || ($OfflineMediaEntityName eq "/v")) {
				$output = $leftside;
			}#endif
			#print "$fileName ($fileSize)\n";
			#if it's a multipart file, it's extremely convenient to print a total
			if (($fileName =~ /part([0-9]+)/i) && ($fileName =~ /[rza][aic][rpe]$/i)) {		
				$fileName =~ /part([0-9]+)/i;
				$part_number    = $1;
				#goat
				if ($part_number < $last_part_number) {
					#print the summary, but no point if it's only 1 part (probably a multipart split across multidiscs)
					if ($parts_tallied > 1) {
						$output .= "$tally_filename ($parts_tallied parts:".&commaize($tally).") \n$leftside";
					}
					$tally=0; $parts_tallied=0;
					$LAST_WAS_MULTIPART=0;		#variablename not quite right.. GOAT
				} elsif ($LAST_WAS_MULTIPART==0) {
					$LAST_WAS_MULTIPART=1;
				}
				#DEBUG:print "parts_tallied was $parts_tallied\n";
				$parts_tallied += 1; 
				#DEBUG:$output .= "$part_number < $last_part_number\n\t\t    ";
				$last_part_number = $part_number;
				$tally_filename = $fileName;
				$tally_filename =~ s/part([0-9])+//i;
				$tally_filename =~ s/\.\././i;
				$tally += $fileSizeUgly;
				$output .= "$fileName ($fileSize)\n";
			} elsif ($LAST_WAS_MULTIPART==1) { 
				if ($parts_tallied > 1) {
					$output .= "$tally_filename ($parts_tallied parts:".&commaize($tally).")\n$leftside";
				}
				$output .= "$fileName ($fileSize)\n";
				$LAST_WAS_MULTIPART=0; $part_number=""; $tally=0; $parts_tallied=0;
			} else {
				$last_part_number = -1;
				$output .= "$fileName ($fileSize)\n";
			}#endif
		}#endif
	}#endif
	print $output;
}#endwhile
#DEBUG:print "$part_number < $last_part_number\n\t\t    ";
if (($last_part_number > 0) && ($parts_tallied > 1)) {
	print $leftside . "$tally_filename ($parts_tallied parts:".&commaize($tally).")\n";
}
####################################################################################

#############################################
sub commaize {
	my $s = $_[0];
	while ($s =~ /[0-9]{4}/) {
	    $s =~ s/([0-9])([0-9]{3})$/$1,$2/g;
	    $s =~ s/([0-9])([0-9]{3}),/$1,$2/g;
	}#endwhile
	return($s);
}#endsub comma
#############################################
########################################################################
#sub wanted {
#	my $name = $File::Find::name;
#	print "$name\n";
#}#endsub wanted
########################################################################

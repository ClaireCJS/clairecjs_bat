#DEPRECATED, now replaced with sync-mp3-playlists-to-location-helper.pl

#step 1 - change / to \
#step 2 - change U:\mp3\ to \MUSIC\

my $mp3 = $ENV{"mp3official"};
$mp3 =~ s/\\/\\\\/ig;

#print "mp3 is $mp3\n";
@LINES=<STDIN>;

foreach $line (sort @LINES) {
	$line =~ s/\//\\/ig;
	if (($line =~ /^$mp3/i) || ($line =~ /^C:[\\\/]mp3/)) {
		$line =~ s/$mp3/\\MUSIC/i;
		$line =~ s/^[A-Z]:[\\\/]mp3/\\MUSIC/i;
		$line =~ s/^[A-Z]:[\\\/]testing/\\MUSIC/i;
		$line =~ s/^[A-Z]:[\\\/]media[\\\/]mp3-processing\READY-FOR-TAGGGING/\\MUSIC/i;
		$line =~ s/^[A-Z]:[\\\/]media[\\\/]mp3-processing\check4norm/\\MUSIC/i;
		$line =~ s/^[A-Z]:[\\\/]media[\\\/]mp3-processing\check4norm[\\\/]DOWNLOADS/\\MUSIC/i;
		$line =~ s/^[A-Z]:[\\\/]media[\\\/]mp3-processing\check4norm[\\\/]NEXT/\\MUSIC/i;
		$line =~ s/^[A-Z]:[\\\/]media[\\\/]mp3-processing\check4norm[\\\/]NEXT.INPROGRESS/\\MUSIC/i;
		print $line;
	}
}

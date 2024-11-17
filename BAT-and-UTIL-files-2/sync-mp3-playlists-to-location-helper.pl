

#USAGE: sync-mp3-playlists-to-location-helper.pl

#step 1 - change / to \
#step 2 - change U:\mp3\ to \MUSIC\ or whatever basedir we use

my $mp3		= $ARGV[0];
my $BASEDIR = $ARGV[1];
$BASEDIR =~ s/[\\\/]$//gi;		#trailing slash makes double-slahes
$mp3     =~ s/\\/\\\\/ig;

#DEBUG: print "mp3 is $mp3, basedir is $BASEDIR\n";

while ($line=<STDIN>) {
	$line =~ s/\//\\/ig;
	#if (($line =~ /^$mp3/i) || ($line =~ /^C:[\\\/]mp3/)) {
			##### WARNING! CLIOVIRONMENT REQUIRES ANY UPDATES TO BELOW TO ALSO BE MADE TO SYNC-FILELIST-HELPER.PL, which is the generalized/2nd version of this
			##### WARNING! CLIOVIRONMENT REQUIRES ANY UPDATES TO BELOW TO ALSO BE MADE TO SYNC-FILELIST-HELPER.PL, which is the generalized/2nd version of this
			##### WARNING! CLIOVIRONMENT REQUIRES ANY UPDATES TO BELOW TO ALSO BE MADE TO SYNC-FILELIST-HELPER.PL, which is the generalized/2nd version of this
			##### WARNING! CLIOVIRONMENT REQUIRES ANY UPDATES TO BELOW TO ALSO BE MADE TO SYNC-FILELIST-HELPER.PL, which is the generalized/2nd version of this
			##### WARNING! CLIOVIRONMENT REQUIRES ANY UPDATES TO BELOW TO ALSO BE MADE TO SYNC-FILELIST-HELPER.PL, which is the generalized/2nd version of this
			##### WARNING! CLIOVIRONMENT REQUIRES ANY UPDATES TO BELOW TO ALSO BE MADE TO SYNC-FILELIST-HELPER.PL, which is the generalized/2nd version of this
			##### WARNING! CLIOVIRONMENT REQUIRES ANY UPDATES TO BELOW TO ALSO BE MADE TO SYNC-FILELIST-HELPER.PL, which is the generalized/2nd version of this
			##### WARNING! CLIOVIRONMENT REQUIRES ANY UPDATES TO BELOW TO ALSO BE MADE TO SYNC-FILELIST-HELPER.PL, which is the generalized/2nd version of this
			##### WARNING! CLIOVIRONMENT REQUIRES ANY UPDATES TO BELOW TO ALSO BE MADE TO SYNC-FILELIST-HELPER.PL, which is the generalized/2nd version of this
			##### WARNING! CLIOVIRONMENT REQUIRES ANY UPDATES TO BELOW TO ALSO BE MADE TO SYNC-FILELIST-HELPER.PL, which is the generalized/2nd version of this
#		$line =~ s/^[A-Z]:[\\\/]mp3/$BASEDIR/i;
		$line =~ s/^[A-Z]:[\\\/]testing([\\\/])1 - ONEDIR JUDGE WITH CAROLYN/$BASEDIR/i;
		$line =~ s/^[A-Z]:[\\\/]testing/$BASEDIR/i;
		$line =~ s/^[A-Z]:[\\\/]media[\\\/]mp3-processing[\\\/]READY-FOR-TAGGING[\\\/]in base attrib correctly,but untagged \(KEEP IN THIS FOLDER WHEN MOVING TO TESTING\)/$BASEDIR/i;
		$line =~ s/^[A-Z]:[\\\/]media[\\\/]mp3-processing[\\\/]READY-FOR-TAGGING/$BASEDIR/i;
		$line =~ s/^[A-Z]:[\\\/]media[\\\/]mp3-processing[\\\/]check4norm[\\\/]changerrecent[\\\/]/$BASEDIR/i;
		$line =~ s/^[A-Z]:[\\\/]media[\\\/]mp3-processing[\\\/]check4norm[\\\/]DOWNLOADS/$BASEDIR/i;
		$line =~ s/^[A-Z]:[\\\/]media[\\\/]mp3-processing[\\\/]check4norm[\\\/]NEXT/$BASEDIR/i;
		$line =~ s/^[A-Z]:[\\\/]media[\\\/]mp3-processing[\\\/]check4norm[\\\/]NEXT.INPROGRESS/$BASEDIR/i;
		$line =~ s/^[A-Z]:[\\\/]media[\\\/]mp3-processing[\\\/]check4norm/$BASEDIR/i;

		### ^^^^ when adding there vvvvv also add with short filenames

		$line =~ s/^[A-Z]:[\\\/]media[\\\/]MP3-PR~1[\\\/]CHECK4~1[\\\/]READY-FOR-TAGGING[\\\/]in base attrib correctly,but untagged \(KEEP IN THIS FOLDER WHEN MOVING TO TESTING\)/$BASEDIR/i;
		$line =~ s/^[A-Z]:[\\\/]media[\\\/]MP3-PR~1[\\\/]CHECK4~1[\\\/]READY-FOR-TAGGING/$BASEDIR/i;
		$line =~ s/^[A-Z]:[\\\/]media[\\\/]MP3-PR~1[\\\/]CHECK4~1[\\\/]changerrecent[\\\/]/$BASEDIR/i;
		$line =~ s/^[A-Z]:[\\\/]media[\\\/]MP3-PR~1[\\\/]CHECK4~1[\\\/]DOWNLOADS/$BASEDIR/i;
		$line =~ s/^[A-Z]:[\\\/]media[\\\/]MP3-PR~1[\\\/]CHECK4~1[\\\/]NEXT/$BASEDIR/i;
		$line =~ s/^[A-Z]:[\\\/]media[\\\/]MP3-PR~1[\\\/]CHECK4~1[\\\/]NEXT.INPROGRESS/$BASEDIR/i;
		$line =~ s/^[A-Z]:[\\\/]media[\\\/]MP3-PR~1[\\\/]CHECK4~1/$BASEDIR/i;
		$line =~ s/^[A-Z]:[\\\/]mp3/$BASEDIR/i;																					#20140819 just moved this to end
		print $line;
	#}
}

#!/usr/local/bin/perl
my $DEBUG=0;

my $EXTENSION="flac";	#assuming your calling something like flac2wav, mp32wav, i.e. it's already named the way Clio names things, then editing this line is ALL you have to do
use utf8;										#20221102
use open qw( :std :encoding(UTF-8) );			#20221102
binmode(STDIN,  ':encoding(UTF-8)');
binmode(STDOUT, ':encoding(UTF-8)');


open(NEWNAMES,"$ARGV[0]")||die("couldn't open $ARGV[0]");          ##### 1st file, $tmp1, the   new    filenames
while ($filename=<NEWNAMES>) {
#while ($filename=<>) {
	chomp $filename;

	if ($DEBUG) { print "Debug: filename=$filename\n"; }
    chomp $filename;
    if ($filename !~ /\.$EXTENSION$/i) { 
		if ($DEBUG) { print "\t...NOT proper extension of $EXTENSION\n"; }
		next; 
	} else {
		if ($DEBUG) { print "\t...is proper extension of $EXTENSION\n"; }
	}

    $wavfile = $filename;
    $wavfile =~ s/\.$EXTENSION$/\.wav/i;


    ##### Use short filename to make the command line shorter:
    # NOTE: GetShortPathName doesn't work with special (foreign) characters
    my $shortfile=Win32::GetShortPathName($filename);
    if ((length($shortfile) < length($filename)) && (length($shortfile) > 0)) { $filename = $shortfile; }

    #DEBUG: print qq[rem sfn = $shortfile\n];
	print qq[call randfg\n];
    print qq[call ] . $EXTENSION . qq[2wav  "$filename" "$wavfile"\n];

}

#!/usr/local/bin/perl
use utf8;										#20221102
use open qw( :std :encoding(UTF-8) );			#20221102
binmode(STDIN,  ':encoding(UTF-8)');
binmode(STDOUT, ':encoding(UTF-8)');
my $EXTENSION="mp3";
my $fileToRead="$ARGV[0]";
open(NEWNAMES,$fileToRead) || die("echo couldn't open $fileToRead");          ##### 1st file, $tmp1, which is the new filenames
while ($filename=<NEWNAMES>) {
#hile ($file=<>) 
	print "echo this was never completed!\n";
	print "echo this was never completed!\n";
	print "echo this was never completed!\n";
	print "echo this was never completed!\n";
	print "echo this was never completed!\n";
	print "echo this was never completed!\n";
	print "echo this was never completed!\n";
	print "echo this was never completed!\n";
	print "echo this was never completed!\n";
	print "pause\n";
	print "pause\n";
	print "pause\n";
	print "pause\n";
	print "pause\n";
	print "pause\n";
	print "pause\n";
	print "pause\n";
	print "pause\n";

    chomp $file;
	print "\$file=$file\n";
    next if $file !~ /\.$EXTENSION$/i;

    $wavfile = $file;
    $wavfile =~ s/\.$EXTENSION$/\.wav/i;


    ##### Use short filename to make the command line shorter:
    # NOTE: GetShortPathName doesn't work with special (foreign) characters
    my $shortfile=Win32::GetShortPathName($file);
    if ((length($shortfile) < length($file)) && (length($shortfile) > 0)) { $file = $shortfile; }

    #DEBUG: print qq[rem sfn = $shortfile\n];
    print qq[call ] . $EXTENSION . qq[2wav "$file" "$wavfile"\n];
}

#!/usr/local/bin/perl
use utf8;										#20221102
use open ':std',':encoding(UTF-8)' ;
binmode(STDIN,  ':encoding(UTF-8)');
binmode(STDOUT, ':encoding(UTF-8)');
my $EXTENSION="mpc";
open(NEWNAMES,"$ARGV[0]");          ##### 1st file, $tmp1, the   new    filenames
while ($filename=<NEWNAMES>) {
#while ($mp3file=<>) {
    chomp $mp3file;
    next if $mp3file !~ /\.$EXTENSION$/i;

    $wavfile = $mp3file;
    $wavfile =~ s/\.$EXTENSION$/\.wav/i;


    ##### Use short filename to make the command line shorter:
    # NOTE: GetShortPathName doesn't work with special (foreign) characters
    my $shortfile=Win32::GetShortPathName($mp3file);
    if ((length($shortfile) < length($mp3file)) && (length($shortfile) > 0)) { $mp3file = $shortfile; }

    #DEBUG: print qq[rem sfn = $shortfile\n];
    print qq[call ] . $EXTENSION . qq[2wav  "$mp3file" "$wavfile"\n];
}

#!/usr/local/bin/perl
use utf8;										#20221102
use open qw( :std :encoding(UTF-8) );			#20221102
binmode(STDIN,  ':encoding(UTF-8)');
binmode(STDOUT, ':encoding(UTF-8)');


open(NEWNAMES,"$ARGV[0]");          ##### 1st file, $tmp1, the   new    filenames
while ($filename=<NEWNAMES>) {
#while ($avifile=<>) {
    chomp $avifile;
    next if $avifile !~ /\.avi$/i;

    $wavfile = $avifile;
    $wavfile =~ s/\.avi$/\.wav/i;

    my $shortfile=Win32::GetShortPathName($avifile);
    if ((length($shortfile) < length($avifile)) && (length($shortfile) > 0)) { $avifile = $shortfile; }

    print qq[avi2wav "$avifile" "$wavfile"\n];
}

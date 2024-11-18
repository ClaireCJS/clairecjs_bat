#!/usr/local/bin/perl
use open ':std',':encoding(UTF-8)' ;
binmode(STDIN,  ':encoding(UTF-8)');
binmode(STDOUT, ':encoding(UTF-8)');
use utf8;										#20221102
#use open qw( :std :encoding(UTF-8) );			#20221102

if ($ARGV[1] ne "") { 
    $destination=$ARGV[1]; 
    if ($destination !~ /[\\\/]/) { $destination .= "\\"; }
} else { $destination=""; }


while ($avifile=<>) {
    chomp $avifile;

    if ($avifile !~ /\.avi$/i) {
        if ($avifile !~ /\.wav$/i) {
            print "REM Ignoring non-avi/non-wav file: $avifile\n\n";
        }
        next;
    }

    $wavfile = $avifile;
    $wavfile =~ s/\.avi$/\.wav/i;

    if (!-e $wavfile) {
        print "REM *** WAV file does not exist, but should: $wavfile\n\n";
        next;
    }

    $newavifile = $avifile;
    $newavifile =~ s/(\.avi)$/ -- AUDIO-FROM-WAV$1/;

    print qq[start /w avimux "$avifile" "$destination$newavifile" "$wavfile" "$wavfile"\n];
    $count++;
}


print "\nREM    $count AVI files will be converted.\n";

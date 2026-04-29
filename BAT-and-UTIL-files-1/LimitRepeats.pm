package LimitRepeats;


use strict;
use warnings;
use Exporter 'import';
use utf8;

our @EXPORT = qw(
	limit_repeats
);



sub limit_repeats {
	#USAGE: $line = &limit_repeats($line,5) -- would limit any repeated character to 5 max
    my ($s, $max) = @_;
    my $result = '';
    my $last_char = '';
    my $count = 0;

    foreach my $c (split //, $s) {
        if ($c eq $last_char) {
            $count++;
        } else {
            $last_char = $c;
            $count = 1;
        }
        $result .= $c if $count <= $max;
    }

    return $result;
}


1;




#!/usr/local/bin/perl

#### THE PYTHON VERSION IS 32% SLOWER....BUT IT HANDLES EMOJI AND PERL CAN’T

### substitutes {{{{QUOTE}}}}   into "
### substitutes {{{{QUOTES}}}}  into "
### substitutes {{{{PERCENT}}}} into %
### substitutes {{{{PCT}}}}     into %
### substitutes {{{{PIPE}}}}    into |

use utf8;
binmode(STDIN,  ':encoding(UTF-8)');
binmode(STDOUT, ':encoding(UTF-8)');
use open ':std', ':encoding(UTF-8)';


my $line;
my $arg=$ARGV[0];																																	#DEBUG: #use Encode; @ARGV = map { decode("UTF-8", $_) } @ARGV;#DEBUG: #for my $arg (@ARGV) { print "Raw ARGV: ", join(" ", map { sprintf("\\x%02X", ord($_)) } split(//, $arg)), "\n"; } print "ARGV[0]: $ARGV[0]\n";

$arg =~ s/{{{{QUOTE}}}}/"/g;
$arg =~ s/{{{{QUOTES}}}}/"/g;
$arg =~ s/{{{{PERCENT}}}}/%/g;
$arg =~ s/{{{{PCT}}}}/%/g;
$arg =~ s/{{{{PIPE}}}}/|/g;

while ($line=<STDIN>) {
    chomp $line;
    print $arg . $line . "\n";
}

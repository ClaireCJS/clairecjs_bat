#!/usr/local/bin/perl

#### THE PYTHON VERSION IS 32% SLOWER....BUT IT HANDLES EMOJI

#changes {{{{QUOTE}}}} to "


my $line;

my $arg=$ARGV[0];
$arg =~ s/{{{{QUOTE}}}}/"/g;

while ($line=<STDIN>) {
    chomp $line;
    print $arg . $line . "\n";
}

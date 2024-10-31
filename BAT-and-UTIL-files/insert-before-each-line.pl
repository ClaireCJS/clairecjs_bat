#!/usr/local/bin/perl

#### THE PYTHON VERSION IS 32% SLOWER....BUT IT HANDLES EMOJI

my $line;

while ($line=<STDIN>) {
    chomp $line;
    print $ARGV[0] . $line . "\n";
}

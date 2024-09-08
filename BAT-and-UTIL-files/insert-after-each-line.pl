#!/usr/local/bin/perl

my $line;

while ($line=<STDIN>) {
    chomp $line;
    print $line . $ARGV[0] . "\n";
}

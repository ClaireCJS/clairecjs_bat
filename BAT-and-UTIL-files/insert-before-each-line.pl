#!/usr/local/bin/perl

my $line;

while ($line=<STDIN>) {
    chomp $line;
    print $ARGV[0] . $line . "\n";
}

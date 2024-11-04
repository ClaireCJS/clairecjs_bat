#!/usr/local/bin/perl

#changes {{{{QUOTE}}}} to "

my $line;

my $arg = $ARGV[0];
$arg =~ s/{{{{QUOTE}}}}/"/g;

while ($line=<STDIN>) {
    chomp $line;
    print $line . $arg . "\n";
}

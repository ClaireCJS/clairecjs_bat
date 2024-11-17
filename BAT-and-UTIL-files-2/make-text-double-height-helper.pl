#!/usr/bin/perl

# Probably need to pipe this output through fast_cat.exe to fix ANSI rendering errors with Windows Terminal + TCC

my $double_height_top    = "\e#3";		# VT100 ANSI escape code to enable double height top    line
my $double_height_bottom = "\e#4";		# VT100 ANSI escape code to enable double height bottom line

foreach my $line (<STDIN>) {			# Read lines from standard input
    print $double_height_top    .		# Print escape code to enable double height top line
          $line                 .	    # Print the line
          $double_height_bottom .	    # Print escape code to enable double height bottom line
          $line;        			    # Print the line again to complete the double height effect
}

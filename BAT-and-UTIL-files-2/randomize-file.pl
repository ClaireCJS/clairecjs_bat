my @lines     = <STDIN>;											# Read all lines into an array
my $num_lines = scalar @lines;
for (my $i = $num_lines - 1; $i > 0; $i--) {						# Fisher-Yates shuffle
    my $j = int(rand($i + 1));										# Random index between 0 and $i
    ($lines[$i], $lines[$j]) = ($lines[$j], $lines[$i]);		    # Swap lines[$i] and lines[$j]
}
print @lines;														# Print shuffled lines

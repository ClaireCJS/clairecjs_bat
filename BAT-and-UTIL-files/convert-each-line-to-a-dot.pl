# Turn on autoflush for STDOUT
$| = 1;

while (<>) { 
	# Generate a random color code (30-37)
	my $color_code = int(rand(8)) + 30;

	# ANSI escape sequence for setting foreground color
	my $ansi_rand_fg = "\e[${color_code}m";

	# Print text with random foreground color
	print "${ansi_rand_fg}.";
}
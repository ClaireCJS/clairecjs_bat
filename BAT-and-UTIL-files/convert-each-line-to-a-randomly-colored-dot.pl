                 $| = 1;									# Turn on autoflush for STDOUT for best performance
select (STDOUT); $| = 1;									# Turn on autoflush for STDOUT for best performance
binmode(STDOUT , ":encoding(UTF-8)");                       # ensure STDOUT is correct encoding

print "\e[0m";												# reset ansi colors
my $last_randcolor=30;     								    # track last color used to prevent duplicates
my $curr_randcolor;                                         # current randomly-generated color

while (<>) {												# while STDIN exists
	$curr_randcolor = int(rand(8)) + 30;					# Generate a random color code (30-37)
	while ($curr_randcolor == $last_randcolor) {			# if the color is the same as last
		$curr_randcolor = int(rand(8)) + 30;				# then re-generate it until it isn't
	}
	$last_randcolor = $curr_randcolor;						# keep track of color so next line isn't the same color
	#print "\e[${curr_randcolor}m.";						# ANSI escape sequence for setting foreground color
	#yswrite(STDOUT,"\e[${curr_randcolor}m.");				# ANSI escape sequence for setting foreground color
	syswrite(STDOUT,"\e[${curr_randcolor}m.\e[0m");  		# ANSI escape sequence for setting foreground color
}

my $APPEND=" ";					#stuff to append to each line - for tweaking this to special purposes like adding a tab or comma

#get 2 numbers
my $lower = $ARGV[0] || die("need two numbers as a range");
my $upper = $ARGV[1] || die("need two numbers as a range");
#^these 2 variable names don't make as much sense when we are going backwards :)

#count down if we are instructed to, otherwise count up
if ($upper > $lower) {
	for (my $i=$lower; $i<=$upper; $i++) { print "$i$APPEND\n"; }
} else {
	for (my $i=$lower; $i>=$upper; $i--) { print "$i$APPEND\n"; }
}
#!perl

my @LINES=();
my @OUTPUT=();
my $line="";
my $original_line="";
my $linenum=0;
while ($line=<STDIN>) {	
	$linenum++;
	$LINES[$linenum]=$line; 
}
my $NUM_LINES = $linenum;
my $FOUND=0;
for (my $currentLine=1; $currentLine<=$NUM_LINES; $currentLine++) {
	$FOUND=0;
	while ($FOUND==0) {
		$testIndex = int(rand($NUM_LINES)) + 1;
		if ($OUTPUT[$testIndex] eq "") { 
			$FOUND=1; 
			$OUTPUT[$testIndex]=$LINES[$currentLine]; 
		}
	}
}
for (my $currentLine=1; $currentLine<=$NUM_LINES; $currentLine++) { 
	print $OUTPUT[$currentLine]; 
}

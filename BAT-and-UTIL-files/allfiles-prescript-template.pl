use open ':std',':encoding(UTF-8)' ;
binmode(STDIN,  ':encoding(UTF-8)');
binmode(STDOUT, ':encoding(UTF-8)');
while ($line=<>) {
	chomp $line;													#take out the \n at the end
	#$original_line = $line;										#preserve line if we want

	#if ($_ !~ / \- /) { print $_; next; }							#skip lines we don't care about like this, which wouldn't make sense for a renaming script


	$line          =~ /^(.*)(\.[^\.]+)$/;						    #get base filename and extension
	$base          = $1;											#get base filename and extension
	$ext_with_dot  = $2;											#get base filename and extension
	#DEBUG: 
	print "* line is $line\n\t-base is $base\n\t-ext_with_dot is $ext_with_dot\n";

	##### Transformations to our filename go here
	#($left,$right)=split(/ \- /,$base);							#example of swapping around a hyphen
	#$line = "$right - $left$ext";								    #example of swapping around a hyphen

	print "$line\n";												#only add the \n back at the very end
}
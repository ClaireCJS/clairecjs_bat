use utf8;
use open ':std',':encoding(UTF-8)' ;
binmode(STDIN,  ':encoding(UTF-8)');
binmode(STDOUT, ':encoding(UTF-8)');
while (<>) {
	if ($_ !~ / \- /) { print $_; next; }
	else { 
		$line = $_;
		chomp $line;
		$line =~ /^(.*)(\..*)$/;
		$base = $1;
		$ext = $2;
		#print "line is $line base is $bse ext is $ext";
		($left,$right)=split(/ \- /,$base);
		print "$right - $left$ext\n";
	}
}
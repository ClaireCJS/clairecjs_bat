

#------------------------------------------------------------------------------
#smss.exe pid: 336 NT AUTHORITY\SYSTEM


local $exe;
local $pid;
local $name;
&resetCurrentProcessValues("");

while ($line=<>) {
	if ($line =~ /^\-\-\-\-\-\-\-/) { 
		&resetCurrentProcessValues(""); 
	} elsif ($line =~ / pid: /) {
		&resetCurrentProcessValues("PARSEFAIL");
		if ($line =~ /^(.*) pid: ([0-9]*) (.*)$/) {			#smss.exe pid: 336 NT AUTHORITY\SYSTEM
			$exe  = $1;
			$pid  = $2;
			$name = $3;
		}
	} else {
		$line = "$exe\t$pid\t$name\t$line";
	}
	print $line;
}


#################################################
sub resetCurrentProcessValues {
	my $valueToResetTo = $_[0];
	$exe  = $valueToResetTo;
	$pid  = $valueToResetTo;
	$name = $valueToResetTo;
}
#################################################

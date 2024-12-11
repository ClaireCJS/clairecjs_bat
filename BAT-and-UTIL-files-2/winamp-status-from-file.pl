use strict; 
use warnings; 
my $DEBUG=0;

 
#my $url  = "http://" . $ENV{"MUSICSERVER"} . "/main";			print_if_debug("* url is $url\n");
#   $url  = "http://" . $ENV{"MUSICSERVER"} . "/winamp?page=main";	
#my $data = <>;										    print_if_debug("* Retrieved " . length($data) . " bytes of data.\n"); print_if_debug("* data is: $data\n");
#die "couldn't get \$data" unless defined $data;

my $mode = "UNKNOWN";
foreach my $line (<STDIN>) {
	if ($DEBUG) { print "*** line is $line"; }
	#Playing track 249 - NoFX - Intro (live) -  (1:07 / 1:45)
	#Paused in track 250 - NoFX - Intro (live) -  (1:07 / 1:45)
	#Winamp is stopped at track 250 - NoFX - Liza
	if ($line =~    /Playing track/) { $mode="PLAYING"; }
	if ($line =~  /Paused in track/) { $mode="PAUSED" ; }
	if ($line =~ /stopped at track/) { $mode="STOPPED"; }
}

print $mode;													print_if_debug("\n\n* mode is $mode\n");














sub print_if_debug {
	if ($DEBUG) { print $_[0]; }
}

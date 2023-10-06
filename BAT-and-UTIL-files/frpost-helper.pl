#!/usr/local/bin/perl

$|=1;
binmode(STDOUT, ":unix");

## uncommenting this: 
#use Win32::Console::ANSI;
## causes the faint ansi in this to not work in this:
#print "\e[31mThis should be red \e[2m and this should be faint red \e[22m \e[0m\n";

# Volume in drive C is STORM -- 40    Serial number is 463E:0E06
# 40,968,290,304 bytes total disk space
# 31,206,539,264 bytes used
# 9,761,751,040 bytes free
#
# Volume in drive D is STORM -- 60    Serial number is 2863:0DE6
# 61,452,451,840 bytes total disk space
# 46,054,440,960 bytes used
# 15,398,010,880 bytes free


##### PROCESS OPTIONS:
my $DISPLAY_TOTALS=1;
if ($ARGV[0] eq "nototals") { $DISPLAY_TOTALS=0; }


my $showreald1;

while ($line=<STDIN>) {
    chomp $line;

    next if $line =~ /in use$/;
	$line =~ s/^/\e[23m/;

	$line =~ s/ Volume in drive(.*)$/💿\e[3mVolume in drive$1\e[23m/ig;

	#            function ANSI_MOVE_TO_COL=`%@CHAR[27][%1G`	                    %+ rem moves cursor to column #
	#$line =~ s/Serial number is(.*)$/\e7\e[s\e[54G\e[2m(Serial number is$1)\e[22m/i;
	$line =~ s/Serial number is(.*)$//i;

    $showreald1=0;
    if ($line =~ /([0-9,]+) bytes total disk space/i) {
        $total = $1;
        $showreald1=1;
    }#endif

    if ($line =~ /([0-9,]+) bytes used/i)             {
        $used  = $1;
        $showreald1=1;
    }#endif

    if ($line =~ /([0-9,]+) bytes free/i)             {
        $free  = $1;
        $showreald1=1;
    }#endif

    print $line;
    if ($showreald1) {
        my $reald1=$1;
        $reald1 =~ s/,//g;
        #print "reald1 is $reald1\n";

        $reald14print = &comma(sprintf("%.0f",($reald1/1024/1024/1024)))."\e[2m\e[3mG\e[23m\e[22m";
        print " ($reald14print)";

		#2023 - need terabyte summaries for drives these days :)
		#DEBUG: print " [reald1 is $reald1]";
		if ($reald1 > 1099511627776) {
			$reald2 = &comma(sprintf("%.1f",($reald1/1024/1024/1024/1024)))."\e[2m\e[3mT\e[23m\e[22m";
			print " ($reald2)";
		}
    }
    print "\n";

    $totalnice = &nocomma($total);
    $usednice  = &nocomma($used);
    $freenice  = &nocomma($free);
    #print "total is $total\n";

    if ($totalnice) {
       $pctfull = $usednice / $totalnice * 100;
       $pctfree = $freenice / $totalnice * 100;
    }

    $pctfull = sprintf("%2.1f",$pctfull);
    $pctfree = sprintf("%2.1f",$pctfree);

    if ($line =~ /([0-9,]+) bytes free/i) {
        print "  ";
		if ($totalnice <= 9999999999999) { print " "; }
		print "\e[6m\e[4m" . sprintf("%27s","$pctfull\e[24m\%\e[25m full / $pctfree\% free\n");
        $totaltotalnice += $totalnice;
        $totalusednice  += $usednice;
        $totalfreenice  += $freenice;
    }
}#endwhile

if ($totaltotalnice != 0) {
	$fullpct = sprintf("%2.2f",($totalusednice / $totaltotalnice * 100));
	$freepct = sprintf("%2.2f",($totalfreenice / $totaltotalnice * 100));
}

my $USE_TERABYTES=0;
if ($totaltotalnice/1024/1024/1024) { $USE_TERABYTES=1; }	#I forgot how this makes sense


if ($DISPLAY_TOTALS) {
	print "\n";
	print "\t    Total Usable Space: ".sprintf("%19s",&comma($totaltotalnice))." ".sprintf("%8.1f",($totaltotalnice/1024/1024/1024))."G";
	#if (($totaltotalnice/1024/1024/1024) > 1) { print "" . sprintf("%8.2f",($totaltotalnice/1024/1024/1024/1024)) . "T"; }
	if ($USE_TERABYTES) { print "" . sprintf("%8.2f",($totaltotalnice/1024/1024/1024/1024)) . "T"; }
	print "\n";
	print "\t    Total  Used  Space: ".sprintf("%19s",&comma($totalusednice) )." ".sprintf("%8.1f",($totalusednice /1024/1024/1024))."G";
	if ($USE_TERABYTES) { print "" . sprintf("%8.2f",($totalusednice/1024/1024/1024/1024)) . "T"; }
	print "\n";
	print "\t    Total  Free  Space: ".sprintf("%19s",&comma($totalfreenice) )." ".sprintf("%8.1f",($totalfreenice /1024/1024/1024))."G";
	if ($USE_TERABYTES) { print "" . sprintf("%8.2f",($totalfreenice/1024/1024/1024/1024)) . "T"; }
	print "\n";
	print "\tPercentage Free (Full): ".sprintf("%23s","") . sprintf("%7s","$freepct\%  (\e[21m\e[6m$fullpct\e[24m\%\e[25m full)") . " " . "\n";
}


##########################################
sub nocomma {
	my $s = $_[0];
	$s =~ s/,//g;
	return($s);
}#endsub nocomma
##########################################
#############################################
sub comma {
	my $s = $_[0];
	while ($s =~ /[0-9]{4}/) {
		$s =~ s/([0-9])([0-9]{3})$/$1,$2/g;
		$s =~ s/([0-9])([0-9]{3}),/$1,$2/g;
	}
	return($s);
}#endsub comma
#############################################

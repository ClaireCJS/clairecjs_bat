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
my $ANSI_RESET                = "\e[0m" ;
my $ANSI_BOLD_ON              = "\e[1m" ;
my $ANSI_BOLD_OFF             = "\e[24m";
my $ANSI_BLINK_ON             = "\e[6m" ;
my $ANSI_BLINK_OFF            = "\e[25m";
my $ANSI_ITALICS_ON           = "\e[3m" ;
my $ANSI_ITALICS_OFF          = "\e[23m";
my $ANSI_FAINT_ON             = "\e[2m" ;
my $ANSI_FAINT_OFF            = "\e[22m";
my $ANSI_UNDERLINE_ON         = "\e[4m" ;
my $ANSI_UNDERLINE_OFF        = "\e[24m";
my $ANSI_DOUBLE_UNDERLINE_ON  = "\e[53m";
my $ANSI_DOUBLE_UNDERLINE_OFF = "\e[55m";

my $KILOBYTE=1024;
my $MEGABYTE=1024*1024;
my $GIGABYTE=1024*1024*1024;
my $TERABYTE=1024*1024*1024*1024;
my $TEN_TERABYTES=10*1024*1024*1024*1024;
my $HUNDRED_TERABYTES=100*1024*1024*1024*1024;

my $msg="";
while ($line=<STDIN>) {
    chomp $line;

    next if $line =~ /in use$/;

	$line =~ s/^/\e[23m/;

	if ($line =~ /Volume in drive/) {
		print &colorprint($pctfull,0) . $msg;
		$msg="";
		$line =~ s/ Volume in drive(.*)$/💿\e[3mVolume in drive$1$ANSI_FAINT_ON/ig;
	}

	#            function ANSI_MOVE_TO_COL=`%@CHAR[27][%1G`	                    %+ rem moves cursor to column #
	#$line =~ s/Serial number is(.*)$/\e7\e[s\e[54G\e[2m(Serial number is$1)\e[22m/i;
	$line =~ s/Serial number is(.*)$//i;

    $showreald1=0;
    if ($line =~ /([0-9,]+) bytes total disk space/i) {
		$line = $ANSI_FAINT_ON . $line;
        $total      = $1;
        $showreald1 =  1;
		$line =~ s/ disk space//;
    }#endif

    if ($line =~ /([0-9,]+) bytes used/i)   {
		$line = $ANSI_FAINT_ON . $line;
        $used       = $1;
        $showreald1 =  1;
		$line =~ s/bytes used/bytes used /;
    }#endif

    if ($line =~ /([0-9,]+) bytes free/i) {
		$line = $ANSI_FAINT_ON . $line;
        $free       = $1;
        $showreald1 =  1;
		$line =~ s/bytes free/bytes free /;
		if (($freenice<$TEN_TERABYTES) && ($totalnice>$TEN_TERABYTES)) { $line =~ s/bytes free/bytes free /; }
    }#endif


    $totalnice = &nocomma($total);
    $usednice  = &nocomma($used);
    $freenice  = &nocomma($free);
    #$msg .= "total is $total\n";

    if ($totalnice) {
       $pctfull = $usednice / $totalnice * 100;
       $pctfree = $freenice / $totalnice * 100;
    }

    $pctfull = sprintf("%2.1f",$pctfull);
    $pctfree = sprintf("%2.1f",$pctfree);


    $msg .= $line;
    if ($showreald1) {
        my $reald1=$1;
        $reald1 =~ s/,//g;
        #$msg .= "reald1 is $reald1\n";

		#### PRINT GIGABYES, THEN TERABYTES {added 2023}:
        $reald14print = &comma(sprintf("%.0f",($reald1/1024/1024/1024))     ) . "G" . $ANSI_ITALICS_OFF;   $msg .= " ($reald14print)";
		if ($reald1 > 1099511627776) { #DEBUG: $msg .= " [reald1 is $reald1]";
			$reald2   = &comma(sprintf("%.1f",($reald1/1024/1024/1024/1024))) . "T" . $ANSI_ITALICS_OFF;   $msg .= " " . "[";
		    if (($freenice<$TEN_TERABYTES) && ($totalnice>$TEN_TERABYTES) && $line =~ /bytes free/) { $msg .= " "; }

			$msg .= "$ANSI_FAINT_OFF$reald2$ANSI_FAINT_ON]";
		}
    }
    $msg .= "$ANSI_FAINT_OFF\n";

    if ($line =~ /([0-9,]+) bytes free/i) {
        $msg .= "  ";
		#$msg .= "[totalnice=$totalnice]";
		if ($totalnice <= 10000000000000) { $msg .= " " ; }
		if ($totalnice <=  1000000000000) { $msg .= " "; }													#to truly line up this should be 2psaces because of the comma
		#$msg .= "\e[4m" ;
		$msg .= &colorprint($pctfull,0);
		$msg .= sprintf("%27s",&colorprint($pctfull,1) . "\%$ANSI_UNDERLINE_OFF full / $pctfree\% free$ANSI_RESET\n");
        $totaltotalnice += $totalnice;
        $totalusednice  += $usednice;
        $totalfreenice  += $freenice;
    }
}#endwhile

print &colorprint($pctfull,0);
print $msg; $msg="";

if ($totaltotalnice != 0) {
	$fullpct = sprintf("%2.2f",($totalusednice / $totaltotalnice * 100));
	$freepct = sprintf("%2.2f",($totalfreenice / $totaltotalnice * 100));
}

my $USE_TERABYTES=0;
if ($totaltotalnice/1024/1024/1024) { $USE_TERABYTES=1; }	#I forgot how this makes sense


#my $FINAL_ANSI  = "\e[38;2;192;48;192m";
my $FINAL_ANSI = "\e[48;2;0;64;02m\e[38;2;204;48;204m";


if ($DISPLAY_TOTALS) {
	my $SPACER = "    ";
	print "$FINAL_ANSI\n\n";
	print "$SPACER    Total Usable Space: ".sprintf("%19s",&comma($totaltotalnice))." ".sprintf("%8.1f",($totaltotalnice/1024/1024/1024))."G";
	#if (($totaltotalnice/1024/1024/1024) > 1) { print "" . sprintf("%8.2f",($totaltotalnice/1024/1024/1024/1024)) . "T"; }
	if ($USE_TERABYTES) { print "" . sprintf("%8.2f",($totaltotalnice/1024/1024/1024/1024)) . "T"; }
	print "\n";
	print "$SPACER    Total  Used  Space: ".sprintf("%19s",&comma($totalusednice) )." ".sprintf("%8.1f",($totalusednice /1024/1024/1024))."G";
	if ($USE_TERABYTES) { print "" . sprintf("%8.2f",($totalusednice/1024/1024/1024/1024)) . "T"; }
	print "\n";
	print "$SPACER    Total  Free  Space: ".sprintf("%19s",&comma($totalfreenice) )." ".sprintf("%8.1f",($totalfreenice /1024/1024/1024))."G";
	if ($USE_TERABYTES) { print "" . sprintf("%8.2f",($totalfreenice/1024/1024/1024/1024)) . "T"; }
	print "\n";
	print "${SPACER}Percentage Free (Full): ".sprintf("%17s","") . sprintf("%7s","🌟🌟🌟 $freepct\%  (\e[21m" . &colorprint($fullpct,1) . "\e[24m\%\e[25m full") . "$ANSI_RESET$FINAL_ANSI) 🌟🌟🌟\n";
	print "$ANSI_RESET\n";
}

sub colorprint($) {
    my ($s,$to_print) = @_;
	my $retval="";

    # Convert the string to a number
    my $value = $s + 0;

    my ($r, $g, $b) = (255, 0, 0); # Default to red

	#print "Value is $value\n";

	my $blink = 0;
	if ($value < 70) {
		# Green to yellow-like green gradient
		$r = int($value / 60 * 255); # Increasing red component for the yellow-green transition
		$g = 255;
		$b = 0;
		if (1 && ($value > 50)) {
			$factor = .85;
			$r = int($r*$factor);
			$g = int($g*$factor);
			$blink = 0;
		}
	} elsif ($value < 80) {
		# Yellow to orange-like yellow gradient
		$r = 255;
		$g = int(255 - (($value - 60) / 20 * 90)); # Decreasing green component for the yellow-orange transition
		$b = 0;
		$factor = 1.3;
		$r = int($r*$factor); if ($r > 255) { $r=255; }
		$g = int($g*$factor); if ($g > 255) { $g=255; }
		$blink = 0;
	} elsif ($value < 90) {
		# Orange to red gradient
		$r = 255;
		$g = int(165 - (($value - 80) / 10 * 96)); # Further decreasing green component for the orange-red transition
		$b = 0;
		$blink = 0;
	} elsif ($value < 98) {
		# Red
		$r = 255;
		$g = int(69 - (($value - 90) / 8 * 69)); # Reducing green to 0 for bright red
		$b = 0;
		$blink = 0;
	} else {
		# Bright red with blinking for >= 98%
		$r = 255;
		$g = 0;
		$b = 0;
		$retval .= $ENV{BLINK_ON};
		$blink = 1;
	}

    # Print the value with color
	$retval .= "\e[38;2;$r;$g;$b" . "m";
	if ($to_print != 0) { 
		$retval .= $ANSI_UNDERLINE_ON ;
		$retval .= $s;
		$retval .= $ANSI_UNDERLINE_OFF;
		#$retval .= $ANSI_RESET;
	}

    # Turn off blinking if it was turned on
    if ($blink) { $retval .= $ENV{BLINK_OFF}; }

    return(      $retval      );
    return('[' . $retval . ']');
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

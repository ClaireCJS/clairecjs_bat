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


my $format_line;
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

my         $KILOBYTE =                     1024;     my         $KILOBYTE_WRONG =                     1000;	#1000
my         $MEGABYTE =                1024*1024;     my         $MEGABYTE_WRONG =                1000*1000;	#1000000
my         $GIGABYTE =           1024*1024*1024;     my         $GIGABYTE_WRONG =           1000*1000*1000;	#1000000000
my     $TEN_GIGABYTE =        10*1024*1024*1024;     my     $TEN_GIGABYTE_WRONG =        10*1000*1000*1000;	#10000000000
my $HUNDRED_GIGABYTE =       100*1024*1024*1024;     my $HUNDRED_GIGABYTE_WRONG =       100*1000*1000*1000;	#100000000000
my         $TERABYTE =      1024*1024*1024*1024;     my         $TERABYTE_WRONG =      1000*1000*1000*1000;	#1000000000000
my     $TEN_TERABYTE =   10*1024*1024*1024*1024;     my     $TEN_TERABYTE_WRONG =   10*1000*1000*1000*1000;	#10000000000000
my $HUNDRED_TERABYTE =  100*1024*1024*1024*1024;     my $HUNDRED_TERABYTE_WRONG =  100*1000*1000*1000*1000;	#100000000000000
my         $PETABYTE = 1024*1024*1024*1024*1024;     my         $PETABYTE_WRONG = 1000*1000*1000*1000*1000; #1000000000000000

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

	#——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————

	#            function ANSI_MOVE_TO_COL=`%@CHAR[27][%1G`	                    %+ rem moves cursor to column #
	#$line =~ s/Serial number is(.*)$/\e7\e[s\e[54G\e[2m(Serial number is$1)\e[22m/i;
	$line =~ s/Serial number is(.*)$//i;

	#——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————

    $format_line = 0;

    if ($line =~ /([0-9,]+) bytes total disk space/i) {
		$line        = $ANSI_FAINT_ON . $line;
        $total       = $1;
        $totalnice   = &nocomma($total);
        $format_line =  1;
		$line        =~ s/ disk space//;
    }#endif
    #$msg .= "total is $total\n";


	#——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————

    if ($line =~ /([0-9,]+) bytes used/i)   {
		$line        = $ANSI_FAINT_ON . $line;
        $used        = $1;
		$usednice    = &nocomma($used);
        $format_line =  1;
		$line        =~ s/bytes used/bytes used /;
    }#endif

	#——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————

	if ($line =~ /([0-9,]+) bytes free/i) {
		$line        = $ANSI_FAINT_ON . $line;
        $free        = $1;
        $freenice    = &nocomma($free);
        $format_line =  1;
		$line        =~ s/bytes free/bytes free /;
    }#endif
	#print "Freenice is $freenice";

	#——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————

	#————————————————————————————————————————————— COMPUTE SUMMARY VALUES: ———————————————————————————————————————————————
    if ($totalnice) {
       $pctfull = $usednice/$totalnice * 100; $pctfull = sprintf("%2.1f",$pctfull);
       $pctfree = $freenice/$totalnice * 100; $pctfree = sprintf("%2.1f",$pctfree);
    }
	$freenice4print = &comma(sprintf("%.0f",($freenice/$GIGABYTE))     );
	#————————————————————————————————————————————— COMPUTE SUMMARY VALUES ————————————————————————————————————————————————


    $msg .= $line;
    if ($format_line) {
		#### PRINT GIGABYTES: {added 2001}

		if (($line =~ /bytes used/) && ($usednice < $TERABYTE_WRONG) && ($totalnice > $TERABYTE_WRONG)) { $msg .= "  "; }				#if (($line =~ /bytes used/) && ($usednice < $TERABYTE) && ($totalnice > $TEN_TERABYTE)) { $msg .= " " ; }


		$msg .= " ($freenice4print" . "G" . $ANSI_ITALICS_OFF . ")";		#if ($freenice > $TERABYTE) { #DEBUG: $msg .= " [freenice is $freenice]";

		#### PRINT TERABYTES {added 2023}:
		if ($totalnice > $TERABYTE) {																									#DEBUG: $msg .= " [reald1 is $freenice]";	#trying 20240126
			$freenice_as_terabytes   = &comma(sprintf("%.1f",($freenice/$TERABYTE))) . "T" . $ANSI_ITALICS_OFF;   
			$msg .= " " . "[";
			if (($freenice<$TEN_TERABYTE_WRONG) && ($totalnice>$TEN_TERABYTE_WRONG)) { $msg .= " "; }
			if (($freenice<$TEN_TERABYTE_WRONG) && ($totalnice>$TEN_TERABYTE_WRONG)) { $msg .= " "; }
			$msg .= "$ANSI_FAINT_OFF$freenice_as_terabytes$ANSI_FAINT_ON]";
		}
    }
    $msg .= "$ANSI_FAINT_OFF\n";
	#$msg .= "[totalnice=$totalnice]\n";

    if ($line =~ /([0-9,]+) bytes free/i) {										#summary line for each drive {NOT the grand summary}
		if ($totalnice <=         $PETABYTE_WRONG) { $msg .= "!" ; }
		if ($totalnice <= $HUNDRED_TERABYTE_WRONG) { $msg .= "!" ; }			#10000695029760 is
		if ($totalnice <=     $TEN_TERABYTE_WRONG) { $msg .= "!" ; }			# 4000650883072 is
		if ($totalnice <=         $TERABYTE_WRONG) { $msg .= "!"; }			    #  999452307456 is		
		if ($totalnice <=         $GIGABYTE_WRONG) { $msg .= "!" ; }			
		if ($totalnice <=         $MEGABYTE_WRONG) { $msg .= "!" ; }						
		$msg .=                 &colorprint($pctfull,0);
		#$msg .= sprintf("%27s",&colorprint($pctfull,1) . "\%" . "$ANSI_UNDERLINE_OFF full / $pctfree\% free$ANSI_RESET\n");
		$msg .=                 &colorprint($pctfull,1) . "\%" . "$ANSI_UNDERLINE_OFF full / $pctfree\% free$ANSI_RESET\n";
        $totaltotalnice += $totalnice;
        $totalusednice  += $usednice;
        $totalfreenice  += $freenice;
    }
}#endwhile


print &colorprint($pctfull,0);
print $msg; $msg="";

#——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————

if ($totaltotalnice != 0) {
	$fullpct = sprintf("%2.2f",($totalusednice / $totaltotalnice * 100));
	$freepct = sprintf("%2.2f",($totalfreenice / $totaltotalnice * 100));
}

my $USE_TERABYTES=0;
if ($totaltotalnice/$GIGABYTE) { $USE_TERABYTES=1; }	#I forgot how this makes sense

#y $FINAL_ANSI = "\e[38;2;192;48;192m";
my $FINAL_ANSI = "\e[48;2;0;64;02m\e[38;2;204;48;204m";

if ($DISPLAY_TOTALS) {
	my $SPACER = "    ";	#currently 4 spaces
	print "$FINAL_ANSI\n";

	print "${SPACER}    Total Usable Space: ".sprintf("%19s",&comma($totaltotalnice))." ";
	print sprintf("%6.1f",($totaltotalnice/$GIGABYTE))."G";	if ($USE_TERABYTES) { print "" . sprintf("%5.1f",($totaltotalnice/$TERABYTE)) . "T                 "; }	print "\n";
	print "${SPACER}    Total  Used  Space: ".sprintf("%19s",&comma($totalusednice) )." ";
	print sprintf("%6.1f",($totalusednice /$GIGABYTE))."G";	if ($USE_TERABYTES) { print "" . sprintf("%5.1f",($totalusednice /$TERABYTE)) . "T                 "; }	print "\n";
	print "${SPACER}    Total  Free  Space: ".sprintf("%19s",&comma($totalfreenice) )." ";
	print sprintf("%6.1f",($totalfreenice /$GIGABYTE))."G";	if ($USE_TERABYTES) { print "" . sprintf("%5.1f",($totalfreenice /$TERABYTE)) . "T                 "; }	print "\n";
	print "${SPACER}Percentage Free (Full): ".sprintf("%16s",           ""          )." ";
	print sprintf(  "%7s","🌟🌟🌟 $freepct\% (\e[21m" . &colorprint($fullpct,1) . "\e[24m\%\e[25m full") . "$ANSI_RESET$FINAL_ANSI) 🌟🌟🌟    \n$ANSI_RESET";
}



sub colorprint($) {
    my ($s,$to_print) = @_;
	my $retval="";

    my $value = $s + 0;			    # Convert the string to a number

    my ($r, $g, $b) = (255, 0, 0);	# Default to red
	#print "Value is $value\n";

	my $blink = 0;
	if ($value < 75) {				# Green to yellow-like green gradient
		$r = int($value / 60 * 255); # Increasing red component for the yellow-green transition
		$g = 255;
		$b = 0;
		if (1 && ($value > 50)) {
			$factor = .85;
			$r = int($r*$factor);
			$g = int($g*$factor);
			$blink = 0;
		}
	} elsif ($value < 82) {			# Yellow to orange-like yellow gradient
		$r = 255;
		$g = int(255 - (($value - 60) / 20 * 90)); # Decreasing green component for the yellow-orange transition because these just...loooked too green
		$b = 0;
		$factor = 1.3;
		$r = int($r*$factor); if ($r > 255) { $r=255; }
		$g = int($g*$factor); if ($g > 255) { $g=255; }
		$blink = 0;
	} elsif ($value < 89) {		    # Orange to red gradient
		$r = 255;
		$g = int(165 - (($value - 80) / 10 * 96)); # Further decreasing green component for the orange-red transition because these lookd too green
		$b = 0;
		$blink = 0;
	} elsif ($value < 96) {			# Red
		$r = 255;
		$g = int(69 - (($value - 90) / 8 * 69));   # Reducing green to near-0 for bright red
		$b = 0;
		$blink = 0;
	} else {						# Bright red with blinking
		$r=255; $g=0; $b=0;
		$retval .= $ANSI_BLINK_ON;
		$blink = 1;
	}

    # Print the value with color
	                       $retval .= "\e[38;2;$r;$g;$b" . "m";
	if ($to_print != 0) {  $retval .= $ANSI_UNDERLINE_ON . $s . $ANSI_UNDERLINE_OFF; }
    if ($blink)          { $retval .=                               $ANSI_BLINK_OFF; }    # Turn off blinking if it was turned on

    return(      $retval      );
    #eturn('[' . $retval . ']');
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

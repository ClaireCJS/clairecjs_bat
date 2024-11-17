#!/usr/local/bin/perl
use open ':std',':encoding(UTF-8)' ;
binmode(STDIN,  ':encoding(UTF-8)');
binmode(STDOUT, ':encoding(UTF-8)');

#allfiles wav2mp3


##### After 10+ yrs of happiness, XING CBR encoder no longer works under Windows 7. Now switching to LAME which doesn't put "000" after its bitrates the way XING does:
if ($ENV{"OS"} eq "7") { $LAME=1; } else { $LAME=0; }
if (!$LAME)      { $SUFFIX="000"; } else { $SUFFIX=""; }




my @bitrates=(24000,32000,48000,56000,64000,
				#80000,							#This one seems to be bad nowadays! [2009]
			  96000,112000,128000,160000,192000,224000,256000,320000);
my @bitratesSHORT=(24,32,48,56,64,
				#80,							#This one seems to be bad nowadays! [2009]
				96,112,128,160,192,224,256,320);
my $tmpbitrate="";
my $match=0;


if (-e "__ mono __") { $ALL_MONO=1; }


##### MODE: Renaming downloads, or rips?
if ($ARGV[1] =~ /^[\-\/]d$/i) {
    $MODE="downloaded";
    $default_command = "wav2mp3x";
} else {
    $MODE="ripped";
    $default_command = "wav2mp3";
}
print "title Encoding...\n";
#print ": $ARGV[0] $ARGV[1] $ARGV[2]\n";
print ": mode=$MODE, default_command=$default_command\n";


while ($wavfile=<>) {
	##### Skip non-wavs:
    chomp $wavfile;
    if ($wavfile !~ /\.wav$/i) {
         if ($wavfile =~ /^_/) { print qq[: skipping $wavfile\n]; }
         next;
    }
    $mp3file = $wavfile;
    $mp3file =~ s/\.wav$/\.mp3/i;

    $command=$default_command;			#a BAT file

    $options=""; $bitrate=0; $MONO=0;

    if ($wavfile =~ / VBR[^a-z]/) { $options .= ""; $command="wav2mp3x"; }				### Sometimes I tag things like "VBR 192kbps" because they are technically VBR but really hover around 192kbps mostly and may as well be encodedl ike a CBR 192kbps mp3. This is very rare.
    if ($wavfile =~ /([0-9]+)kbps/) {													### Encode at the proper bitrate
		$options .= $1;
		if (!$LAME) { $options .= "000"; }
		$bitrate=1; 
	}
    if ($wavfile =~ /([0-9]+)kHz/i) {													### If the file is a certian number of kHz, we need to only sample at that level
		if (!$LAME) { 
			$options .= " -r"; 
		} else {
			#Lame has an option for this, but it requires more programming here because you actually have to tell it the sample rate, while Xing just detected it. 
			#For now we just won't do it until we care enough to fix this.
		}
	}								
    if (($wavfile !~ /phased/i) && ($wavfile =~ /[^a-z]mono[^a-z]/i)) { $MONO=1; }		### If the file is mono, we need to sample it as such
    if (($wavfile =~ /phased/i) && ($bitrate)) {										### If the file is "phased" (when I add reverb by delaying 1 channel to make it work in surround better) we round up to 9600kbps
		#remove any mono command parameters:
		if (!$LAME) {
	        $options =~ s/ \-d//;											
		} else {
	        $MONO=0; $options =~ s/ \-m m//;					
		}
		if (!$LAME) { if ($options =~ /([0-9]+000)/) { if ($1 < 96000) { $options =~ s/$1/96000/; } } } 
		else        { if ($options =~ /-b ([0-9]+)/) { if ($1 < 96   ) { $options =~ s/$1/96/   ; } } }
    }

	if ($ALL_MONO) { $MONO=1; }
	if (!$bitrate) {
		#if (-e "__ 160kbps __") { $bitrate=160000; if ($MODE ne "downloaded") { $options .= " $bitrate"; } }
		#if (-e "__ 256kbps __") { $bitrate=256000; }
		$match=0;
		foreach $tmpbitrate (@bitratesSHORT) {
		    if (-e "__ ".$tmpbitrate."kbps __")       { $bitrate=$tmpbitrate.$SUFFIX; $match=1; }
		    if (-e "__ ".$tmpbitrate."kbps 48kHz __") { $bitrate=$tmpbitrate.$SUFFIX; $match=1;  }
		    if (-e "__ ".$tmpbitrate."kbps mono __")  { $bitrate=$tmpbitrate.$SUFFIX; $match=1; $MONO=1; }
		}
		if (($match) && ($MODE ne "downloaded")) { $options .= " $bitrate"; }
	
	}
    if ($MONO) { 
		if (!$LAME) { $options .= " -d";                                } 
		else        { $options .=  " -m m"; $options  =~ s/ ?\-m j / /; }
	} else {
		#LAME-only when this was written - we dropped Xing around 2013
		$options .=  " -m j"; 
		$options  =~ s/ ?\-m m / /;
	}

    if ($bitrate) { $command="wav2mp3x"; }
    if (!$bitrate && ($MODE eq "downloaded")) {
        $command = "wav2mp3x";
        $bitrate = "128$SUFFIX";
        $options .= " $bitrate";
    }




#print "\n:bitrate=\"$bitrate\", options=\"$options\" for $wavfile\n";
#if ($bitrate) { print ":$bitrate is true\n"; }
#else { print ":$bitrate is false\n"; }

    #If we have a weird bitrate we should fix it...
    if ($options =~ /\-b ([0-9]+)/) {
        foreach (@bitrates) { if ($1==$_) { goto FINE; } }
        my $newbitrate=$1;
        foreach (@bitrates) { if ($1==$_) { goto FINE; $bitrate++; } }
    }
    FINE:

    ##### Use short filename to make the command line shorter so we don't hit BAT file limits:
    my $shortfile=Win32::GetShortPathName($wavfile);
    if ((length($shortfile) < length($wavfile)) && (length($shortfile) > 0)) { $wavfile = $shortfile; }

    print qq[call randcolor\n];
    print qq[call $command "$wavfile" "$mp3file" $options\n];
}


print "beep\n";
#pint "call white-noise 1\n";
print "call fix-window-title\n";


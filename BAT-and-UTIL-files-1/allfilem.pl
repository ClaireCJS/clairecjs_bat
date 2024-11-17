#!/usr/local/bin/perl


#use strict;		
#use vars qw($PARENTHESIS);
use utf8;										#20221102
use open qw( :std :encoding(UTF-8) );			#20221102
binmode(STDIN,  ':encoding(UTF-8)');
binmode(STDOUT, ':encoding(UTF-8)');

my $MAX_FILENAME_LENGTH=101;

my %FILENAMES=();
my $filename="";
my @LINES=();
my $line;
my $BREAK;
my %FILEAMES=();					#hash of used filenams
open(NEWNAMES,"$ARGV[0]") || die ("could not open $ARGV[0] goddamnit");          ##### 1st file, $tmp1, the   new    filenames
while ($line=<NEWNAMES>) {
#while ($line=<STDIN>) {
	chomp $line;
	push(@LINES,$line);
	$FILENAMES{$line}="1";
}
close(NEWNAMES); ##### #wasn't that easy?. NO!
my $original_filename;
foreach $filename (@LINES) {
	#DEBUG: print "filename is $filename\n";
	$filename          = &remove_leading_and_trailing_spaces($filename);
	$original_filename = $filename;

	$BREAK=0;
	while ((length($filename) > $MAX_FILENAME_LENGTH) && (!$BREAK)) {
		#DEBUG: print "filename is $filename\n";
		#rules should be ordered such that the things that aren't as
		#bad to abbreviate are abbreviated before the things that are
		#annoying to abbreviate
		if (0) {
			#This just makes it easier to insert rules at the top.

		# MEAT
		} elsif ($filename =~  /\(widescreen\)/i) {
			     $filename =~ s/\(widescreen\)/(ws)/i;			
		} elsif ($filename =~  /high-pitched/) {
			     $filename =~ s/high-pitched/hp/;
		} elsif ($filename =~  /\) \(/) {
			     $filename =~ s/\) \(/)(/;
		} elsif ($filename =~  / snd\)/i) {
			     $filename =~ s/ snd\)/)/i;
		} elsif ($filename =~  / - /i) {
			     $filename =~ s/ - /-/i;
		} elsif ($filename =~  /\(xvid\)/i) {
			     $filename =~ s/\(xvid\)/(xv)/i;
		} elsif ($filename =~  /\(divx[34576]?\)/i) {
			     $filename =~ s/\(divx[34576]?\)//i;
		} elsif ($filename =~  / \(/i) {			#))))))))))
			     $filename =~ s/ \(/(/i;			#))))))))))
		} elsif ($filename =~  /\(([0-9\.]+)fps\)/i) {
			     $filename =~ s/\(([0-9\.]+)fps\)/($1f)/i;
		} elsif ($filename =~  /uncr vhs/i) {
			     $filename =~ s/uncr vhs/uncrVHS/i;
		} elsif ($filename =~  /\)\(/) {
				 $filename =~ s/\)\(/,/;
		} elsif ($filename =~  /48kHz hissy/i) {
			     $filename =~ s/48kHz hissy/48kHzHissy/i;
		} elsif ($filename =~  /buzzy hissy/i) {
			     $filename =~ s/buzzy hissy/BuzzyHissy/i;
		} elsif ($filename =~  /BuzzyHissy/i) {
			     $filename =~ s/BuzzyHissy/BuzzHiss/i;
		} elsif ($filename =~  /no theme or credits/i) {
			     $filename =~ s/no theme or credits/no th or cr/i;
		} elsif ($filename =~  /no credits/i) {
			     $filename =~ s/no credits/no cr/i;

		#BLANKS:
		#} elsif ($filename =~  //i) {
			     #$filename =~ s///i;
		#} elsif ($filename =~  //i) {
			     #$filename =~ s///i;
		#} elsif ($filename =~  //i) {
			     #$filename =~ s///i;

		} else { 
			print ": WARNING : $filename is still too long for $original_filename\n";
			$BREAK=1;
		}
	}

	### DONE MASSAGING FILENAME, PRINT IT OUT:
    print "mv \"$original_filename\" \"$filename\"\n";                 #print the (possibly) new name
	print ":^^ length changed from " . length($original_filename) . " to " . length($filename) ."\n\n";
}#endwhile
##############################################################################
################################## END MAIN ##################################
##############################################################################


###############################################################################
sub remove_leading_and_trailing_spaces {
	my $s = $_[0];
	$s =~ s/\s+$//;
	$s =~ s/^\s+//;
	return($s);
}
###############################################################################





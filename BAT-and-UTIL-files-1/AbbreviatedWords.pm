package AbbreviatedWords;

use strict;
use warnings;
use Exporter 'import';
use utf8;
our @EXPORT = qw(
	remove_period_from_end_of_line_unless_abbreviation
	abbreviated_words
	abbreviated_words_regex
);

################################## CONFIG: LIST OF ABBREVIATIONS: ################################## 
our @abbreviated_words = qw(                                                                             
	Mr Dr Jr Sr Ms Mrs Mx Prof St Fr etc vs v. e.g i.e viz Hon Gen Col Capt Adm Sen              
	Rev Gov Pres Lt Cmdr Sgt Pvt Maj Ave Blvd Rd Hwy Pk Pl Sq Ln Ct                              
	Inc Corp Ltd Co LLP Intl Assoc Org Co. Mt Ft    Vol Ch Sec Div Dep Dept                      
	U.S U.K U.N U.A.E E.U A.T.M I.M.F W.H.O N.A.S.A                                              
	Ph.D M.D B.A M.A D.D.S J.D D.V.M B.Sc M.B.A B.F.A M.F.A                                      
	A.D B.C BCE CE C.E B.P T.P R.C A.C a.m p.m A.M P.M                                           
	St. N.Y. L.A. D.C. Chi. S.F. B.K.                                                            
	approx esp fig min     std var coeff corr dep est lim val eq dif exp                         
	opp alt gen rel abs simp conv coeff asym diag geom alg trig calc                             
	vol chap pg sec ex exs     ref       fig     sup eqn prop cor sol prob                       
	adj adv     aux cl     conj det exclam intj n. nn np vb prn pron                             
);
our $abbreviated_words_regex = join '|', map { quotemeta } @abbreviated_words;                          # Build a regex from exceptions, escaping special characters

sub remove_period_from_end_of_line_unless_abbreviation {
	my $s = $_[0];	
	if    ( $s =~ /\.\.\.\s*$/) { $s =~ s/\.\.\.\.$/.../; }												# Check if line ends with ellipses (“..."), if so, don’t use our period-removal code, but DO change a line ending in “....” to “...”
	elsif ( $s =~ /(\b(?:$abbreviated_words_regex))\.\s*$/i) { }										# Otherwise, check if the line ends with a recognized exception (“Ms.”)
	else  { $s =~ s/\.\s*$//;}																			# Remove a single trailing period (and spaces) including our “invisible periods”
	return ($s);
}

1;







### ######## Original list, which may have been slightly modified for reasons: ######## 
#   Mr Dr Jr Sr Ms Mrs Mx Prof St Fr etc vs v. e.g i.e viz Hon Gen Col Capt Adm Sen                    # Titles and general abbreviations
#   Rev Gov Pres Lt Cmdr Sgt Pvt Maj Ave Blvd Rd Hwy Pk Pl Sq Ln Ct                                    # Street, road, and location abbreviations
#   Inc Corp Ltd Co LLP Intl Assoc Org Co. Mt Ft No Vol Ch Sec Div Dep Dept                            # Corporate and geographic terms
#   U.S U.K U.N U.A.E E.U A.T.M I.M.F W.H.O N.A.S.A                                                    # Country and organizational abbreviations
#   Ph.D M.D B.A M.A D.D.S J.D D.V.M B.Sc M.B.A B.F.A M.F.A                                            # Academic and professional degrees
#   A.D B.C BCE CE C.E B.P T.P R.C A.C a.m p.m A.M P.M                                                 # Historical and time-related terms
#   St. N.Y. L.A. D.C. Chi. S.F. B.K.                                                                  # Common city/state abbreviations
#   approx esp fig min     std var coeff corr dep est lim val eq dif exp                               # Scientific and statistical abbreviations: removed some
#   opp alt gen rel abs simp conv coeff asym diag geom alg trig calc                                   # Mathematical and geometric terms
#   vol chap pg sec ex exs     ref       fig     sup eqn prop cor sol prob                             # Book and academic citations: removed some
#   adj adv     aux cl     conj det exclam intj n. nn np vb prn pron                                   # Grammatical and linguistic abbreviations: removed some
#   #approx esp fig min max std var coeff corr dep est lim val eq dif exp                              # Scientific and statistical abbreviations
#   #vol chap pg sec ex exs add ref trans fig app sup eqn prop cor sol prob                            # Book and academic citations
#   #adj adv art aux cl con conj det exclam intj n. nn np vb prn pron pro                              # Grammatical and linguistic abbreviations

################################################################################################################################################################################################################################################
################################################################################################################################################################################################################################################
################################################################################################################################################################################################################################################

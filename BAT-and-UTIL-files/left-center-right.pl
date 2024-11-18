#!/usr/bin/perl
use strict;
use warnings;

# Check for valid input
die "Usage: $0 player1 player2 [player3...]\n" if @ARGV < 2;

my @players = @ARGV;
my @chips = (3) x @players;

my $center = 0;
my $total_chips_in_play = 3 * @players;
my $num_turns=0;
my $num_rolls=0;
my $num_rolled=0;
my $game_over = 0;

my $dot='. (keep)';
sub roll {
    my @faces = ($dot, $dot, $dot, 'left', 'center', 'right');
	$num_rolled++;
    return $faces[int(rand(6))];
}

TURN: 
while (grep { $_ > 0 } @chips > 1 && !$game_over) {
    for my $i (0 .. $#players) {
        my $player = $players[$i];
        
        if ($chips[$i] == $total_chips_in_play) {
            #print "$player has won!\n\n";
            $total_chips_in_play = 0;
			$game_over = 1;
            last TURN;
        }
        
        $num_turns++;
        print "* Turn #$num_turns: $player\n\n";
        my $rolls = $chips[$i] > 3 ? 3 : $chips[$i];
        if ($rolls == 0) { print "$player has no chips and cannot roll.\n\n"; }
        else {
            $num_rolls++;
            for (1 .. $rolls) {
                my $roll = roll();
                if ($roll eq 'left' && $chips[$i] > 0) {
                    $chips[($i + 1) % @players]++;
                    $chips[$i]--;
                } elsif ($roll eq 'right' && $chips[$i] > 0) {
                    $chips[($i - 1) % @players]++;
                    $chips[$i]--;
                } elsif ($roll eq 'center' && $chips[$i] > 0) {
                    $center++;
                    $chips[$i]--;
                }

                print "$player rolled a $roll\n";
                $total_chips_in_play = 3 * @players - $center;
                print "Total chips left by $player: $chips[$i]\n";
                print "Total chips left in play: $total_chips_in_play\n\n";
				if ($total_chips_in_play == 1) { goto GAMEOVER; }
            }
        }
        print "---\n\n";
    }
}

GAMEOVER:
# Find the winner
my ($winner) = grep { $chips[$_] > 0 } 0 .. $#players;
if (defined $winner) {
	print "\n\n\n*** GAME OVER! ***\n\n";
    print "Total players: ".@players."\n";
    print "Total turns: $num_turns\n";
    print "Total rolls: $num_rolls\n";
    print "Total dice rolled: $num_rolled\n";
    print "\n*** Winner: $players[$winner] ***\n";
} else {
    print "No winner found. This should never happen.\n";
}

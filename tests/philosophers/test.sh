#!/bin/sh
#
# Tests for the dining philosophers example
#

if [ -z "$MVMAUDE" ]; then
	MVMAUDE=mvmaude
fi

## Rounds with one action per philosopher (this forces the order of actions too much,
## since the fork released by a philosopher will be necessarily taken by his neighbor)

# Estimated time when the first phisolopher eats
"$MVMAUDE" philosophers-parallel.maude 'initial(5)' someoneEats.multiquatex pparity --opaque parityRound -t uniform -- -d1 0.4
"$MVMAUDE" philosophers-parallel.maude 'initial(5)' someoneEats.multiquatex parity -t uniform -- -d1 0.4

# Estimated time when all philosophers have eaten
"$MVMAUDE" philosophers-parallel.maude 'initial(5)' allEaten.multiquatex parity -t uniform -- -d1 1.0

# Estimated time when philosopher number 1 eats
"$MVMAUDE" philosophers-parallel.maude 'initial(5)' eatsOne.multiquatex pparity --opaque parityRound -t uniform -- -d1 0.4
"$MVMAUDE" philosophers-parallel.maude 'initial(5)' eatsOne.multiquatex parity -t uniform -- -d1 1.0


## The same but forks are released before each round

# Estimated time when all philosophers have eaten
"$MVMAUDE" philosophers-parallel.maude 'initial(5)' allEaten.multiquatex pparityr --opaque parityRoundR -t uniform -- -d1 0.4

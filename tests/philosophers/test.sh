#!/bin/sh
#
# Tests for the dining philosophers example
#

if [ -z "$MVMAUDE" ]; then
	MVMAUDE=mvmaude
fi

# Estimated time when the first phisolopher eats
"$MVMAUDE" philosophers-parallel.maude 'initial(5)' someoneEats.multiquatex pparity --opaque parityRound -t uniform
"$MVMAUDE" philosophers-parallel.maude 'initial(5)' someoneEats.multiquatex parity -t uniform

# Estimated time when all philosophers have eaten
"$MVMAUDE" philosophers-parallel.maude 'initial(5)' allEaten.multiquatex pparity --opaque parityRound -t uniform
"$MVMAUDE" philosophers-parallel.maude 'initial(5)' allEaten.multiquatex parity -t uniform

# Estimated time when philosopher number 1 eats
"$MVMAUDE" philosophers-parallel.maude 'initial(5)' eatsOne.multiquatex pparity --opaque parityRound -t uniform -- -ds 0.5
"$MVMAUDE" philosophers-parallel.maude 'initial(5)' eatsOne.multiquatex parity -t uniform

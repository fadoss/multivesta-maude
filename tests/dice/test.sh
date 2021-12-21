#!/bin/sh
#
# Tests for the adapted PMaude's dice example
#

if [ -z "$MVMAUDE" ]; then
	MVMAUDE=mvmaude
fi

"$MVMAUDE" dice.maude 'initial(6)' dice-probExtract1.multiquatex -- -ds 0.05
"$MVMAUDE" dice.maude 'initial(6)' dice-probExtractEachFace.multiquatex

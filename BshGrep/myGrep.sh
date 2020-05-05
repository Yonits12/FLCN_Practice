#!/usr/bin/env bash

RED='\033[0;31m'
NC='\033[0m'
EXPR=$1
INPUT=$2

while IFS= read -r currline; do
    if [[ $currline =~ $EXPR ]]; then
        HALF1_COOL=${currline%%"$BASH_REMATCH"*}
        HALF2_COOL=${currline##*"$BASH_REMATCH"}

        echo -en $HALF1_COOL
        echo -en ${RED}${BASH_REMATCH}${NC}
        echo "$HALF2_COOL"

        # echo "HALF1_COOL:_____$HALF1_COOL"
        # echo -e "BASH_REMATCH:_____${RED}${BASH_REMATCH}${NC}"
        # echo "HALF2_COOL:_____$HALF2_COOL"
    fi
done < "${INPUT:-/dev/stdin}"

#!/usr/bin/env bash

RED='\033[0;31m'
NC='\033[0m'
IN="Yoni ;Anna Yossi; Avner"
sep='Anna'
EXPR=$1
INPUT=$2

while IFS= read -r currline; do
    if [[ $currline =~ $EXPR ]]; then
        END_MATCH=${currline/BASH_REMATCH[0]*/}
        BEGIN_LINE=${currline/currline*/}
        let REAL_LOC=${#END_MATCH}-${#BEGIN_LINE}-1
        HALF1=$(cut -c 1-${REAL_LOC} <<< $currline)
        let AFTER_LOC=${REAL_LOC}+${#BASH_REMATCH}+1
        HALF2=$(cut -c ${#END_MATCH}- <<< $currline)
        echo -e "$HALF1\c"
        echo -e "$RED${BASH_REMATCH[0]}$NC\c"
        echo -e "$HALF2"
    fi
done < "${INPUT:-/dev/stdin}"

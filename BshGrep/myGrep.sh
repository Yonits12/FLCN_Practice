#!/usr/bin/env bash

RED='\033[0;31m'
NC='\033[0m'

EXPR=$1
INPUT=$2

while IFS= read -r currline; do
    if [[ $currline =~ $EXPR ]]; then
        MATCH_IDX=${currline/$BASH_REMATCH*/}
        let REAL_LOC=${#MATCH_IDX}
        HALF1=$(cut -c 1-${REAL_LOC} <<< $currline)
        let AFTER_LOC=${REAL_LOC}+${#BASH_REMATCH}+1
        HALF2=$(cut -c ${AFTER_LOC}- <<< $currline)
        
        echo -e "$HALF1\c"
        echo -e "$RED${BASH_REMATCH[0]}$NC\c"
        echo -e "$HALF2"
        
    fi
done < "${INPUT:-/dev/stdin}"

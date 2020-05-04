#!/usr/bin/env bash

RED='\033[0;31m'
NC='\033[0m'
EXPR=$1
INPUT=$2

while IFS= read -r currline; do
    if [[ $currline =~ $EXPR ]]; then
        MATCH_IDX=${currline/$BASH_REMATCH*/}
        HALF1=""
        if [[ ${#MATCH_IDX} > 0 ]]; then
            HALF1=$(cut -c 1-${#MATCH_IDX} <<< $currline)
        fi
        let AFTER=${#MATCH_IDX}+${#BASH_REMATCH}+1
        HALF2=$(cut -c ${AFTER}- <<< $currline)
        echo -e "$HALF1\c"
        echo -e "$RED${BASH_REMATCH[0]}$NC\c"
        echo -e "$HALF2"
        
    fi
done < "${INPUT:-/dev/stdin}"

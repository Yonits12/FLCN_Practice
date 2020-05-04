#!/usr/bin/env bash

RED='\033[0;31m'
NC='\033[0m'
EXPR=$1
INPUT=$2

while IFS= read -r currline; do
    if [[ $currline =~ $EXPR ]]; then
        UP_TO_MATCH=${currline/${BASH_REMATCH}*/}
        MATCH_IDX=${#UP_TO_MATCH}
        HALF1=""
        if [[ $MATCH_IDX > 0 ]]; then
            echo "______ Not at the beginning ______"
            HALF1=$(cut -c 1-$MATCH_IDX <<< $currline)
        fi
        let AFTER=$MATCH_IDX+${#BASH_REMATCH}+1
        HALF2=$(cut -c ${AFTER}- <<< $currline)
        echo -en "$HALF1"
        echo -en "$RED${BASH_REMATCH}$NC"
        echo "$HALF2"
    fi
done < "${INPUT:-/dev/stdin}"

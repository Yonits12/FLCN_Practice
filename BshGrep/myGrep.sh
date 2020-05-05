#!/usr/bin/env bash

RED='\033[0;31m'
NC='\033[0m'
EXPR=$1
INPUT=$2

while IFS= read -r currline; do
    while [ -n "${currline}" ]; do
        if [[ ${currline} =~ ${EXPR} ]]; then
            HALF1_COOL=${currline%%"$BASH_REMATCH"*}
            HALF2_COOL=${currline#*"$BASH_REMATCH"}

            # double quotes essential for spaces keeping
            echo -en "${HALF1_COOL}"                      
            echo -en "${RED}${BASH_REMATCH}${NC}"
            currline="${HALF2_COOL}"
        else
            echo -n "${HALF2_COOL}"
            currline=${currline#${currline}*}
        fi
    done
    echo
done < "${INPUT:-/dev/stdin}"

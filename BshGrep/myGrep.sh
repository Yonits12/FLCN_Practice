#!/usr/bin/env bash

RED='\033[1;31m'
NO_COLOR='\033[0m'

if [[ $# -eq 0 ]]; then
    echo "Usage: ./myGrep PATTERN [FILE]"
    exit 2
fi

EXPR="$1"
INPUT="$2"

while IFS= read -r currline; do
    while [[ -n "${currline}" && "${currline}" =~ ${EXPR} ]]; do
        HALF1="${currline%%"$BASH_REMATCH"*}"
        HALF2="${currline#*"$BASH_REMATCH"}"

        # double quotes essential for spaces keeping
        echo -n "${HALF1}"                      
        echo -en "${RED}"
        echo -n "${BASH_REMATCH}"
        echo -en "${NO_COLOR}"
        currline="${HALF2}"
    done
    if [[ -v HALF2 ]]; then
        echo "${HALF2}"
        unset HALF2
    fi
done < "${INPUT:-/dev/stdin}"

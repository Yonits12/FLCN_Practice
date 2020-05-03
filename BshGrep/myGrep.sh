#!/usr/bin/env bash

INPUT=$2
EXPR=$1

while IFS= read -r currline; do
    if [[ $currline =~ $EXPR ]]; then
        echo "$currline"
    fi
done < "$INPUT"

#!/bin/bash
clear
echo "starting shell script

"

input="yoni1.txt"
# read currline <$input
while IFS= read -r currline
do
    if [[ $currline =~ ^2 ]]
    then
        echo "It's there!"
    else
        echo "Ooooops!" 
    fi

  echo "$currline"
done < "$input"



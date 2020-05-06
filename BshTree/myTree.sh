#!/usr/bin/env bash

#COLORS
DIR_FORMAT=$'\033[1;94m'
LINK=$'\033[1;36m'
EXE=$'\033[1;31m'
NO_FORMAT=$'\033[0m'

ZIP=$'\033[1;93m'
MEDIA=$'\033[1;95m'
SOCKET=$'\033[1;92m'
BRANCH_MID='├── '
BRANCH_END='└── '
DEPTH='│   '

# gets DIRECTORY PREFIX
dive_into(){
    local curr_dir="$1"
    local curr_prefix="${2}"
    local internal_prefix="${DEPTH}${curr_prefix}"
    
    IFS=""
    for file in "$curr_dir"/*; do
        local file_name=${file##*/}
        if [[ -d ${file} ]]; then
            echo "${curr_prefix}${BRANCH_MID}${DIR_FORMAT}${file_name}${NO_FORMAT}"
            dive_into "${file}" "${internal_prefix}"
        else
            color_by_type "${file}" "${file_name}" "${curr_prefix}${BRANCH_MID}"
        fi
    done
}

# gets PATH FILENAME PREFIX
color_by_type(){
    local path_to_file=$1
    local filename=$2
    local curr_prefix=$3
    if [[ -e ${path_to_file} ]]; then   # exist
        echo "${curr_prefix}${filename}"
    elif [[ -L ${path_to_file} ]]; then #link
        echo "${curr_prefix}${LINK}${filename}${NO_FORMAT}"
    elif [[ -f ${path_to_file} ]]; then # regular
        echo "${curr_prefix}${LINK}${filename}${NO_FORMAT}"
    elif [[ -S ${path_to_file} ]]; then
        echo "${curr_prefix}${SOCKET}${filename}${NO_FORMAT}"
    elif [[ -x ${path_to_file} ]]; then
        echo "${curr_prefix}${EXE}${filename}${NO_FORMAT}"
    else
        echo "____${path_to_file}____ does not exist"
    fi
}

dir=${1:-.}
echo "${DIR_FORMAT}${dir}${NO_FORMAT}"
dive_into $dir ""

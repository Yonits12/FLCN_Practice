#!/usr/bin/env bash

#COLORS
DIR_FORMAT=$'\033[1;94m'
LINK=$'\033[1;36m'
EXE=$'\033[1;92m'
NO_FORMAT=$'\033[0m'

ZIP=$'\033[1;31m'
MEDIA=$'\033[1;95m'
SOCKET=$'\033[1;93m'
BRANCH_MID='├── '
BRANCH_END='└── '
DEPTH='│   '

# gets DIRECTORY PREFIX
dive_into(){
    local curr_dir="${1}"
    local curr_prefix="${2}"
    local internal_prefix="${curr_prefix}${DEPTH}"
    local list_files="${curr_dir}"/*
    local files_array=($list_files)
    local files_left=${#files_array[@]}
    local branching="${BRANCH_MID}"
    for file in "$curr_dir"/*; do
        local file_name="$(basename "${file}")"
        if [[ $files_left -eq 1 ]]; then
            branching="${BRANCH_END}"
            internal_prefix="${internal_prefix/%"${DEPTH}"/'    '}"
        fi
        if [[ -L ${file} ]]; then #link
            local origin="$(readlink -f ${file})"
            if [[ "${origin}" == */*/* ]]; then
                origin="../$(basename `dirname $origin`)/$(basename $origin)"
            fi
            # TODO: Handle broken links here
            echo "${curr_prefix}${LINK}${file_name} -> ${origin}${NO_FORMAT}"
        elif [[ -d ${file} ]]; then
            echo "${curr_prefix}${branching}${DIR_FORMAT}${file_name}${NO_FORMAT}"
            dive_into "${file}" "${internal_prefix}"
        else
            color_by_type "${file}" "${curr_prefix}${branching}"
        fi
        ((--files_left))
    done
}

# gets PATH PREFIX
color_by_type(){
    local path_to_file=$1
    local filename="$(basename "${path_to_file}")"
    local curr_prefix=$2
    if [[ -e ${path_to_file} ]]; then   # exist
        echo "${curr_prefix}${filename}"
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
echo "${EXE}${dir}${NO_FORMAT}"
dive_into $dir ""

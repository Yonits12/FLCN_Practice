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
    IFS=
    local list_files="${curr_dir}"/*
    local files_array=(${list_files})
    local files_left=${#files_array[@]}
    local branching="${BRANCH_MID}"
    for file in "$curr_dir"/*; do
        local file_name="$(basename "${file}")"
        if [[ $files_left -eq 1 ]]; then
            branching="${BRANCH_END}"
            internal_prefix="${internal_prefix/%"${DEPTH}"/'    '}"
        fi
        if [[ -L ${file} ]]; then #link
            local origin="$(readlink ${file})"
            # TODO: Handle broken links here
            if [[ -d "$(readlink -f ${file})" ]]; then
                origin="${DIR_FORMAT}${origin}${NO_FORMAT}"
                ((++count_dirs))
            else
                ((++count_files))
            fi
            echo "${curr_prefix}${branching}${LINK}${file_name}${NO_FORMAT} -> ${origin}"
        elif [[ -d ${file} ]]; then
            echo "${curr_prefix}${branching}${DIR_FORMAT}${file_name}${NO_FORMAT}"
            dive_into "${file}" "${internal_prefix}"
            ((++count_dirs))
        else
            ((++count_files))
            color=$(color_by_type "${file}")
            echo "${curr_prefix}${branching}${color}${file_name}${NO_FORMAT}"
        fi
        ((--files_left))
    done
}

# gets PATH
color_by_type(){
    local path_to_file="$1"
    local filename="$(basename "${path_to_file}")"
    if [[ -d ${path_to_file} ]]; then
        echo ${DIR_FORMAT}
    elif [[ -S ${path_to_file} ]]; then
        echo ${SOCKET}
    elif [[ -x ${path_to_file} ]]; then
        echo ${EXE}
    elif [[ -f ${path_to_file} ]]; then
        echo ${NO_FORMAT}
    fi
}

init_dir=${1:-.}
let count_dirs=0
let count_files=0
echo "${DIR_FORMAT}${init_dir}${NO_FORMAT}"
ANCESTOR_DIRNAME="$(basename `realpath ${init_dir}`)"
dive_into "$init_dir" ""
echo "${count_dirs} directories, ${count_files} files"
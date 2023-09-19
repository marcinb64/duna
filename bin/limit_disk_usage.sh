#!/bin/bash

get_size() {
    du -s $1 | awk '{print $1}'
}

remove_oldest_in() {
    oldest=$(ls -1tr "$1" | head -1)
    rm -fr "$1/$oldest"
}

dir=$1
MAX_SIZE=$((1 * 1000 * 1000)) # in kB

while [[ $(get_size "$dir") -gt $MAX_SIZE ]]; do
    remove_oldest_in "$dir"
done

#!/bin/bash

if [ $# -eq 0 ]; then
    echo "Directory name required"
    exit 1
fi

#main directory name
DIRNAME=$1

for d in $DIRNAME/*/ ; do
    cd "$d"
    echo "Processsing ${d}"
    mogrify -format jpg *.png 
    rm *.png
    cd -
done

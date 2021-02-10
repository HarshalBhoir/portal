#!/bin/bash

dest_path=$1
days=$2

# Remove backup file that is older than n days
find $dest_path -type f -name '*.zip' -mtime +$days -exec rm {} \;
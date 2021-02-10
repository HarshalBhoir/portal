#!/bin/bash

set -e

timestamp(){
   echo -n `date --date="8 hours" "+%Y-%m-%d %H:%M:%S,"`
}

#variable from python
current_date=`date +"%Y-%m-%d"`
dest_ip=$1
dest_port=$2
dest_login=$3
source_path=$4
dest_path=$5
db_name=$6
url=$7
db_pass=$8
days=$9
remove_script=${10}

if [ ! -d $source_path/$db_name ]; then
  mkdir $source_path/$db_name
fi
# Get the zip file from client instance
curl -X POST -F master_pwd=$db_pass -F name=$db_name -F backup_format=zip -o $source_path/$db_name/$current_date-$db_name.zip $url/web/database/backup

# Check validity of zip file
if unzip -t $source_path/$db_name/$current_date-$db_name.zip >/dev/null 2>&1
then
  valid=true
else
  mv $source_path/$db_name/$current_date-$db_name.zip $source_path/$db_name/$current_date-$db_name-bad.zip
  valid=false
fi

# Delete backup file that is older than n days on source server
find $source_path -type f -name '*.zip' -mtime +$days -exec rm {} \;

# Delete backup file that is older than n days on destination server
ssh -p $dest_port -l $dest_login $dest_ip "bash -s" < $remove_script $dest_path $days

# Copy the zip file from the web portal server to Destination Server with Rsync method
if $valid ; then
  timestamp; echo " Start to copy $dest_path to $dest_ip."
  timeout 1800 rsync -chavzP -e "ssh -p $dest_port" $source_path/$db_name/$current_date-$db_name.zip $dest_login@$dest_ip:$dest_path/$db_name/
  timestamp; echo " The file is copied."
fi


#!/bin/bash

set -e

timestamp(){
   echo -n `date --date="8 hours" "+%Y-%m-%d %H:%M:%S,"`
}

#variable from python
current_date=`date +"%Y-%m-%d"`
pgo_namespace=$1
service_name=$2
cust_db=$3
template_db=$4
free_instance_user=$5
namespace=$6


rancher kubectl exec -it -n $pgo_namespace svc/$service_name -- psql <<EOF
CREATE DATABASE "$cust_db" TEMPLATE "$template_db";
ALTER DATABASE "$cust_db" OWNER TO "$free_instance_user";
EOF

timestamp; echo "Script: Done create database-----------------"

rancher kubectl exec -it -n $namespace svc/service-$template_db -- bash <<EOF
cd /var/lib/odoo/filestore/
cp -r $template_db $cust_db
EOF

timestamp; echo "Script: Done copy filestore-------------------"
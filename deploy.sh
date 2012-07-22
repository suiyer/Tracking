#!/bin/bash
#
# deploy.sh
#
# Notes:
#   This script runs as root
#   This script runs on an EC2 instance
#
#

set -o errexit

. /opt/bazaarvoice/bvlabs/Utilities/deploy/bvlabs-functions

VERSION="$1"
ENVIRONMENT="$2"
SOURCE_DIR=`pwd`
DEPLOYMENT_DIR=/var/www/tornado
# gcc/python-devel is needed to compile simplejson native speedups
PACKAGES=( nginx gcc python-devel )

deploy_app $DEPLOYMENT_DIR $VERSION $SOURCE_DIR
django_deployment_setup $DEPLOYMENT_DIR $VERSION 'deployment/requirements.txt'

# setup the app environment
rm -rf $DEPLOYMENT_DIR/build
as_deployer "mkdir -p $DEPLOYMENT_DIR/logs"

install_packages "${PACKAGES[@]}"

# nginx configuration
copy_file_if_changed "$SOURCE_DIR/deployment/nginx.conf" "/etc/nginx/nginx.conf"
enable_service nginx
restart_service nginx

# supervisor configuration
pip install supervisor --upgrade
mkdir -p /var/log/supervisord/
copy_file_if_changed "$SOURCE_DIR/deployment/supervisord.conf" "/etc/supervisord.conf"
copy_file_if_changed "$SOURCE_DIR/deployment/supervisord" "/etc/init.d/supervisord"
stop_service supervisord
enable_service supervisord
supervisorctl update
supervisorctl restart all


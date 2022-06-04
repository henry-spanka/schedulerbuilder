#!/bin/sh

set -e

# https://stackoverflow.com/questions/8518750/to-show-only-file-name-without-the-entire-directory-path
BUILD_FILE=`ls -t dist/schedulerbuilder-*.whl | head -1 | xargs -n 1 basename` # get latest wheel file

NODE="$1"

if [ -z "$NODE" ]
then
    echo "Hostname der Controller Nicht gesetzt.\n./install.sh HOSTNAME"
    exit 1
fi

python3 setup.py bdist_wheel

scp dist/$BUILD_FILE root@$NODE:/root/
ssh root@$NODE "docker cp $BUILD_FILE nova_scheduler:$BUILD_FILE"
ssh root@$NODE "docker exec nova_scheduler pip install --no-deps --force-reinstall -U $BUILD_FILE"
ssh root@$NODE 'docker restart nova_scheduler'
ssh root@$NODE "docker cp $BUILD_FILE nova_api:$BUILD_FILE"
ssh root@$NODE "docker exec nova_api pip install --no-deps --force-reinstall -U $BUILD_FILE"
ssh root@$NODE 'docker restart nova_api'

echo "schedulerbuilder erfolgreich auf dem Controller installiert."

#!/bin/sh

set -e

# https://stackoverflow.com/questions/8518750/to-show-only-file-name-without-the-entire-directory-path
BUILD_FILE=`ls -t dist/schedulerbuilder-*.whl | head -1 | xargs -n 1 basename` # get latest wheel file

if [ -z "$1" ]
then
    echo "Hostname der Controller Nicht gesetzt.\n./install.sh root@HOSTNAME [root@HOSTNAME2 root@HOSTNAME3 ...]"
    exit 1
fi

tox -e build

for NODE in "$@"
do
    echo "Installing on $NODE"
    scp dist/$BUILD_FILE $NODE:/root/
    ssh $NODE "docker cp $BUILD_FILE nova_scheduler:$BUILD_FILE"
    ssh $NODE "docker exec nova_scheduler pip install --no-deps --force-reinstall -U $BUILD_FILE"
    ssh $NODE 'docker restart nova_scheduler'
    ssh $NODE "docker cp $BUILD_FILE nova_api:$BUILD_FILE"
    ssh $NODE "docker exec nova_api pip install --no-deps --force-reinstall -U $BUILD_FILE"
    ssh $NODE 'docker restart nova_api'
done

echo "schedulerbuilder erfolgreich auf dem Controller installiert."

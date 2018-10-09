#!/bin/sh

#install remotedev
/usr/local/bin/pip install --trusted-host pypi.org "remotedev==0.0.15"
if [ $? -ne 0 ]; then
    exit 1
fi

#set cleepos profile as daemon default profile
/bin/sed -i -E "s/^DAEMON_PROFILE_NAME=.*$/DAEMON_PROFILE_NAME=cleepos/g" /etc/default/remotedev.conf
if [ $? -ne 0 ]; then
    exit 1
fi


#!/bin/sh

#install remotedev
/usr/local/bin/pip install --trusted-host pypi.org "remotedev==0.0.14"

#set cleepos profile as daemon default profile
/bin/sed -i -E "s/^DAEMON_PROFILE_NAME=.*$/DAEMON_PROFILE_NAME=cleepos/g" /etc/default/remotedev.conf


#!/bin/sh

#make sure remotedev is uninstalled
/usr/local/bin/pip2 uninstall --yes remotedev

#install cleep-cli
/usr/local/bin/pip2 install --trusted-host pypi.org "cleepcli>=1.4.4" "mock>=3.0.5"
if [ $? -ne 0 ]; then
    exit 1
fi

#clone cleep core repo
/usr/local/bin/cleep-cli coreget; /bin/true


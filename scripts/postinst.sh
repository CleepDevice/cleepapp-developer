#!/bin/sh

# make sure remotedev is uninstalled
python3 -m pip uninstall --yes remotedev

# install cleep-cli
python3 -m pip install --trusted-host pypi.org "cleepcli==1.43.9" "mock==5.2.0"
if [ $? -ne 0 ]; then
    exit 1
fi

# clone cleep core repo
/usr/local/bin/cleep-cli coreget; /bin/true


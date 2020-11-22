#!/bin/bash

# This is setting up ortho2 after a fresh installation
# Reason for not adding this to %post rpm section in
# orthos2.spec is the complex dependencies to django and
# other packages that then show up.

# This one can and should be used at CI integration as well
# at some point of time

cd /usr/lib/orthos2
sudo -u orthos ./manage.py migrate

sudo -u orthos ./manage.py collectstatic --noinput
./create_super_user.sh
if [ $1 -eq 1 ] ; then
    # New installation - upgrade is 2:
    # Data can only be filled up once.
    sudo -u orthos ./install_all_fixtures.sh
fi

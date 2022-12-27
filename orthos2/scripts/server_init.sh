#!/bin/sh

BASHRC='/root/.bashrc'
NGINX=/etc/nginx/nginx.conf

if ! grep -q '### ORTHOS BASHRC EXTENSIONS ###' $BASHRC;then
    echo "Extending .bashrc"
        cat <<'EOF' >> ${BASHRC}
### ORTHOS BASHRC EXTENSIONS ###
FQDN=$(python3 -c 'import socket; print(socket.getfqdn())')
alias manage="sudo -i -u orthos /usr/lib/orthos2/manage.py"
alias goto_orthos='pushd /usr/lib/python3.6/site-packages/orthos2'
alias tail_log="tail -f /var/log/orthos/default.log"
### ORTHOS BASHRC EXTENSIONS ###
EOF
fi

if grep -q 'user  nginx;' ${NGINX};then
    echo "Replace nginx user with orthos in ${NGINX}"
    sed 's/user  nginx;/user  orthos orthos;/' -i ${NGINX}
if 

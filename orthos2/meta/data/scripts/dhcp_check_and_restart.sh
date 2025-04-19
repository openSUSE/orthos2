#!/bin/bash

######
# Check and restart DHCP server
#
# This script checks the DHCP syntax for all `$1/*.conf.new` files, copies them to `$1/*.conf` and
# restarts the DHCP server afterwards. The IP version (DHCPv4, DHCPv6) is set by $2.
#
# Contact: <jloeser@suse.de>
######

scriptname=$(basename $0)
dhcpdv4="/usr/sbin/dhcpd"
dhcpdv6="/usr/sbin/dhcpd6"
logfile_path="/var/log/orthos"
logfile="${logfile_path}/dhcp.log"

function log() {
    if [ ! -d "${logfile_path}" ]; then
        mkdir -p "${logfile_path}"
    fi
    echo "$0: $1" >> "$logfile"
}

function error() {
    log "ERROR: $1"
    exit 1
}

[ $# -ne 2 ] && error "Illegal amount of parameters"

path="$1"
version=$2

for dhcpfile in ${path}/*.conf.orthos-generated; do
    [ -e "${dhcpfile}" ] || continue

    log "$(date) starting DHCPv${version} check for file: ${dhcpfile}"

    if [ $version -eq 4 ]; then
        `${dhcpdv4} -t -cf "${dhcpfile}" > ${logfile}`
    else
        `${dhcpdv6} -t -cf "${dhcpfile}" > ${logfile}`
    fi

    if [ $? -ne 0 ];then
        error "DHCPv${version} config syntax broken for file: ${dhcpfile}"
        exit 1
    fi
done

for dhcpfile in ${path}/*.conf.orthos-generated; do
    [ -e "${dhcpfile}" ] || continue

    dhcpfile2=${dhcpfile%.*}
    cp "${dhcpfile}" "${dhcpfile2}"
    rm "${dhcpfile}"
done

if [ $version -eq 4 ]; then

    if [ -x /usr/bin/systemctl ];then
        systemctl restart dhcpd
    else
        /etc/init.d/dhcpd restart
    fi

    [ ! $? -eq 0 ] && error "Starting of DHCPv${version} server failed!"

else

    if [ -x /usr/bin/systemctl ];then
        systemctl restart dhcpd6
    else
        /etc/init.d/dhcpd6 restart
    fi

    [ ! $? -eq 0 ] && error "Starting of DHCPv${version} server failed!"
fi

log "DHCPv${version} server successfully restarted!"
exit 0

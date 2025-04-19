#!/bin/bash

# Copyright by Vanessa Wallfahrer <vwallfahrer@suse.de>, SUSE GmBH

#Check if default route is already br0
defaultroute=$(ip route show |grep "^default" |awk '{print $5}')
dir="/sys/class/net/$defaultroute/bridge"
if [ -d "$dir" ]; then
    exit 0
fi

#Create br0 file
echo "BOOTPROTO='dhcp'
BRIDGE='yes'
BRIDGE_FORWARDDELAY='0'
BRIDGE_PORTS='$defaultroute'
BRIDGE_STP='off'
STARTMODE='auto'" > /etc/sysconfig/network/ifcfg-br0

#Change BOOTPROTO from 'dhcp' to 'none' in eth file
ethfile="/etc/sysconfig/network/ifcfg-$defaultroute"
[ ! -w $ethfile ] && exit 1
sed -i "s/BOOTPROTO='dhcp'/BOOTPROTO='none'/" $ethfile
wicked ifreload all

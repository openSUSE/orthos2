#!/bin/bash
#
# Gets the firmware version.
#

DMIDECODE=/usr/sbin/dmidecode

function firmware_default()
{
    local in_bios=0
    local oldifs="$IFS"
    IFS="
"
    $DMIDECODE | while read line ; do
        if (( $in_bios )) ; then
            if echo "$line" | grep -q '^[[:space:]]\+Version: ' ; then
                version=$(echo "$line" | sed -e 's/^\s\+Version: \(.*\)/\1/g')
                echo -n "$version "
            elif echo "$line" | grep -q '^[[:space:]]\+Release Date: ' ; then
                release=$(echo "$line" | sed -e 's/^\s\+Release Date: \(.*\)/\1/g')
                echo "$release"
            elif echo "$line" | grep -q -v '^[[:space:]]' ; then
                break
            fi
        else
            if echo "$line" | grep -q "^BIOS Information" ; then
                in_bios=1
            fi
        fi
    done
    IFS="$oldifs"
}

function firmware_ppc()
{
    if [ -f /proc/device-tree/openprom/model ] ; then
        strings /proc/device-tree/openprom/model
    fi
}

case $(uname -i) in
    ppc|ppc64)
        firmware_ppc
        ;;
    *)
        firmware_default
        ;;
esac

# vim: set sw=4 ts=4 et: :collapseFolds=1:

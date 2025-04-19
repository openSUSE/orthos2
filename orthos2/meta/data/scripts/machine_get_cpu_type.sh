#!/bin/bash
#
# Gets the CPU type.
#

STEPPING_URL=ftp://ftphost.network.tld/orthos/stepping

ADD_X86_FLAGS=true

function cpu_type_x86()
{
    local MODELNAME=$(grep '^model name' /proc/cpuinfo  | head -1 |
        sed -e 's/.*: //g' | sed -e 's/ \+/ /g')

    local FLAGS=$(grep '^flags' /proc/cpuinfo  | head -1 |
        sed -e 's/.*: //g' | sed -e 's/ \+/ /g')

    if wget -q $STEPPING_URL &>/dev/null ; then
        chmod 755 ./stepping
        NAME=$(./stepping 1| head -1 | cut -c 4-)
        echo -n "$MODELNAME"
    else
        echo -n "$MODELNAME"
    fi
    # cpu_flags get scanned in a seperat script now    
    # if $ADD_X86_FLAGS;then
	# echo " : $FLAGS"
    # else
	echo
    # fi

    rm -f ./stepping
}

function cpu_type_ia64()
{
    local VENDOR=$(grep ^vendor /proc/cpuinfo  | head -1 | sed -e 's/.*: //g')
    local FAMILY=$(grep ^family /proc/cpuinfo  | head -1 | sed -e 's/.*: //g')

    echo "$FAMILY: $VENDOR"
}

function cpu_type_ppc()
{
    local CPU=$(grep ^cpu /proc/cpuinfo | head -1 | sed -e 's/.*: //g')
    
    echo "$CPU"
}

function cpu_type_other()
{
    echo "Unknown"
}


case $(uname -i) in
    ia64)                   cpu_type_ia64   ;;
    i386|x86_64)            cpu_type_x86    ;;
    ppc|ppc64|ppc64le)      cpu_type_ppc    ;;
    *)                      cpu_type_other  ;;
esac

# vim: set sw=4 ts=4 et: :collapseFolds=1:

#!/bin/sh
#
# Gets the CPU number.
#

SOCKETS=0
CORES=0
THREADS=0

function cpu_number_default()
{
    THREADS=$(grep -c ^processor /proc/cpuinfo)
    SOCKETS=$(grep ^physical /proc/cpuinfo | cut -d : -f 2 | sort | uniq | wc -l)
    local cores=$(grep '^cpu cores' /proc/cpuinfo | head -1 | cut -d : -f 2)
    if [ -z "$cores" ] || [ "$cores" -eq 0 ] ; then
        CORES=$THREADS
    else
        CORES=$[ $cores * $SOCKETS ]
    fi

    if [ -z "$SOCKETS" ] || [ "$SOCKETS" -eq 0 ] ; then
        SOCKETS=$THREADS
    fi
}

function cpu_number_ia64()
{
    THREADS=$(grep -c ^processor /proc/cpuinfo)
    SOCKETS=$(grep ^physical /proc/cpuinfo | cut -d : -f 2 | sort | uniq | wc -l)
    local cores=$(grep '^cpu regs' /proc/cpuinfo | head -1 | cut -d : -f 2)
    if [ -z "$cores" ] || [ "$cores" -eq 0 ] ; then
        CORES=$THREADS
    else
        CORES=$[ $cores * $SOCKETS ]
    fi

    if [ -z "$SOCKETS" ] || [ "$SOCKETS" -eq 0 ] ; then
        SOCKETS=$THREADS
    fi
}

function cpu_number_ppc()
{
    THREADS=$(grep -c ^processor /proc/cpuinfo)
    SOCKETS=$THREADS
    CORES=$THREADS
}


case $(uname -i) in
    ia|ia64)
        cpu_number_ia64
        ;;
    ppc|ppc64)
        cpu_number_ppc
        ;;
    *)
        cpu_number_default
        ;;
esac

echo "SOCKETS=${SOCKETS}"
echo "CORES=${CORES}"
echo "THREADS=${THREADS}"

# vim: set sw=4 ts=4 et: :collapseFolds=1:

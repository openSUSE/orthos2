#!/bin/bash
#
# Gets the CPU speed
#

function cpu_speed_default()
{
    local mhz=$(grep -m 1 '^cpu MHz' /proc/cpuinfo | sed -e 's/cpu MHz.*: //g')
    echo "$mhz * 1000000" | bc -l | sed -e 's/\..*//g'
}

function cpu_speed_ppc()
{
    local mhz=$(grep -m 1 '^clock' /proc/cpuinfo | sed -e 's/clock.*: //g' -e 's/MHz//g')
    echo "$mhz * 1000000" | bc -l | sed -e 's/\..*//g'
}



case $(uname -i) in
    ppc|ppc64)
        cpu_speed_ppc
        ;;
    *)
        cpu_speed_default
        ;;
esac

# vim: set sw=4 ts=4 et: :collapseFolds=1:

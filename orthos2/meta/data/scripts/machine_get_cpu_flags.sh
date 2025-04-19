#!/bin/bash
#
# Gets the CPU flags.
#

function cpu_flags_x86()
{
    local FLAGS=$(grep '^flags' /proc/cpuinfo  | head -1 |
        sed -e 's/.*: //g' | sed -e 's/ \+/ /g')
	echo "$FLAGS"
}

function cpu_flags_other()
{
    echo "Unknown"
}


case $(uname -i) in
    i386|x86_64)    cpu_flags_x86    ;;
    *)              cpu_flags_other  ;;
esac

# vim: set sw=4 ts=4 et: :collapseFolds=1:

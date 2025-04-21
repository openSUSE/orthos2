#!/bin/sh
#
# This scripts syncs the motd of the current installation with
# all motds.
#

if [ ! -f "/etc/motd.orthos" ] ; then
    exit 1
fi

function replace_motd()
{
    local motd=$1

    repl=0
    in_orthos=0
    while read line ; do
        if [ "$in_orthos" -eq 0 ] ; then
            if echo "$line" | grep '^-\+ Orthos{ --$' &>/dev/null ; then
                cat /etc/motd.orthos >> ${motd}.new
                in_orthos=1
                repl=1
            else
                echo "$line" >> ${motd}.new
            fi
        else
            if echo "$line" | grep '^-\+ Orthos} --$' &>/dev/null ; then
                in_orthos=0
            fi
        fi
    done < ${motd}

    if [ "$repl" -eq 0 ] ; then
        cat /etc/motd.orthos >> ${motd}.new
    fi

    mv ${motd}.new ${motd}
}


replace_motd /etc/motd

DISKS=$(cat /proc/partitions | awk '{print $4}' | \
    grep -v name | grep -v '^$' | grep -v loop | grep '[0-9]')
ROOT=$(mount | grep ' / ' | cut -d ' ' -f 1)
for partition in ${DISKS} ; do
    partition=/dev/${partition}
    # Only try filesystems which had been default for the
    # corresponding partitions
    if [ ! -b ${partition} ] || [ ${partition} = ${ROOT} ] ; then
	continue;
    fi
    FS=""
    case "${partition}" in
	*5)
	    FS="ext3"
	    ;;
	*6)
	    FS="ext3"
	    ;;
	*7)
	    FS="ext4 ext3 btrfs"
	    ;;
	*8)
	    FS="ext3"
	    ;;
	*)
	    continue
	    ;;
    esac
    for fs in $FS;do
	mount -t "$fs" ${partition} /mnt &> /dev/null
	if [ $? -ne 0 ];then
	    continue;
	fi
	if [ -f /etc/SuSE-release ] && [ -f /mnt/etc/motd ] ; then
            replace_motd /mnt/etc/motd
	fi
	umount /mnt &> /dev/null
    done
done

# vim: set sw=4 ts=4 et: :collapseFolds=1:

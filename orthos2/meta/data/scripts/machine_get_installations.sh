#!/bin/bash
#
#
# Collects installation information.
#

function get_milestone()                                                   # {{{
{
    local FILE=$1
    local milestone=
    local issue=

    issue=$(grep "Build\|Alpha\|Beta\|RC" ${FILE})

    if [ -n "${issue}" ] ; then
	milestone=$(echo ${issue} | sed -e 's/^.*\(Build[ ]*\?[0-9]\+\| Alpha[ ]*\?[0-9]\+\|Beta[ ]*\?[0-9]\+\|RC[ ]*\?[0-9]\+\).*$/\1/gi')
    fi

    echo $milestone
}                                                                          # }}}

function pretty_suse()                                                     # {{{
{
    local MP="$1"
    local FILE="$MP/etc/SuSE-release"
    local base=

    [ -r "${FILE}" ] || return
    base=$(head -1 < ${FILE} | sed -e 's/(.*)//g' -e 's/SP[0-9]//g')
    if echo ${base} | grep Enterprise &>/dev/null ; then
        local sp=$(grep PATCHLEVEL ${FILE} |cut -d '=' -f 2)
        sp=$(echo ${sp} | sed -e 's/ //g')
        if [ "${sp}" == "0" ] ; then
            base="${base} GA"
        elif [ -n "${sp}" ] ; then
            base="${base} SP${sp}"
        fi
    fi

    base=$(echo "${base}" | sed -e 's/SUSE L[Ii][nN][uU][xX] Enterprise Server/SLES/g')

    echo $base
}                                                                          # }}}

function pretty_os()                                                       # {{{
{
    local MP="$1"
    local FILE="$MP/etc/os-release"
    local dist=
    local vers=

    if [ -r "${FILE}" ]; then
        dist=$(sed -ne 's/^NAME="\([^"]*\)".*$/\1/p' "${FILE}")
        vers=$(sed -ne 's/^VERSION_ID="\([^"]*\)".*$/\1/p' "${FILE}")
        case "$dist" in
        (SLE*)
          case "$vers" in
          (*.*)    vers=$(echo "$vers" | sed -e 's/\./ SP/') ;;
          (*-SP*)  vers=$(echo "$vers" | sed -e 's/-/ /') ;;
          esac
          ;;
        esac
    fi

    if [ -z "$dist" ]; then
        dist=$(pretty_suse "$MP")
    else
        dist="$dist $vers"
    fi
    [ -n "$dist" ] || dist="N/N"

    echo "$dist"
}                                                                          # }}}

function chroot_kernel()                                                   # {{{
{
    local chroot=$1

    rpm -r ${chroot} -qa kernel-* \
        | grep -v -- -source- \
        | grep -v -- -update-tool \
        | grep -v -- -sym- \
        | grep -v -- -kdump- \
        | grep -v -- -debuginfo- \
        | grep -v -- -debugsource- \
        | head -1 \
        | sed -e 's/kernel-//g' \
        | sed -e 's/\([a-z]\+\)-\(.*\)/\2-\1/'
}                                                                          # }}}

function get_installation()                                                # {{{
{
    local part=$1
    local mp=$2

    if [ -z "$mp" ] ; then
        echo >&2 "mounting $part failed, and its currently not mounted"
        return
    fi

    if [ -f $mp/etc/SuSE-release ] ; then
        echo ----
        if grep i[365]86 $mp/etc/SuSE-release ; then
            echo ARCH=i386
        else
            echo ARCH=$GLOBAL_ARCH
        fi
        echo KERNEL=$(chroot_kernel $mp)
        DIST=$(pretty_os $mp)
        MILESTONE=$(get_milestone $mp/etc/issue)
        echo DIST=${DIST} ${MILESTONE}
        echo PART=${part}
        echo RUNNING=0
    fi
}                                                                          # }}}
GLOBAL_ARCH=$(uname -i)

DISKS=$(cat /proc/partitions |grep -v loop | awk '{print $4}' | \
    grep -v name | grep -v '^$' | grep '[0-9]')
ROOT=$(mount | grep ' / ' | cut -d ' ' -f 1)

#
# running installation
echo ----
echo ARCH=$GLOBAL_ARCH
echo KERNEL="$(uname -r)"
DIST=$(pretty_os "")
MILESTONE=$(get_milestone /etc/issue)
echo DIST=${DIST} ${MILESTONE}
echo RUNNING=1
echo PART=${ROOT}

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
            get_installation $partition /mnt
	fi
	umount /mnt &> /dev/null
    done
done

# vim: set sw=4 ts=4 et: :collapseFolds=1:

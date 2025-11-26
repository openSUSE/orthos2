#!/bin/bash
#
#
# Collects installation information.
#
etc_issue='/etc/issue'
etc_os_release='/etc/os-release'
etc_suse_release='/etc/SuSE-release'
dist_debug=

while test $# -gt 0
do
    case "$1" in
    --issue) etc_issue=$2 ; shift ;;
    --os-release) etc_os_release=$2 ; shift ;;
    --suse-release) etc_suse_release=$2 ; shift ;;
    --dist-debug) dist_debug='dist_debug' ;;
    esac
    shift
done

function get_milestone()                                                   # {{{
{
    local FILE=$1

    test -f "${FILE}" || return
    sed -ne 's/^.*[[:blank:]]\(\(Build\|Snapshot\|Alpha\|Beta\|RC\)[- ]*\?[-0-9]\+\|PublicRC\).*/\1/p' "${FILE}"
}                                                                          # }}}

function pretty_suse()                                                     # {{{
{
    local FILE=${etc_suse_release}
    local base=

    [ -r "${FILE}" ] || return
    base=$(sed -e 's/(.*)//g;s/SP[0-9]//g;q' "${FILE}")
    if echo ${base} | grep Enterprise &>/dev/null ; then
        local sp=$(grep PATCHLEVEL ${FILE} |cut -d '=' -f 2)
        sp=$(echo ${sp} | sed -e 's/ //g')
        if [ "${sp}" == "0" ] ; then
            base="${base} GA"
        elif [ -n "${sp}" ] ; then
            base="${base} SP${sp}"
        fi
    fi

    base=$(echo "${base}" | sed -e 's/SUSE L[Ii][nN][uU][xX] Enterprise Server/SLES/g;s/SUSE Linux Enterprise Desktop/SLED/')

    echo $base
}                                                                          # }}}

function pretty_os()                                                       # {{{
{
    local FILE=$1
    local dist=
    local vers=

    if [ -r "${FILE}" ]; then
        dist=$(sed -ne '/^SUSE_SUPPORT_PRODUCT=/{s|[^=]\+="\?\([^"]*\)"\?.*$|\1|;p}' "${FILE}")
        if test -n "${dist}"
        then
            case "${dist}" in
            "SUSE Linux Enterprise Server") dist='SLES' ;;
            "SUSE Linux Enterprise Server for SAP applications") dist='SLES_SAP' ;;
            "SUSE Linux Micro") dist='SL-Micro' ;;
            esac
            vers=$(sed -ne '/^SUSE_SUPPORT_PRODUCT_VERSION=/{s|[^=]\+="\?\([^"]*\)"\?.*$|\1|p}' "${FILE}")
        else
            dist=$(sed -ne 's/^NAME="\?\([^"]*\)"\?.*$/\1/p' "${FILE}")
            vers=$(sed -ne 's/^VERSION_ID="\?\([^"]*\)"\?.*$/\1/p' "${FILE}")
            case "$dist" in
            "SLE Micro")
              ;;
            "SL-Micro")
              ;;
            (SLE*)
              case "$vers" in
              (16.*)   ;;
              (*.*)    vers=$(echo "$vers" | sed -e 's/\./ SP/') ;;
              (*-SP*)  vers=$(echo "$vers" | sed -e 's/-/ /') ;;
              esac
              ;;
            esac
        fi
    fi

    if [ -z "$dist" ]; then
        dist=$(pretty_suse)
    else
        dist="$dist $vers"
    fi
    [ -n "$dist" ] || dist="N/N"

    echo "$dist"
}                                                                          # }}}

DIST=$(pretty_os "${etc_os_release}")
MILESTONE=$(get_milestone "${etc_issue}")
if test -n "${dist_debug}"
then
    echo DIST=${DIST} ${MILESTONE}
    exit 0
fi
#
# running installation
echo ----
echo ARCH=$(uname -i)
echo KERNEL="$(uname -r)"
echo DIST=${DIST} ${MILESTONE}
echo RUNNING=1
echo PART=$(mount | sed -ne '/ \/ /{s|[[:blank:]].*$||p;q}')

# vim: set sw=4 ts=4 et: :collapseFolds=1:

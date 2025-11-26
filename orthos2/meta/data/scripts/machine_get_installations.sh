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
    local FILE="/etc/SuSE-release"
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
    local FILE="/etc/os-release"
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
        dist=$(pretty_suse)
    else
        dist="$dist $vers"
    fi
    [ -n "$dist" ] || dist="N/N"

    echo "$dist"
}                                                                          # }}}

#
# running installation
echo ----
echo ARCH=$(uname -i)
echo KERNEL="$(uname -r)"
DIST=$(pretty_os)
MILESTONE=$(get_milestone /etc/issue)
echo DIST=${DIST} ${MILESTONE}
echo RUNNING=1
echo PART=$(mount | sed -ne '/ \/ /{s|[[:blank:]].*$||p;q}')

# vim: set sw=4 ts=4 et: :collapseFolds=1:

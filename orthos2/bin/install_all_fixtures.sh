#!/bin/bash
#
# Author Jan Löser <jloeser@suse.de>
# Published under the GNU Public Licence 2
declare -A FIXTURES
EXEC="/usr/lib/orthos2/manage.py"
LOAD="ALL"

FIXTURES["DATA"]="/usr/share/orthos2/fixtures/data/*.json"
FIXTURES["TASKMANAGER"]="/usr/share/orthos2/fixtures/taskmanager/*.json"
FIXTURES["ALL"]="${FIXTURES[@]}"

function help {
    echo "$(basename $0) [ FIXTURE ]"
    echo
    echo "Available fixtures (default ALL):"
    for fix in ${!FIXTURES[@]};do
	echo $fix
    done
}
	
function error_out {
    echo "$1"
    echo
    help
} >/dev/stderr

if [ $# -eq 1 ];then
    LOAD=${1^^}
    if ! [ -v FIXTURES[$LOAD] ];then
	error_out "$1: fixture does not exist"
    fi
fi

set -x
${EXEC} loaddata ${FIXTURES[$LOAD]}

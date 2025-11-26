#!/bin/bash
set -e
script='orthos2/meta/data/scripts/machine_get_installations.sh'
data_dir='tests/machine_get_installations/data'
out='testoutput.txt'
test -d "$1" && data_dir=$1
declare -i failures=0
read exe < <(readlink -f "${script}")
pushd "${data_dir}" > /dev/null
for dist in *
do
	test -d "${dist}" || continue
	if ! test -f "${dist}/DIST.txt"
	then
		echo >&2 "INFO: DIST.txt missing in ${dist}"
		continue
	fi
	rm -f "${out}"	
	pushd "${dist}" > /dev/null
	if test -f 'usr/lib/os-release' && test -f 'usr/lib/issue.d/10-SUSE'
	then
		"${exe}" --dist-debug --os-release 'usr/lib/os-release' --issue 'usr/lib/issue.d/10-SUSE' --suse-release '/dev/null' > "../${out}"
	elif test -f 'usr/lib/os-release' && test -f 'usr/lib/issue.d/10-openSUSE.conf'
	then
		"${exe}" --dist-debug --os-release 'usr/lib/os-release' --issue 'usr/lib/issue.d/10-openSUSE.conf' --suse-release '/dev/null' > "../${out}"
	elif test -f 'usr/lib/os-release' && test -f 'etc/issue'
	then
		"${exe}" --dist-debug --os-release 'usr/lib/os-release' --issue 'etc/issue' --suse-release '/dev/null' > "../${out}"
	elif test -f 'etc/os-release' && test -f 'usr/lib/issue.d/10-SUSE'
	then
		"${exe}" --dist-debug --os-release 'etc/os-release' --issue 'usr/lib/issue.d/10-SUSE' --suse-release '/dev/null' > "../${out}"
	elif test -f 'etc/os-release' && test -f 'etc/issue'
	then
		"${exe}" --dist-debug --os-release 'etc/os-release' --issue 'etc/issue' --suse-release '/dev/null' > "../${out}"
	elif test -f 'etc/SuSE-release' && test -f 'etc/issue'
	then
		"${exe}" --dist-debug --os-release '/dev/null' --issue 'etc/issue' --suse-release 'etc/SuSE-release' > "../${out}"
	else
		echo >&2 "INFO: ${dist} lacks os-release/issue files"
		: $((failures++))
	fi
	popd > /dev/null
	if test -f "${out}"
	then
		diff -u "${dist}/DIST.txt" "${out}" || : $((failures++))
	fi
done
rm -f "${out}"	
popd > /dev/null
echo "${failures} failures from ${script}"
test ${failures} -eq 0

#!/bin/bash
#
# Author Jan Löser <jloeser@suse.de>
# Published under the GNU Public Licence 2
ROOT_DIR=`git rev-parse --show-toplevel`

fixtures=""

for fixture in $(find ./data/fixtures/*.json); do
    fixtures="${fixtures} $(basename ${fixture%.*})"
done

python "${ROOT_DIR}/orthos2/manage.py" loaddata ${fixtures}

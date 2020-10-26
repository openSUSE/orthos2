#!/bin/bash
#
# Author Jan Löser <jloeser@suse.de>
# Published under the GNU Public Licence 2
ROOT_DIR="/usr/lib/orthos2"

login="admin"
password="test1234"
email="admin@myproject.com"

pycode="""
from django.db.utils import IntegrityError;
from django.contrib.auth.models import User;
try:
    user=User.objects.create_superuser('${login}', '${email}', '${password}');
    print('admin user created')
    print('Manually do: ./manage.py changepassword %s' % '${login}')
except IntegrityError:
    print('User does already exist!')
"""

"${ROOT_DIR}/manage.py" shell -c "${pycode}"


#!/bin/bash
#
# Author Jan Löser <jloeser@suse.de>
# Published under the GNU Public Licence 2
ROOT_DIR=`git rev-parse --show-toplevel`

login="admin"
password="test1234"

pycode="""
from django.db.utils import IntegrityError;
from django.contrib.auth.models import User;
try:
    user=User.objects.create_user('${login}', password='${password}');
    user.is_superuser=True;
    user.is_staff=True;
    user.save()
except IntegrityError:
    print('User does already exist!')
"""

python "${ROOT_DIR}/orthos2/manage.py" shell -c "${pycode}"

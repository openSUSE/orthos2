#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Author Jan Löser <jloeser@suse.de>
# Published under the GNU Public Licence 2
import sys
import os
import json
proj_path = os.path.dirname(os.path.abspath(__file__)) + '/../'
sys.path.append(proj_path)

import orthos2.wsgi

import configparser

try:
    config = configparser.ConfigParser()
    config.read('./orthos-server.credentials.conf')

    DB_HOST = config.get('database', 'host')
    DB_USER = config.get('database', 'username')
    DB_PASS = config.get('database', 'password')
    DB_NAME = config.get('database', 'database')

    print("Database connection read...")

except Exception as e:
    print(e)
    print("No database connection read!")

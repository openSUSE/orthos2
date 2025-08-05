****************
Groups and Users
****************

Concepts
########

A standard user does not belong to a group. Orthos can manage its own user base. Additionally it can also connect to an
LDAP server and add LDAP users to its local database if successfully authenticated. By default the user cannot log
in to the admin dashboard, the necessary rights must be granted by an administrator over the admin dashboard.
It is possible to create a user without group membership. However, users should
be added to the appropriate groups for easier administration and permissions. Administrative permissions are set in
Orthos in such a way that everything is forbidden first, necessary rights must be set.

.. code-block::

    ---------------------------
    |          Groups         |
    ---------------------------
    | granular administrative |     ---------------------------
    | permissions             |-----|          Users          |
    ---------------------------     ---------------------------
                                    | granular administrative |     -------------------
                                    | permissions             |-----| Admin Dashboard |
                                    ---------------------------     -------------------


Groups fields description
#########################

Name (required)
===============

Name of group. Please, use unique name.

Permissions
===========

Detailed Orthos administration rights. Every user in the profile must have the blalbla enabled to login to the admin
dashboard. by the name of rights, rights are self-explanatory.

Example: ``admin | log entry | Can add log entry, data | enclosure | Can add enclosure etc.``

Users fields description
########################

Username (required)
===================

Name of user.

Password
========

User password, it must comply with password rules.

Active
======

Designates whether this user should be treated as active. Unselect this instead of deleting accounts.

Staff status
============

Designates whether the user can log into this admin site.

Superuser status
================

Designates that this user has all permissions without explicitly assigning them.

Groups
======

Here users can be grouped and administrative rights can be assigned to individual groups.

User permissions
================

Detailed Orthos administration rights. Every user in the profile must have the Staff status enabled to login to the
admin dashboard. Rights that can be assigned are self-explanatory.

Example: ``admin | log entry | Can add log entry, data | enclosure | Can add enclosure etc.``


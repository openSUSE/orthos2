****************
Groups and Users
****************

Concepts
########

A standard user does not belong to a group. Orthos can manage its own user base. Additionally it can also connect to an
OIDC server and add OIDC users to its local database if successfully authenticated. By default a user has no
administrative permissions; the necessary Django model permissions (e.g. to change enclosures or machines) must be
granted by an administrator via Groups or directly on the user. Superuser-only pages (Users, Groups, Systems, Server
Configuration, etc.) additionally require superuser status, which only an existing superuser can grant.
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
                                    | granular administrative |     -----------------------
                                    | permissions             |-----| Administrative Pages |
                                    ---------------------------     -----------------------


Groups fields description
#########################

Name (required)
===============

Name of group. Please, use unique name.

Permissions
===========

Detailed Orthos administration rights, granted to every member of the group. Rights that can be assigned are
self-explanatory.

Example: ``data | enclosure | Can change enclosure, data | machine | Can change machine etc.``

Users fields description
########################

Username (required)
===================

Name of user.

Password
========

There is no password field when creating a user from this page. New accounts start with no usable password;
access is granted afterward by using the "Send password reset email" action on the user's detail page, or the user
can simply log in via OIDC if configured.

Active
======

Designates whether this user should be treated as active. Unselect this instead of deleting accounts.

Staff status
============

A Django built-in flag, shown as a badge and filterable on the Users list. It is not currently used to gate access
to any Orthos 2 page — administrative pages are gated by superuser status and/or Django model permissions instead.

Superuser status
================

Designates that this user has all permissions without explicitly assigning them.

Groups
======

Here users can be grouped and administrative rights can be assigned to individual groups. This is the only way to
grant a user model permissions from this page; individual (per-user) permissions are not editable here.


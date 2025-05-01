#!/bin/bash

/usr/bin/ssh-keygen -A
/usr/sbin/sshd && cobblerd && apachectl -D FOREGROUND

#!/bin/bash

# Generate SSH host keys if they don't exist
/usr/bin/ssh-keygen -A

# Start SSH daemon in foreground
/usr/sbin/sshd -D

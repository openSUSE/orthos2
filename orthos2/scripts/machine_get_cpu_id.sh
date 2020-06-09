#!/bin/bash

STEPPING_URL=ftp://ftphost.network.tld/orthos/stepping

if wget -q "$STEPPING_URL" &>/dev/null ; then
  chmod 755 ./stepping
  CPUID=$(./stepping -s | cut -d : -f 2)
  echo -n "$CPUID"
  rm ./stepping
  exit 0
else
  exit 1
fi

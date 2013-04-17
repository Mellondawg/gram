#!/bin/bash

# Start or stop all GRAM services

echo $#

export SENSE="start"

if [ $# -gt 0 ] 
then
    export SENSE=$1
fi
service gram-am $SENSE
service gram-amv2 $SENSE
service gram-ch $SENSE
service gram-cni $SENSE
service gram-ctrl $SENSE
service gram-vmoc $SENSE


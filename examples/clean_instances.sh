#!/bin/bash

INSTANCES=""

for i in $INSTANCES
do
	corc oci orchestration instance stop --instance-display-name $i
done

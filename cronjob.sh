#!/bin/bash

FROM_DATE=$(date +%Y-%m-%d --date=yesterday)
TO_DATE=$(date +%Y-%m-%d --date=tomorrow)
PYTHON=$(command -v python3.7)

$PYTHON ~/octograph/app/octopus_to_influxdb.py \
	--config-file ~/octograph/octograph.ini \
	--from-date=$FROM_DATE \
	--to-date=$TO_DATE

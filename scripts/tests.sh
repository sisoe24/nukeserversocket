#!/usr/bin/env bash

for file in tests/*; do
    if [[ $file =~ ^tests\/test_ ]]; then
        $(which pytest) $file >> report.log
    fi
done
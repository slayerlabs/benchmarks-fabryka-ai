#!/usr/bin/env bash
# Lokalny bezpiecznik: niszczy instancje podana w $1 po $2 sekundach, jesli jeszcze istnieje.
ID=$1
sleep "$2"
date
vastai destroy instance "$ID" -y

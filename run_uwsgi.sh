#!/bin/bash

#uwsgi -s /tmp/yourapplication.sock --manage-script-name --mount /=hello:app --virtualenv /home/kdoju/domains/meteowilanow.pl/venv --http :8000 &
uwsgi -s /tmp/yourapplication.sock --manage-script-name --mount /=app_main:app --virtualenv /home/kdoju/domains/meteowilanow.pl/venv --http :8000 &

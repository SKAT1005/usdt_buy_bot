#!/bin/bash

if [ "$RUN_ADMIN" == "true" ]; then
    # Run admins panel
    mkdir -p data
    python manage.py makemigrations
    python manage.py migrate
    python manage.py runserver 0.0.0.0:8000
else
    # Run bot
    python manage.py makemigrations bot
    python manage.py migrate
    python main.py
fi

#!/bin/sh

python create_db.py

while true; do
    flask db upgrade
    if [ $? -eq 0 ]; then
        break
    fi
    echo Deploy command failed, retrying in 5 secs...
    sleep 5
done


exec "$@"


exec gunicorn -b :5000 --access-logfile - --error-logfile - run:app
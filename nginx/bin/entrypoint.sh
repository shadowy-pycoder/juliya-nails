#!/bin/sh
# credits to https://git.psu.edu/rzm102/docker-nginx-gunicorn-flask-letsencrypt
certbot certonly --standalone -d $1 -d www.$1 --email $2 -n --agree-tos --expand
/usr/sbin/nginx -g "daemon off;"
/usr/sbin/crond -f -d 8 &

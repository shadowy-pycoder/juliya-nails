FROM nginx:1.25.1-alpine
RUN apk add --no-cache certbot
RUN rm /etc/nginx/nginx.conf && rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/
COPY ./conf.d/flask_app.conf /etc/nginx/conf.d/

ARG DOMAIN
ARG FLASK
ARG EMAIL

ENV DOMAIN=$DOMAIN
ENV FLASK=$FLASK
ENV EMAIL=$EMAIL
ENV DOLLAR='$'

RUN envsubst \
  </etc/nginx/conf.d/flask_app.conf \
  >/etc/nginx/conf.d/application.conf \
  && rm /etc/nginx/conf.d/flask_app.conf

RUN mkdir /var/lib/certbot
COPY ./bin/entrypoint.sh /entrypoint.sh
COPY ./bin/renew /etc/periodic/weekly/renew
RUN chmod +x /entrypoint.sh \
  && chmod +x /etc/periodic/weekly/renew

ENTRYPOINT /entrypoint.sh $DOMAIN $EMAIL 

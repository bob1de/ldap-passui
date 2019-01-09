FROM alpine:latest

ENV DEBUG ""

WORKDIR /opt/ldap-passui

COPY requirements.txt ./
RUN apk add --update tini py3-pip uwsgi uwsgi-http uwsgi-python3 && \
    pip3 install --upgrade pip && \
    pip3 install --upgrade -r requirements.txt && \
    rm -rf /tmp/* /var/tmp/* /var/cache/apk/* /var/cache/distfiles/* ~/.cache

COPY . .

CMD ["tini", "uwsgi", "--yaml", "uwsgi.yaml"]

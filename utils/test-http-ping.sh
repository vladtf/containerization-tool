#!/bin/sh

while true; do
    domain="www.google.com"

    nslookup "$domain"

    if curl --max-time 5 -s --head "$domain" -o /dev/null -w '%{http_code}\n' | grep -q '200'; then
        echo "Request to $domain was successful."
    else
        echo "Request to $domain failed."
    fi 

    sleep 3
done

#!/bin/bash

while true; do
  echo -e "HTTP/1.1 200 OK\r\n\r\nHello, World!" | nc -l -p 8080 -q 1
done

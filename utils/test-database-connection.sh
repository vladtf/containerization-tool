#!/bin/sh

while true; do
    mysql -h containerization-tool-mysql-server.mysql.database.azure.com \
    -u containerization@containerization-tool-mysql-server \
    -pPassword123! \
    -e "SELECT VERSION();" \
    --connect-timeout 5

    if [ $? -eq 0 ]; then
        echo "Connection to MySQL server was successful."
    else
        echo "Connection to MySQL server failed."
    fi

    sleep 3

done
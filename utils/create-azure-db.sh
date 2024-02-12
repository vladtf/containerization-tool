#!/bin/sh

RESOURCE_GROUP="containerization-tool"
LOCATION="uksouth"
MYSQL_SERVER_NAME="containerization-tool-mysql-server"
MYSQL_ADMIN_USER="containerization"
MYSQL_ADMIN_PASSWORD="Password123!"
MYSQL_DB_NAME="containerization-tool-db"


# This script will create an Azure Database for MySQL server and database.
az mysql server create \
    --resource-group $RESOURCE_GROUP \
    --name $MYSQL_SERVER_NAME \
    --location $LOCATION \
    --admin-user $MYSQL_ADMIN_USER \
    --admin-password $MYSQL_ADMIN_PASSWORD \
    --sku-name GP_Gen5_2 \
    --version 5.7

az mysql db create \
    --resource-group $RESOURCE_GROUP \
    --server-name $MYSQL_SERVER_NAME \
    --name $MYSQL_DB_NAME

# String url ="jdbc:mysql://containerization-tool-mysql-server.mysql.database.azure.com:3306/{your_database}?useSSL=true&requireSSL=false"; myDbConn = DriverManager.getConnection(url, "containerization@containerization-tool-mysql-server", {your_password});

# Run a select statement to verify the database is working
mysql -h containerization-tool-mysql-server.mysql.database.azure.com -u containerization@containerization-tool-mysql-server -pPassword123! -e "SELECT VERSION();"


mysql -h 51.105.64.0 -u containerization@containerization-tool-mysql-server -pPassword123! -e "SELECT VERSION();" --connect-timeout 1

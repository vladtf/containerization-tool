FROM mysql:lts-oraclelinux8

ADD ./init/schema.sql /docker-entrypoint-initdb.d

ADD ./conf.cnf /etc/mysql/conf.d

EXPOSE 3306
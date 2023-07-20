USE localdb;

CREATE TABLE
    fluentd_logs (
        id INT AUTO_INCREMENT PRIMARY KEY,
        time DATETIME,
        host VARCHAR(255),
        ident VARCHAR(255),
        pid INT,
        msgid VARCHAR(255),
        extradata VARCHAR(255),
        message TEXT
    );
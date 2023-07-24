USE localdb;

CREATE TABLE
    containers (
        id VARCHAR(12) PRIMARY KEY,
        name VARCHAR(255),
        status VARCHAR(50),
        ip VARCHAR(20),
        image VARCHAR(255),
        created DATETIME
    );

CREATE TABLE
    fluentd_logs (
        id INT AUTO_INCREMENT PRIMARY KEY,
        time DATETIME,
        host VARCHAR(255),
        ident VARCHAR(12),
        pid INT,
        msgid VARCHAR(255),
        extradata VARCHAR(255),
        message TEXT,
        FOREIGN KEY (ident) REFERENCES containers (id) ON DELETE CASCADE
    );